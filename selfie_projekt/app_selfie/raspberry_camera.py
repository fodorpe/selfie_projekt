#!/usr/bin/env python3
import subprocess
import base64
import os
import time

class RaspberryCamera:
    """Raspberry Pi kamera osztály - ÉLŐ PREVIEW-VEL"""
    
    def __init__(self):
        self.camera_type = "Camera Module 2 (IMX219)"  # Fix V2-nek
        self.available = self._check_availability()
        self.preview_process = None
    
    def _check_availability(self):
        """Kamera elérhetőségének ellenőrzése"""
        try:
            # Egyszerűbb ellenőrzés
            result = subprocess.run(['libcamera-hello', '--timeout', '100'],
                                  capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except Exception:
            return False
    
    def start_preview(self, width=640, height=480, timeout_ms=30000):
        """Élő preview indítása (új ablakban)"""
        try:
            # Megállítjuk az előző preview-t ha van
            self.stop_preview()
            
            # Új preview indítása külön ablakban
            self.preview_process = subprocess.Popen([
                'libcamera-hello',
                '--width', str(width),
                '--height', str(height),
                '--timeout', str(timeout_ms),
                '--qt-preview'
            ])
            
            print(f"✅ Preview indítva (PID: {self.preview_process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Preview hiba: {e}")
            return False
    
    def stop_preview(self):
        """Preview leállítása"""
        if self.preview_process:
            try:
                self.preview_process.terminate()
                self.preview_process.wait(timeout=2)
                print("✅ Preview leállítva")
            except:
                pass
            self.preview_process = None
    
    def capture_photo(self, width=640, height=480):
        """Fénykép készítése"""
        try:
            # Először megállítjuk a preview-t (ha fut)
            self.stop_preview()
            
            # Kép készítése
            subprocess.run(['libcamera-jpeg', '-o', '/tmp/raspberry_photo.jpg',
                          '--width', str(width), '--height', str(height),
                          '--nopreview', '--immediate'],  # Azonnal készít
                         check=True, timeout=10)
            
            # Base64 konvertálás
            with open('/tmp/raspberry_photo.jpg', 'rb') as f:
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
    
    def quick_test(self):
        """Gyors teszt hogy működik-e"""
        try:
            result = subprocess.run(['libcamera-jpeg', '-o', '/tmp/test.jpg',
                                   '--width', '100', '--height', '100',
                                   '--nopreview', '--immediate'],
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False