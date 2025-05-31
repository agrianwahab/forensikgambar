"""
Main routes for Forensic Image Detection System
"""

from flask import render_template, redirect, url_for, flash, request, current_app, send_from_directory, abort
from flask_login import login_required, current_user
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import json


from . import main_bp # Mengimpor main_bp dari __init__.py di direktori yang sama
from .. import db, socketio # Mengimpor db dari __init__.py di level atas (web/)
from ..models import Analysis, User
from ..forms import UploadForm, FilterForm
from ..helpers import save_uploaded_file, get_image_info, get_analysis_stages, get_thumbnail_path, delete_analysis_files

# Mengimpor fungsi start_analysis dari app.py di root project
# Ini asumsi app.py ada di root dan web/ adalah subdirektori
# Jika struktur berbeda, path import ini perlu disesuaikan
# from ....app import start_analysis # Jika app.py satu level di atas web/routes/
import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), '../../../')) # Tambahkan root project ke sys.path
from app import start_analysis # Impor dari app.py di root


@main_bp.route('/')
def index():
    """Homepage route"""
    # Get some statistics for the homepage
    total_analyzed = Analysis.query.count()
    user_analyzed_count = 0
    if current_user.is_authenticated:
        user_analyzed_count = Analysis.query.filter_by(user_id=current_user.id).count()

    stats = {
        'total_analyzed_system': total_analyzed,
        'total_analyzed_user': user_analyzed_count,
        'copy_move_accuracy': 95.3, # Contoh data
        'splicing_accuracy': 92.7, # Contoh data
        'authentic_accuracy': 98.1, # Contoh data
        'avg_time_seconds': 115 # Contoh data
    }
    return render_template('index.html', title="Beranda", stats=stats)

