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
        """
        Kamera típusának becslése.
        Ha működik a kamera, de nem tudjuk a szenzort, akkor általános értéket adunk vissza.
        """
        try:
            result = subprocess.run(
                ['libcamera-hello', '--timeout', '100'],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                return 'Raspberry Pi Camera'
            else:
                return 'Kamera nem válaszol'
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
        """Fénykép készítése"""
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
    
    # Preview funkciók
    def start_preview(self, width=640, height=480, timeout_ms=30000):
        """Preview indítása"""
        try:
            self.stop_preview()  # Előző leállítása
            self.preview_process = subprocess.Popen([
                'libcamera-hello',
                '--width', str(width),
                '--height', str(height),
                '--timeout', str(timeout_ms)
            ])
            return True
        except Exception:
            return False
    
    def stop_preview(self):
        """Preview leállítása"""
        if hasattr(self, 'preview_process') and self.preview_process:
            try:
                self.preview_process.terminate()
                self.preview_process.wait(timeout=2)
            except:
                pass
    
    def get_quick_preview(self):
        """Gyors preview kép"""
        try:
            subprocess.run(['libcamera-jpeg', '-o', '/tmp/preview.jpg',
                          '--width', '320', '--height', '240',
                          '--nopreview', '--immediate', '-q', '50'],
                         check=True, timeout=3)
            
            with open('/tmp/preview.jpg', 'rb') as f:
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

# ===== GLOBÁLIS FÜGGVÉNYEK =====
# Ezeket importálod a Flask-ből

def check_camera():
    """Kamera elérhetőség ellenőrzése - EZT IMPORTÁLOD!"""
    try:
        camera = RaspberryCamera()
        return camera.available
    except Exception:
        return False

def take_photo():
    """Kép készítése"""
    try:
        camera = RaspberryCamera()
        return camera.capture_photo()
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def start_preview():
    """Preview indítása"""
    try:
        camera = RaspberryCamera()
        return camera.start_preview()
    except Exception as e:
        return False

def stop_preview():
    """Preview leállítása"""
    try:
        camera = RaspberryCamera()
        camera.stop_preview()
        return True
    except Exception:
        return False

def get_preview_image():
    """Preview kép lekérése"""
    try:
        camera = RaspberryCamera()
        return camera.get_quick_preview()
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

# Alias-ek a régi kód kompatibilitásához
is_camera_available = check_camera
take_photo_base64 = take_photo
capture_image = take_photo