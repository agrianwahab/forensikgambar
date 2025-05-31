"""
Helper functions for Forensic Image Detection System
"""

import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance

def allowed_file(filename, allowed_extensions):
    """Check if file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, filename, upload_folder):
    """Save uploaded file to disk"""
    # Ensure upload folder exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Create results folder if it doesn't exist
    results_folder = os.path.join(upload_folder, 'results')
    os.makedirs(results_folder, exist_ok=True)
    
    # Secure the filename and save
    filename = secure_filename(filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return filepath

def get_image_info(filepath):
    """Get image information"""
    try:
        with Image.open(filepath) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            # Get last modified time
            modified_time = os.path.getmtime(filepath)
            modified_date = datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'width': width,
                'height': height,
                'format': format_name,
                'mode': mode,
                'size': file_size,
                'modified': modified_date
            }
    except Exception as e:
        print(f"Error getting image info: {e}")
        return None

def get_analysis_status(analysis):
    """Get current status of analysis"""
    # This would normally involve checking a task queue or process
    # For demo purposes, we'll return the database status
    
    stages = [
        {'id': 1, 'name': 'Validasi file', 'status': 'pending'},
        {'id': 2, 'name': 'Loading gambar', 'status': 'pending'},
        {'id': 3, 'name': 'Ekstraksi metadata', 'status': 'pending'},
        {'id': 4, 'name': 'Pre-processing', 'status': 'pending'},
        {'id': 5, 'name': 'Multi-quality ELA', 'status': 'pending'},
        {'id': 6, 'name': 'Feature extraction', 'status': 'pending'},
        {'id': 7, 'name': 'Copy-move detection', 'status': 'pending'}
    ]
    
    # Update stages based on current_stage
    for stage in stages:
        if stage['id'] < analysis.current_stage:
            stage['status'] = 'completed'
        elif stage['id'] == analysis.current_stage:
            stage['status'] = 'active'
    
    return {
        'id': analysis.id,
        'status': analysis.status,
        'progress': analysis.progress,
        'current_stage': analysis.current_stage,
        'total_stages': analysis.total_stages,
        'stages': stages,
        'estimated_time': analysis.estimated_time,
        'is_complete': analysis.is_complete
    }

def get_analysis_results(analysis):
    """Get analysis results"""
    # This would normally involve loading result files
    # For demo purposes, we'll return the database results
    
    if not analysis.is_complete:
        return {'error': 'Analysis not complete'}
    
    return {
        'id': analysis.id,
        'result_type': analysis.result_type,
        'confidence': analysis.confidence,
        'technical_data': analysis.technical_data_dict,
        'filename': analysis.filename,
        'created_at': analysis.created_at.isoformat(),
        'export_options': {
            'png': analysis.export_png,
            'pdf': analysis.export_pdf,
            'docx': analysis.export_docx
        }
    }

def perform_ela(image_path, quality=90):
    """
    Perform Error Level Analysis on an image
    
    ELA highlights differences in JPEG compression levels,
    which can indicate areas that may have been modified.
    """
    try:
        # Load original image
        original = Image.open(image_path)
        
        # Save with specific quality to a temporary file
        temp_filename = f"temp_ela_{uuid.uuid4()}.jpg"
        original.save(temp_filename, 'JPEG', quality=quality)
        
        # Open the temporary file
        resaved = Image.open(temp_filename)
        
        # Calculate the difference
        ela_image = ImageChops.difference(original, resaved)
        
        # Enhance the difference for better visibility
        extrema = ela_image.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1
        scale = 255.0 / max_diff
        
        ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
        
        # Clean up
        os.remove(temp_filename)
        
        # Calculate ELA statistics
        ela_array = np.array(ela_image)
        ela_mean = np.mean(ela_array)
        ela_std = np.std(ela_array)
        
        return {
            'ela_image': ela_image,
            'ela_mean': float(ela_mean),
            'ela_std': float(ela_std)
        }
    except Exception as e:
        print(f"Error performing ELA: {e}")
        return None

def detect_copy_move(image_path):
    """
    Detect copy-move forgery in an image
    
    This is a simplified implementation for demonstration purposes.
    A real implementation would use more sophisticated algorithms.
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply SIFT to detect keypoints and descriptors
        sift = cv2.SIFT_create()
        keypoints, descriptors = sift.detectAndCompute(gray, None)
        
        # Match descriptors with themselves
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(descriptors, descriptors, k=2)
        
        # Apply ratio test and filter matches
        good_matches = []
        for m, n in matches:
            # Ensure we're not matching a keypoint with itself
            if m.distance < 0.7 * n.distance and m.queryIdx != m.trainIdx:
                good_matches.append(m)
        
        # Extract matched keypoints
        src_pts = np.float32([keypoints[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([keypoints[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        # Use RANSAC to find homography
        if len(good_matches) >= 4:
            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            ransac_inliers = np.sum(mask)
        else:
            ransac_inliers = 0
        
        # Determine if copy-move forgery is detected
        # This is a simplified threshold, real systems would use more sophisticated methods
        is_copy_move = len(good_matches) > 10 and ransac_inliers > 4
        
        # Calculate confidence based on number of matches and RANSAC inliers
        if is_copy_move:
            confidence = min(100, (ransac_inliers / 4) * 20)
        else:
            confidence = 0
        
        return {
            'is_copy_move': is_copy_move,
            'confidence': confidence,
            'matches': len(good_matches),
            'ransac_inliers': ransac_inliers
        }
    except Exception as e:
        print(f"Error detecting copy-move: {e}")
        return None

def detect_splicing(image_path):
    """
    Detect image splicing (combining parts from different images)
    
    This is a simplified implementation for demonstration purposes.
    A real implementation would use more sophisticated algorithms.
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # Convert to different color spaces
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        
        # Extract channels
        h, s, v = cv2.split(hsv)
        y, cr, cb = cv2.split(ycrcb)
        
        # Apply noise analysis (simplified)
        noise_h = cv2.Laplacian(h, cv2.CV_64F).var()
        noise_s = cv2.Laplacian(s, cv2.CV_64F).var()
        noise_cr = cv2.Laplacian(cr, cv2.CV_64F).var()
        noise_cb = cv2.Laplacian(cb, cv2.CV_64F).var()
        
        # Check for inconsistencies in noise levels
        # This is a simplified approach, real systems would use more sophisticated methods
        noise_diff = max(noise_h, noise_s, noise_cr, noise_cb) / min(noise_h, noise_s, noise_cr, noise_cb)
        
        # Determine if splicing is detected
        is_splicing = noise_diff > 2.5
        
        # Calculate confidence
        if is_splicing:
            confidence = min(100, noise_diff * 10)
        else:
            confidence = 0
        
        return {
            'is_splicing': is_splicing,
            'confidence': confidence,
            'noise_diff': noise_diff,
            'noise_values': {
                'h': noise_h,
                's': noise_s,
                'cr': noise_cr,
                'cb': noise_cb
            }
        }
    except Exception as e:
        print(f"Error detecting splicing: {e}")
        return None

def analyze_image(image_path):
    """
    Perform comprehensive image forensic analysis
    
    This function combines multiple forensic techniques to determine
    if an image has been manipulated and what type of manipulation.
    """
    try:
        # Get image info
        image_info = get_image_info(image_path)
        if not image_info:
            return {'error': 'Could not read image'}
        
        # Perform ELA
        ela_results = perform_ela(image_path)
        if not ela_results:
            return {'error': 'Error performing ELA'}
        
        # Detect copy-move forgery
        copy_move_results = detect_copy_move(image_path)
        if not copy_move_results:
            return {'error': 'Error detecting copy-move forgery'}
        
        # Detect splicing
        splicing_results = detect_splicing(image_path)
        if not splicing_results:
            return {'error': 'Error detecting splicing'}
        
        # Determine overall result
        if copy_move_results['is_copy_move'] and copy_move_results['confidence'] > 70:
            result_type = 'copy-move'
            confidence = copy_move_results['confidence']
        elif splicing_results['is_splicing'] and splicing_results['confidence'] > 70:
            result_type = 'splicing'
            confidence = splicing_results['confidence']
        else:
            result_type = 'authentic'
            confidence = 100 - max(copy_move_results['confidence'], splicing_results['confidence'])
        
        # Compile technical data
        technical_data = {
            'image_info': image_info,
            'ela': {
                'mean': ela_results['ela_mean'],
                'std': ela_results['ela_std']
            },
            'copy_move': {
                'matches': copy_move_results['matches'],
                'ransac_inliers': copy_move_results['ransac_inliers']
            },
            'splicing': {
                'noise_diff': splicing_results['noise_diff'],
                'noise_values': splicing_results['noise_values']
            },
            'processing_time': 42.3  # This would be calculated in a real system
        }
        
        return {
            'result_type': result_type,
            'confidence': confidence,
            'technical_data': technical_data
        }
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return {'error': str(e)}
