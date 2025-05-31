"""
WebSocket handlers for Forensic Image Detection System
"""

from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user

from . import socketio, db # Mengimpor socketio dan db dari __init__.py
from .models import Analysis # Mengimpor model Analysis

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}") # Room per user
        # print(f"Client connected: {request.sid}, User: {current_user.email}")
    else:
        # print(f"Anonymous client connected: {request.sid}")
        pass # Atau bisa kirim pesan error jika otentikasi diperlukan untuk semua koneksi

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        leave_room(f"user_{current_user.id}")
        # print(f"Client disconnected: {request.sid}, User: {current_user.email}")
    else:
        # print(f"Anonymous client disconnected: {request.sid}")
        pass

@socketio.on('join_analysis_room')
def handle_join_analysis_room(data):
    """Client joins a room for specific analysis updates."""
    analysis_id = data.get('analysis_id')
    if not analysis_id:
        emit('error', {'message': 'Analysis ID is required.'})
        return

    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required to join analysis room.'})
        return

    # Verifikasi apakah user berhak melihat analisis ini
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
    if not analysis:
        emit('error', {'message': 'Analysis not found or unauthorized.'})
        return
        
    join_room(f"analysis_{analysis_id}")
    # print(f"User {current_user.email} (SID: {request.sid}) joined room for analysis {analysis_id}")
    # Kirim status terkini saat join
    emit('analysis_update', analysis.to_dict(), room=request.sid)


@socketio.on('leave_analysis_room')
def handle_leave_analysis_room(data):
    """Client leaves a room for specific analysis updates."""
    analysis_id = data.get('analysis_id')
    if not analysis_id:
        # Tidak perlu emit error jika hanya meninggalkan room
        return

    if current_user.is_authenticated:
        leave_room(f"analysis_{analysis_id}")
        # print(f"User {current_user.email} (SID: {request.sid}) left room for analysis {analysis_id}")

# Fungsi ini akan dipanggil dari background task atau setelah DB diupdate
def emit_analysis_update_to_rooms(analysis_id):
    """Emit analysis update to relevant rooms based on Analysis model."""
    analysis = Analysis.query.get(analysis_id)
    if analysis:
        data_to_emit = analysis.to_dict()
        # Kirim ke room spesifik analisis
        socketio.emit('analysis_update', data_to_emit, room=f"analysis_{analysis.id}")
        # Kirim juga ke room user (misalnya untuk notifikasi umum)
        socketio.emit('analysis_update_summary', {
            'id': analysis.id,
            'original_filename': analysis.original_filename,
            'status': analysis.status,
            'progress': analysis.progress,
            'is_complete': analysis.is_complete,
            'result_type': analysis.result_type
        }, room=f"user_{analysis.user_id}")
        # print(f"Emitted analysis_update for {analysis_id} to rooms.")

def emit_analysis_completion_to_rooms(analysis_id):
    analysis = Analysis.query.get(analysis_id)
    if analysis and analysis.is_complete:
        data_to_emit = analysis.to_dict()
        socketio.emit('analysis_complete', data_to_emit, room=f"analysis_{analysis.id}")
        socketio.emit('analysis_complete_summary', {
            'id': analysis.id,
            'original_filename': analysis.original_filename,
            'status': analysis.status,
            'result_type': analysis.result_type,
            'confidence': analysis.confidence
        }, room=f"user_{analysis.user_id}")
        # print(f"Emitted analysis_complete for {analysis_id} to rooms.")


def emit_analysis_error_to_rooms(analysis_id, error_message="Terjadi kesalahan saat analisis."):
    analysis = Analysis.query.get(analysis_id) # Untuk mendapatkan user_id
    data = {
        'id': analysis_id,
        'status': 'error',
        'error_message': error_message,
        'progress': analysis.progress if analysis else 0,
        'current_stage_num': analysis.current_stage_num if analysis else 0
    }
    socketio.emit('analysis_error', data, room=f"analysis_{analysis_id}")
    if analysis:
        socketio.emit('analysis_error_summary', {
            'id': analysis.id,
            'original_filename': analysis.original_filename,
            'error_message': error_message
        }, room=f"user_{analysis.user_id}")
    # print(f"Emitted analysis_error for {analysis_id} to rooms.")
```