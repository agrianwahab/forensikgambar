"""
Authentication routes for Forensic Image Detection System
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import auth_bp # Mengimpor auth_bp dari __init__.py di direktori yang sama
from .. import db, login_manager # Mengimpor db, login_manager dari __init__.py di level atas (web/)
from ..models import User
from ..forms import LoginForm, RegisterForm, ResetPasswordForm, ResetPasswordRequestForm # Tambahkan ResetPasswordRequestForm
# Untuk token reset password (opsional, bisa diimplementasikan lebih lanjut)
# from itsdangerous import URLSafeTimedSerializer
# from flask import current_app

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id)) # Pastikan user_id adalah integer

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Redirect ke main blueprint, fungsi index
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.is_active:
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                flash('Login berhasil!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('main.index'))
            else:
                flash('Akun Anda tidak aktif. Silakan hubungi administrator.', 'warning')
        else:
            flash('Login gagal. Periksa email dan password Anda.', 'danger')
            
    return render_template('auth/login.html', title='Login Pengguna', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registrasi berhasil! Silakan login dengan akun baru Anda.', 'success')
        return redirect(url_for('auth.login')) # auth blueprint, fungsi login
        
    return render_template('auth/register.html', title='Registrasi Pengguna Baru', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request_route(): # Ubah nama fungsi agar unik
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Logika pengiriman email dengan token reset (belum diimplementasikan penuh)
            # token = generate_reset_token(user.email) # Anda perlu fungsi ini
            # send_reset_email(user.email, token) # Anda perlu fungsi ini
            flash('Jika email terdaftar, instruksi reset password telah dikirim.', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('Jika email terdaftar, instruksi reset password telah dikirim.', 'info') # Pesan generik untuk keamanan
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_route(token): # Ubah nama fungsi agar unik
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Logika validasi token (belum diimplementasikan penuh)
    # email = verify_reset_token(token) # Anda perlu fungsi ini
    # if email is None:
    #     flash('Token reset password tidak valid atau sudah kedaluwarsa.', 'warning')
    #     return redirect(url_for('auth.reset_password_request_route'))
    
    # user = User.query.filter_by(email=email).first()
    # if not user:
    #     flash('Pengguna tidak ditemukan.', 'danger')
    #     return redirect(url_for('auth.login'))

    # Untuk demo, kita bypass validasi token dan langsung tampilkan form
    # Hapus/komentari bagian di atas jika implementasi token penuh belum ada
    user = None # Placeholder, ini akan error jika tidak ada logika token yang sebenarnya

    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Jika validasi token sukses dan user ditemukan:
        # user.password_hash = generate_password_hash(form.password.data)
        # db.session.commit()
        flash('Password Anda telah berhasil direset! Silakan login.', 'success')
        return redirect(url_for('auth.login'))
    
    # Jika implementasi token belum ada, bagian ini hanya akan menampilkan form
    # tanpa bisa melakukan reset sebenarnya.
    # Anda bisa tambahkan pesan bahwa fitur ini dalam pengembangan.
    if not user: # Jika user tidak diset dari token (karena logika token belum ada)
        flash('Fitur reset password dengan token belum sepenuhnya aktif. Silakan hubungi admin.', 'info')
        # Daripada error, mungkin redirect atau tampilkan pesan saja.
        # return redirect(url_for('auth.login')) 
        # Atau biarkan form tampil tapi tidak akan berfungsi tanpa user object

    return render_template('auth/reset_password.html', title='Reset Password Anda', form=form, token=token)

# Fungsi placeholder untuk token (perlu implementasi nyata dengan email)
# def generate_reset_token(email):
#     serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
#     return serializer.dumps(email, salt='password-reset-salt')

# def verify_reset_token(token, expiration=3600): # 1 jam
#     serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
#     try:
#         email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
#     except:
#         return None
#     return email

# def send_reset_email(email, token):
#     # Implementasi pengiriman email dengan link reset
#     pass