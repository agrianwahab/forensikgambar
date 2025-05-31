"""
Flask forms for Forensic Image Detection System
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

class LoginForm(FlaskForm):
    """Login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Ingat Saya')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    """Registration form"""
    name = StringField('Nama', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password harus minimal 8 karakter')
    ])
    confirm_password = PasswordField('Konfirmasi Password', validators=[
        DataRequired(),
        EqualTo('password', message='Password harus sama')
    ])
    submit = SubmitField('Register')

class ResetPasswordForm(FlaskForm):
    """Reset password form"""
    password = PasswordField('Password Baru', validators=[
        DataRequired(),
        Length(min=8, message='Password harus minimal 8 karakter')
    ])
    confirm_password = PasswordField('Konfirmasi Password', validators=[
        DataRequired(),
        EqualTo('password', message='Password harus sama')
    ])
    submit = SubmitField('Reset Password')

class UploadForm(FlaskForm):
    """Image upload form"""
    image = FileField('Gambar', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'bmp'], 'Hanya file gambar yang diperbolehkan!')
    ])
    export_png = BooleanField('Export PNG')
    export_pdf = BooleanField('Export PDF')
    export_docx = BooleanField('Export DOCX')
    submit = SubmitField('Mulai Analisis')

class FilterForm(FlaskForm):
    """Filter form for analysis history"""
    result_type = SelectField('Tipe Hasil', choices=[
        ('', 'Semua'),
        ('copy-move', 'Copy-Move'),
        ('splicing', 'Splicing'),
        ('authentic', 'Authentic')
    ])
    date_from = StringField('Dari Tanggal')
    date_to = StringField('Sampai Tanggal')
    submit = SubmitField('Filter')
