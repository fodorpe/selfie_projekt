# app_selfie/test_camera.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'selfie_projekt.settings')
import django
django.setup()

from app_selfie.raspberry_camera import RaspberryCamera

def test():
    print("🧪 Raspberry Pi kamera tesztelése...")
    camera = RaspberryCamera()
    
    print(f"📷 Kamera típus: {camera.camera_type}")
    
    if camera.camera_type == 'none':
        print("❌ Nem található kamera parancs")
        print("Telepítsd: sudo apt install libcamera-apps")
        return
    
    print("📸 Kép készítése...")
    success, message = camera.test_camera()
    
    if success:
        print("✅ Sikeres teszt!")
        print("🎉 A Raspberry Pi kamera működik!")
    else:
        print("❌ Teszt sikertelen")
        print(f"Hiba: {message}")

if __name__ == "__main__":
    test()