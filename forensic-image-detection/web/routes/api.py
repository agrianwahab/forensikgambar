"""
API routes for Forensic Image Detection System
"""

from flask import jsonify, request, current_app
from flask_login import login_required, current_user
import os
import uuid
from datetime import datetime, timedelta
import json

from . import api_bp # Mengimpor api_bp dari __init__.py di direktori yang sama
from .. import db # Mengimpor db dari __init__.py di level atas (web/)
from ..models import Analysis, User
from ..helpers import save_uploaded_file, get_analysis_stages, delete_analysis_files

# Mengimpor fungsi start_analysis dari app.py di root project
# from ....app import start_analysis
import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), '../../../')) # Tambahkan root project ke sys.path
from app import start_analysis


@api_bp.route('/analysis/status/<analysis_id>', methods=['GET'])
@login_required
def analysis_status(analysis_id):
    """Get analysis status"""
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
    
    if not analysis:
        return jsonify({'error': 'Analisis tidak ditemukan atau Anda tidak berhak mengaksesnya.'}), 404
    
    return jsonify(analysis.to_dict())


@api_bp.route('/analysis/submit', methods=['POST'])
@login_required
def submit_analysis_api():
    """API endpoint for image upload and starting analysis"""
    if 'image' not in request.files:
        return jsonify({'error': 'Tidak ada file gambar yang dikirim.'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'Nama file kosong.'}), 400
    
    # Validasi ekstensi file (gunakan config dari app)
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({'error': f"Format file tidak didukung. Format yang diizinkan: {', '.join(allowed_extensions)}"}), 400

    # Simpan file
    stored_fname, file_path = save_uploaded_file(file)
        
    # Get export options
    export_png = request.form.get('export_png', 'false').lower() == 'true'
    export_pdf = request.form.get('export_pdf', 'false').lower() == 'true'
    export_docx = request.form.get('export_docx', 'false').lower() == 'true'
    
    # Create new analysis in database
    analysis_id = str(uuid.uuid4())
    new_analysis = Analysis(
        id=analysis_id,
        user_id=current_user.id,
        original_filename=secure_filename(file.filename), # Gunakan secure_filename di sini juga
        stored_filename=stored_fname,
        filepath=file_path,
        status='queued',
        progress=0.0,
        export_png=export_png,
        export_pdf=export_pdf,
        export_docx=export_docx
    )
    
    db.session.add(new_analysis)
    db.session.commit()
    
    # Start analysis task in background
    start_analysis(analysis_id, file_path)
    
    return jsonify({
        'message': 'Analisis berhasil ditambahkan ke antrian.',
        'analysis_id': analysis_id,
        'status_url': url_for('api.analysis_status', analysis_id=analysis_id, _external=True)
    }), 202 # Accepted

@api_bp.route('/analysis/results/<analysis_id>', methods=['GET'])
@login_required
def get_analysis_results_api(analysis_id):
    """Get analysis results via API"""
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
    
    if not analysis:
        return jsonify({'error': 'Analisis tidak ditemukan atau Anda tidak berhak mengaksesnya.'}), 404
    
    if not analysis.is_complete and analysis.status != 'error':
        return jsonify({
            'status': analysis.status, 
            'progress': analysis.progress,
            'message': 'Analisis masih dalam proses.'
        }), 202 # Accepted, but not complete
    
    return jsonify(analysis.to_dict())

@api_bp.route('/history', methods=['GET'])
@login_required
def get_history_api():
    """Get user's analysis history with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    result_type_filter = request.args.get('result_type')
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    sort_by = request.args.get('sort_by', 'created_at_desc')

    query = Analysis.query.filter_by(user_id=current_user.id)
    
    if result_type_filter:
        query = query.filter(Analysis.result_type == result_type_filter)
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            query = query.filter(Analysis.created_at >= date_from)
        except ValueError:
            return jsonify({'error': 'Format "date_from" tidak valid. Gunakan YYYY-MM-DD.'}), 400
    if date_to_str:
        try:
            # Tambahkan 1 hari ke date_to untuk mencakup semua entri pada hari tersebut
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Analysis.created_at < date_to)
        except ValueError:
            return jsonify({'error': 'Format "date_to" tidak valid. Gunakan YYYY-MM-DD.'}), 400

    if sort_by == 'created_at_asc':
        query = query.order_by(Analysis.created_at.asc())
    elif sort_by == 'original_filename_asc':
        query = query.order_by(Analysis.original_filename.asc())
    elif sort_by == 'original_filename_desc':
        query = query.order_by(Analysis.original_filename.desc())
    else: # Default to created_at_desc
        query = query.order_by(Analysis.created_at.desc())
        
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    analyses_data = [analysis.to_dict() for analysis in pagination.items]
    
    return jsonify({
        'items': analyses_data,
        'total_items': pagination.total,
        'total_pages': pagination.pages,
        'current_page': pagination.page,
        'per_page': pagination.per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

@api_bp.route('/analysis/delete/<analysis_id>', methods=['DELETE'])
@login_required
def delete_analysis_api(analysis_id):
    """Delete an analysis record and its associated files."""
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
    
    if not analysis:
        return jsonify({'error': 'Analisis tidak ditemukan atau Anda tidak berhak menghapusnya.'}), 404
        
    try:
        delete_analysis_files(analysis) # Helper untuk menghapus file-file
        db.session.delete(analysis)
        db.session.commit()
        return jsonify({'message': 'Analisis berhasil dihapus.'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting analysis {analysis_id} via API: {e}")
        return jsonify({'error': f'Gagal menghapus analisis: {str(e)}'}), 500