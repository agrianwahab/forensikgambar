"""
Database models for Forensic Image Detection System
"""

from datetime import datetime
from flask_login import UserMixin
import json

from . import db # Mengimpor db dari __init__.py di direktori yang sama

class User(db.Model, UserMixin):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    analyses = db.relationship('Analysis', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.email}>'

class Analysis(db.Model):
    """Analysis model for storing image analysis data"""
    id = db.Column(db.String(36), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False) # Nama file asli dari user
    stored_filename = db.Column(db.String(255), nullable=False) # Nama file unik di server
    filepath = db.Column(db.String(512), nullable=False) # Path lengkap ke file di server
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Analysis status and progress
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, error
    progress = db.Column(db.Float, default=0.0)  # 0-100%
    current_stage_num = db.Column(db.Integer, default=0) # Nomor tahap saat ini
    total_stages_num = db.Column(db.Integer, default=17) # Total tahap dari sistem_deteksi.main
    current_stage_name = db.Column(db.String(100), default='Initializing') # Nama tahap saat ini
    estimated_time = db.Column(db.Integer, default=120)  # seconds, perkiraan kasar
    
    # Analysis results
    is_complete = db.Column(db.Boolean, default=False)
    result_type = db.Column(db.String(50))  # copy-move, splicing, authentic, complex, error
    confidence = db.Column(db.Float)  # 0-100%
    # technical_data akan menyimpan dictionary JSON dari hasil sistem_deteksi
    technical_data = db.Column(db.Text)
    
    # Export options set by user
    export_png = db.Column(db.Boolean, default=False)
    export_pdf = db.Column(db.Boolean, default=False)
    export_docx = db.Column(db.Boolean, default=False)

    # Paths to exported files
    exported_png_path = db.Column(db.String(512), nullable=True)
    exported_pdf_path = db.Column(db.String(512), nullable=True)
    exported_docx_path = db.Column(db.String(512), nullable=True)
    
    def __repr__(self):
        return f'<Analysis {self.id} - {self.original_filename}>'
    
    @property
    def technical_data_dict(self):
        """Convert technical_data JSON string to dictionary"""
        if not self.technical_data:
            return {}
        try:
            return json.loads(self.technical_data)
        except json.JSONDecodeError:
            # print(f"Warning: Could not decode JSON for Analysis {self.id}: {self.technical_data[:100]}...")
            return {'error': 'Invalid JSON data in technical_data'}
    
    @technical_data_dict.setter
    def technical_data_dict(self, value):
        """Convert dictionary to technical_data JSON string"""
        try:
            self.technical_data = json.dumps(value, default=lambda o: '<not serializable>')
        except TypeError:
            # print(f"Warning: Could not serialize data for Analysis {self.id}")
            self.technical_data = json.dumps({'error': 'Data contains non-serializable objects'})

    def to_dict(self):
        """Convert model to dictionary for API/SocketIO responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'filepath': self.filepath, # Sebaiknya tidak diexpose langsung ke client jika sensitif
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
            'progress': self.progress,
            'current_stage_num': self.current_stage_num,
            'total_stages_num': self.total_stages_num,
            'current_stage_name': self.current_stage_name,
            'estimated_time': self.estimated_time,
            'is_complete': self.is_complete,
            'result_type': self.result_type,
            'confidence': self.confidence,
            'technical_data': self.technical_data_dict, # Kirim sebagai dict
            'export_png': self.export_png,
            'export_pdf': self.export_pdf,
            'export_docx': self.export_docx,
            'exported_png_path': self.exported_png_path,
            'exported_pdf_path': self.exported_pdf_path,
            'exported_docx_path': self.exported_docx_path,
        }