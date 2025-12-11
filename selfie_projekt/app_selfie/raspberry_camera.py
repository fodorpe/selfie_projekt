# app_selfie/raspberry_camera.py
import os
import subprocess
import uuid
from datetime import datetime
from django.conf import settings
import base64

class RaspberryCamera:
    """
    Raspberry Pi kamera kezelése
    """
    
    def __init__(self):
        # Ellenőrizzük, hogy melyik kamera parancs érhető el
        self.camera_type = self._detect_camera()
    
    def _detect_camera(self):
        """Megállapítja, hogy melyik kamera parancs érhető el"""
        try:
            # Próbáljuk meg a libcamera-jpeg-t (új Raspberry Pi OS)
            subprocess.run(['libcamera-jpeg', '--version'], 
                          capture_output=True, timeout=2)
            return 'libcamera'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            try:
                # Próbáljuk meg a raspistill-t (régi Raspberry Pi OS)
                subprocess.run(['raspistill', '--version'], 
                              capture_output=True, timeout=2)
                return 'raspistill'
            except (FileNotFoundError, subprocess.TimeoutExpired):
                return 'none'
    
    def take_photo_base64(self):
        """
        Kép készítése és base64 stringként visszaadása
        """
        try:
            # Ideiglenes fájl létrehozása
            temp_file = f"/tmp/raspberry_photo_{uuid.uuid4().hex}.jpg"
            
            # Kamera parancs végrehajtása
            if self.camera_type == 'libcamera':
                cmd = [
                    'libcamera-jpeg', 
                    '-o', temp_file,
                    '--width', '640',
                    '--height', '480',
                    '--quality', '85'
                ]
            elif self.camera_type == 'raspistill':
                cmd = [
                    'raspistill',
                    '-o', temp_file,
                    '-w', '640',
                    '-h', '480',
                    '-q', '85'
                ]
            else:
                raise Exception("Nincs kamera parancs elérhető. Ellenőrizd a telepítést.")
            
            # Kép készítése
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                raise Exception(f"Kamera hiba: {result.stderr}")
            
            # Fájl beolvasása
            with open(temp_file, 'rb') as f:
                image_data = f.read()
            
            # Base64 kódolás
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Ideiglenes fájl törlése
            os.remove(temp_file)
            
            return f"data:image/jpeg;base64,{base64_image}"
            
        except Exception as e:
            print(f"[HIBA] Raspberry kamera hiba: {str(e)}")   
            return None
    
    def take_photo_to_file(self, filename=None):
        """
        Kép készítése fájlba
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"raspberry_{timestamp}.jpg"
            
            # MEDIA_ROOT használata
            photo_path = os.path.join(settings.MEDIA_ROOT, 'raspberry_photos', filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            
            # Kamera parancs
            if self.camera_type == 'libcamera':
                cmd = [
                    'libcamera-jpeg', 
                    '-o', photo_path,
                    '--width', '1280',
                    '--height', '720',
                    '--quality', '90'
                ]
            elif self.camera_type == 'raspistill':
                cmd = [
                    'raspistill',
                    '-o', photo_path,
                    '-w', '1280',
                    '-h', '720',
                    '-q', '90'
                ]
            else:
                raise Exception("Nincs kamera parancs elérhető.")
            
            # Kép készítése
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return photo_path
            else:
                return None
                
        except Exception as e:
            print(f"[HIBA] Raspberry kamera hiba: {str(e)}")   
            return None
    
    def test_camera(self):
        """Kamera tesztelése"""
        try:
            photo_data = self.take_photo_base64()
            if photo_data:
                return True, "[OK] Kamera működik!"   
            else:
                return False, "[HIBA] Nem sikerült képet készíteni"   
        except Exception as e:
            return False, f"[HIBA] Kamera hiba: {str(e)}"   