@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload page route"""
    form = UploadForm() # FileAllowed akan diatur di dalam form
    if form.validate_on_submit():
        file = form.image.data
        
        # Simpan file yang diupload
        stored_fname, file_path = save_uploaded_file(file) # helper ini perlu current_app context
        
        # Dapatkan info gambar dasar
        image_info = get_image_info(file_path)
        if not image_info:
            flash('Gagal membaca informasi gambar. File mungkin rusak atau format tidak didukung.', 'danger')
            return redirect(url_for('main.upload'))

        # Buat record analisis baru di database
        analysis_id = str(uuid.uuid4())
        new_analysis = Analysis(
            id=analysis_id,
            user_id=current_user.id,
            original_filename=secure_filename(file.filename),
            stored_filename=stored_fname,
            filepath=file_path,
            status='queued', # Status awal: queued
            progress=0.0,
            current_stage_num=0,
            total_stages_num=17, # Default, akan diupdate oleh task
            current_stage_name='Menunggu antrian',
            export_png=form.export_png.data,
            export_pdf=form.export_pdf.data,
            export_docx=form.export_docx.data
        )
        
        db.session.add(new_analysis)
        db.session.commit()
        
        flash(f"Gambar '{new_analysis.original_filename}' berhasil diunggah dan ditambahkan ke antrian analisis.", 'success')
        
        # Panggil fungsi start_analysis dari app.py untuk memulai analisis di background thread
        start_analysis(analysis_id, file_path)
        
        return redirect(url_for('main.analysis_progress', analysis_id=analysis_id))
        
    return render_template('upload.html', title="Upload Gambar", form=form)

@main_bp.route('/analysis/<analysis_id>')
@login_required
def analysis_progress(analysis_id):
    """Analysis progress page route"""
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first_or_404()
    
    if analysis.status == 'completed':
        return redirect(url_for('main.results', analysis_id=analysis_id))

    ui_stages = get_analysis_stages(analysis)

    return render_template('analysis.html', title=f"Proses Analisis - {analysis.original_filename}",
                           analysis=analysis, ui_stages=ui_stages)

@main_bp.route('/results/<analysis_id>')
@login_required
def results(analysis_id):
    """Results page route"""
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first_or_404()
    
    if not analysis.is_complete and analysis.status != 'error':
        flash('Analisis untuk gambar ini belum selesai.', 'info')
        return redirect(url_for('main.analysis_progress', analysis_id=analysis_id))
    
    # Ambil data teknis (sudah dalam bentuk dict karena property di model)
    technical_data = analysis.technical_data_dict
    
    # Siapkan path untuk gambar hasil visualisasi jika ada
    # Ini akan dikirim ke template untuk ditampilkan
    # Contoh: jika visualisasi disimpan sebagai <RESULTS_FOLDER>/<analysis_id>_visualization.png
    vis_png_filename = f"{os.path.splitext(analysis.stored_filename)[0]}_analysis.png" # Sesuai output sistem_deteksi
    vis_png_exists = os.path.exists(os.path.join(current_app.config['RESULTS_FOLDER'], vis_png_filename))
    
    return render_template('results.html', 
                           title=f"Hasil Analisis - {analysis.original_filename}",
                           analysis=analysis,
                           technical_data=technical_data,
                           vis_png_filename=vis_png_filename if vis_png_exists else None,
                           analysis_stages_summary=get_analysis_stages(analysis))


@main_bp.route('/history', methods=['GET', 'POST'])
@login_required
def history():
    """Analysis history page route"""
    form = FilterForm(request.form) # Gunakan request.form agar nilai filter tetap ada setelah submit
    
    query = Analysis.query.filter_by(user_id=current_user.id)
    
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Jumlah item per halaman

    # Penanganan Filter
    filter_active = False
    if request.method == 'POST' and form.validate_on_submit(): # Tombol filter ditekan
        if form.reset_filter.data == "1": # Tombol reset ditekan
             return redirect(url_for('main.history')) # Redirect untuk clear GET params

        filter_active = True
        session['history_filters'] = {
            'result_type': form.result_type.data,
            'date_from': form.date_from.data,
            'date_to': form.date_to.data,
            'sort_by': form.sort_by.data,
        }
        return redirect(url_for('main.history', page=1)) # Reset ke page 1 saat filter baru
    
    # Terapkan filter dari session jika ada (setelah redirect dari POST atau dari navigasi pagination)
    if 'history_filters' in session:
        filters = session['history_filters']
        form.result_type.data = filters.get('result_type')
        form.date_from.data = filters.get('date_from')
        form.date_to.data = filters.get('date_to')
        form.sort_by.data = filters.get('sort_by')
        filter_active = any(filters.values())


    if form.result_type.data:
        query = query.filter(Analysis.result_type == form.result_type.data)
    if form.date_from.data:
        try:
            date_from_obj = datetime.strptime(form.date_from.data, '%Y-%m-%d')
            query = query.filter(Analysis.created_at >= date_from_obj)
        except ValueError:
            flash('Format "Dari Tanggal" tidak valid. Gunakan YYYY-MM-DD.', 'warning')
    if form.date_to.data:
        try:
            date_to_obj = datetime.strptime(form.date_to.data, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(Analysis.created_at <= date_to_obj)
        except ValueError:
            flash('Format "Sampai Tanggal" tidak valid. Gunakan YYYY-MM-DD.', 'warning')

    # Penanganan Urutan
    sort_option = form.sort_by.data or 'created_at_desc' # Default sort
    if sort_option == 'created_at_desc':
        query = query.order_by(Analysis.created_at.desc())
    elif sort_option == 'created_at_asc':
        query = query.order_by(Analysis.created_at.asc())
    elif sort_option == 'original_filename_asc':
        query = query.order_by(Analysis.original_filename.asc())
    elif sort_option == 'original_filename_desc':
        query = query.order_by(Analysis.original_filename.desc())
    else: # Default
        query = query.order_by(Analysis.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    analyses_list = pagination.items
    
    # Get thumbnails
    thumbnails = {analysis.id: get_thumbnail_path(analysis) for analysis in analyses_list}

    return render_template('history.html', title="Riwayat Analisis", 
                           analyses=analyses_list, pagination=pagination, 
                           form=form, filter_active=filter_active, thumbnails=thumbnails)

@main_bp.route('/history/clear_filters')
@login_required
def clear_history_filters():
    session.pop('history_filters', None)
    return redirect(url_for('main.history'))


@main_bp.route('/about')
def about():
    """About page route"""
    return render_template('about.html', title="Tentang Sistem")

@main_bp.route('/uploads/<path:filename>')
@login_required # Sebaiknya ini juga di-protect
def serve_uploaded_file(filename):
    """Serve uploaded files (originals or thumbnails)."""
    # Cek apakah filename mengandung 'thumbnails/'
    if 'thumbnails/' in filename:
        # Ini adalah thumbnail, direktori relatif terhadap UPLOAD_FOLDER
        directory = current_app.config['UPLOAD_FOLDER']
    else:
        # Ini adalah file asli, cek kepemilikan
        # Cek apakah user yang meminta berhak atas file ini
        # Cari analysis record berdasarkan stored_filename
        analysis_record = Analysis.query.filter_by(stored_filename=filename, user_id=current_user.id).first()
        if not analysis_record:
            # Atau jika admin, bisa dibuat logic tambahan
            abort(403) # Forbidden
        directory = current_app.config['UPLOAD_FOLDER']
        
    return send_from_directory(directory, filename)


@main_bp.route('/results_files/<path:filename>')
@login_required
def serve_results_file(filename):
    """Serve analysis result files (e.g., visualizations from sistem_deteksi)."""
    # Perlu verifikasi kepemilikan file hasil juga
    # Asumsi nama file hasil terkait dengan analysis.id atau analysis.stored_filename
    # Misal, filename adalah <analysis_id>_visualization.png
    # Ekstrak analysis_id atau stored_filename dari `filename`
    
    # Placeholder: Cek apakah user memiliki analisis yang mungkin menghasilkan file ini
    # Ini perlu logika yang lebih canggih tergantung bagaimana file hasil dinamai
    # Untuk sekarang, kita asumsikan jika user login, dia bisa akses (perlu diperketat)
    
    # Cek apakah ada analysis record yang `exported_..._path` nya menunjuk ke filename ini
    analysis_record_png = Analysis.query.filter_by(exported_png_path=filename, user_id=current_user.id).first()
    analysis_record_pdf = Analysis.query.filter_by(exported_pdf_path=filename, user_id=current_user.id).first()
    analysis_record_docx = Analysis.query.filter_by(exported_docx_path=filename, user_id=current_user.id).first()
    
    # Atau jika nama file hasil dari sistem deteksi internal (bukan yang di-export user)
    # Misal, <stored_filename_tanpa_ext>_analysis.png
    # Coba cari analysis record dari bagian nama file sebelum _analysis.png
    potential_stored_filename_stem = filename.split('_analysis.')[0] if '_analysis.' in filename else None
    analysis_record_internal_vis = None
    if potential_stored_filename_stem:
        analysis_record_internal_vis = Analysis.query.filter(
            Analysis.stored_filename.startswith(potential_stored_filename_stem),
            Analysis.user_id == current_user.id
        ).first()


    if not (analysis_record_png or analysis_record_pdf or analysis_record_docx or analysis_record_internal_vis):
        # Jika tidak ada record yang cocok, berarti user tidak berhak atau file tidak ada
        # current_app.logger.warning(f"User {current_user.id} tried to access unauthorized/unknown result file: {filename}")
        abort(403)

    return send_from_directory(current_app.config['RESULTS_FOLDER'], filename)


@main_bp.route('/delete_analysis/<analysis_id>', methods=['POST'])
@login_required
def delete_analysis_route(analysis_id):
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first_or_404()
    
    try:
        delete_analysis_files(analysis) # Hapus file terkait
        db.session.delete(analysis)
        db.session.commit()
        flash('Data analisis berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus analisis: {str(e)}', 'danger')
        current_app.logger.error(f"Error deleting analysis {analysis_id}: {e}")
        
    return redirect(url_for('main.history'))

@main_bp.route('/export_file/<analysis_id>/<export_type>')
@login_required
def export_file_route(analysis_id, export_type):
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first_or_404()

    if not analysis.is_complete:
        flash("Analisis belum selesai, tidak dapat mengekspor.", "warning")
        return redirect(url_for('main.results', analysis_id=analysis_id))

    filepath_to_serve = None
    filename_to_download = None
    
    # Asumsikan export_utils.py dari sistem_deteksi menyimpan file di RESULTS_FOLDER
    # dan path relatifnya disimpan di model Analysis
    
    results_folder = current_app.config['RESULTS_FOLDER']
    
    # Jika file export belum ada, generate dulu
    # Ini adalah contoh, idealnya export_utils.py punya fungsi yang bisa dipanggil di sini
    # Untuk sekarang, kita asumsikan file sudah ada jika path-nya tersimpan di model
    
    if export_type == 'png':
        if analysis.exported_png_path and os.path.exists(os.path.join(results_folder, analysis.exported_png_path)):
            filepath_to_serve = analysis.exported_png_path
            filename_to_download = f"{os.path.splitext(analysis.original_filename)[0]}_visualization.png"
        else: # Jika belum ada, coba generate (ini perlu integrasi dengan sistem_deteksi.export_utils)
            flash("File PNG belum tersedia. Fitur auto-generate belum diimplementasikan.", "info") # Placeholder
            return redirect(url_for('main.results', analysis_id=analysis_id))


    elif export_type == 'pdf':
        if analysis.exported_pdf_path and os.path.exists(os.path.join(results_folder, analysis.exported_pdf_path)):
            filepath_to_serve = analysis.exported_pdf_path
            filename_to_download = f"{os.path.splitext(analysis.original_filename)[0]}_visualization.pdf"
        else:
            flash("File PDF visualisasi belum tersedia.", "info")
            return redirect(url_for('main.results', analysis_id=analysis_id))
            
    elif export_type == 'docx':
        if analysis.exported_docx_path and os.path.exists(os.path.join(results_folder, analysis.exported_docx_path)):
            filepath_to_serve = analysis.exported_docx_path
            filename_to_download = f"{os.path.splitext(analysis.original_filename)[0]}_report.docx"
        else:
            flash("File DOCX laporan belum tersedia.", "info")
            return redirect(url_for('main.results', analysis_id=analysis_id))
    else:
        flash("Tipe export tidak valid.", "danger")
        return redirect(url_for('main.results', analysis_id=analysis_id))

    if filepath_to_serve:
        return send_from_directory(results_folder, filepath_to_serve, as_attachment=True, download_name=filename_to_download)
    
    # Fallback jika ada masalah
    return redirect(url_for('main.results', analysis_id=analysis_id))