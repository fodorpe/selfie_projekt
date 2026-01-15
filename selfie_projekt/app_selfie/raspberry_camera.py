import subprocess
import base64
import os

def check_camera():
    """Egyszerű kamera ellenőrzés"""
    try:
        result = subprocess.run(['libcamera-hello', '--timeout', '100'],
                              capture_output=True, text=True, timeout=2)
        return result.returncode == 0
    except Exception:
        return False

def take_photo():
    """Fénykép készítése"""
    try:
        # Kép készítése
        subprocess.run(['libcamera-jpeg', '-o', '/tmp/photo.jpg', 
                       '--width', '640', '--height', '480'], 
                      check=True, timeout=5)
        
        # Base64 konvertálás
        with open('/tmp/photo.jpg', 'rb') as f:
            photo_data = base64.b64encode(f.read()).decode('utf-8')
        
        return {
            'success': True,
            'photo_data': f'data:image/jpeg;base64,{photo_data}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

# Ha osztályt szeretnél, itt van:
class RaspberryCamera:
    """Osztály a Raspberry Pi kamerához"""
    
    @staticmethod
    def is_available():
        return check_camera()
    
    @staticmethod
    def capture():
        return take_photo()