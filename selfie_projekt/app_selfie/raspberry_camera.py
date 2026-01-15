#!/usr/bin/env python3
import subprocess
import base64
import os

class RaspberryCamera:
    """Raspberry Pi kamera osztály - MINDEN METÓDUSSAL"""
    
    def __init__(self):
        self.camera_type = self._detect_camera_type()
        self.available = self._check_availability()
    
    def _detect_camera_type(self):
        """Kamera típusának automatikus detektálása"""
        try:
            result = subprocess.run(['libcamera-hello', '--list-cameras'],
                                  capture_output=True, text=True, timeout=3)
            
            if 'imx219' in result.stdout.lower():
                return 'Camera Module 2 (IMX219)'
            elif 'imx477' in result.stdout.lower():
                return 'HQ Camera (IMX477)'
            elif 'imx708' in result.stdout.lower():
                return 'Camera Module 3 (IMX708)'
            elif 'ov5647' in result.stdout.lower():
                return 'Camera Module 1 (OV5647)'
            else:
                return 'Raspberry Pi Camera'
        except Exception:
            return 'Kamera típus nem detektálható'
    
    def _check_availability(self):
        """Kamera elérhetőségének ellenőrzése"""
        try:
            result = subprocess.run(['libcamera-hello', '--timeout', '100'],
                                  capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except Exception:
            return False
    
    def capture_photo(self, width=640, height=480):
        """Fénykép készítése - az EGYETLEN képkészítő metódus"""
        try:
            # Kép készítése
            subprocess.run(['libcamera-jpeg', '-o', '/tmp/photo.jpg',
                          '--width', str(width), '--height', str(height)],
                         check=True, timeout=10)
            
            # Base64 konvertálás
            with open('/tmp/photo.jpg', 'rb') as f:
                photo_data = base64.b64encode(f.read()).decode('utf-8')
            
            return {
                'success': True,
                'photo_data': f'data:image/jpeg;base64,{photo_data}',
                'camera_type': self.camera_type
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'camera_type': self.camera_type
            }
    
    # ALIAS metódusok - régi kód kompatibilitás miatt
    def take_photo_base64(self, width=640, height=480):
        """Alias capture_photo() metódushoz (régi kód miatt)"""
        return self.capture_photo(width, height)
    
    def take_photo(self, width=640, height=480):
        """Alias capture_photo() metódushoz (régi kód miatt)"""
        return self.capture_photo(width, height)
    
    def get_base64_photo(self, width=640, height=480):
        """Alias capture_photo() metódushoz (régi kód miatt)"""
        return self.capture_photo(width, height)

# ÖSSZES kompatibilitási függvény a régi kódhoz
def check_camera():
    """Gyors kamera ellenőrzés"""
    camera = RaspberryCamera()
    return camera.available

def take_photo():
    """Gyors fénykép készítés"""
    camera = RaspberryCamera()
    return camera.capture_photo()

def take_photo_base64():
    """Gyors fénykép készítés base64 formátumban"""
    camera = RaspberryCamera()
    return camera.capture_photo()

# Deprecated - de használhatod őket
is_camera_available = check_camera
capture_image = take_photo
get_photo = take_photo_base64