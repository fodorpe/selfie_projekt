from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path
from datetime import datetime
import threading
import subprocess
import base64
import json
from .send_email import kuldo_email
from .models import PhotoSession, Photo, AdminSettings, UploadedImage
from PIL import Image
import io
import qrcode

# --- GLOBALIS BEALLITASOK ---
PHOTO_DIR = Path("/home/peti/Desktop/projekt/asd")
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

CAMERA_LOCK = threading.Lock()  # Garantálja, hogy egyszerre csak egy hívás használja a kamerát

# --- HELYI FUNKCIÓK ---
def is_camera_available() -> bool:
    """Ellenőrizzük, hogy elérhető-e a kamera."""
    try:
        subprocess.run(["rpicam-still", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception:
        return False

def capture_photo_file(width=640, height=480, quality=95) -> Path:
    """Fénykép készítése a kamerával, visszaadja a fájl path-ját."""
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime("photo_%Y%m%d_%H%M%S.jpg")
    filepath = PHOTO_DIR / filename

    with CAMERA_LOCK:
        subprocess.run([
            "rpicam-still",
            "-o", str(filepath),
            "--width", str(width),
            "--height", str(height),
            "--nopreview",
            "--immediate",
            "-q", str(quality)
        ], check=True, timeout=5)

    return filepath

# --- VIEWS ---

def email_view(request):
    return render(request, "email.html")

def selfie_view(request):
    email = request.GET.get('email', '')
    if not email:
        return HttpResponse("""
            <html><body style="text-align:center;padding:50px;">
            <h1>⚠️ Nincs email cím!</h1>
            <p>Kérjük, add meg az email címet.</p>
            <a href="/">⬅️ Vissza</a></body></html>
        """)

    latest_overlay = UploadedImage.objects.filter(is_active=True).order_by('-upload_date').first()
    overlay_url = latest_overlay.image.url if latest_overlay else None

    return render(request, 'selfie.html', {
        'email': email,
        'overlay_image': latest_overlay,
        'overlay_url': overlay_url,
        'has_overlay': latest_overlay is not None
    })

def raspberry_view(request):
    email = request.GET.get('email', '')
    return render(request, 'camera.html', {
        'email': email,
        'camera_available': is_camera_available()
    })

@csrf_exempt
def raspberry_start_preview(request):
    """Preview indítása (csak háttérben)."""
    if request.method == 'POST':
        with CAMERA_LOCK:
            subprocess.Popen([
                'rpicam-hello',
                '--width', '640',
                '--height', '480',
                '--timeout', '30000'
            ])
        return JsonResponse({'success': True, 'message': 'Preview elindítva'})

@csrf_exempt
def raspberry_stop_preview(request):
    """Preview leállítása."""
    if request.method == 'POST':
        with CAMERA_LOCK:
            subprocess.run(['pkill', 'rpicam-hello'])
        return JsonResponse({'success': True, 'message': 'Preview leállítva'})

@csrf_exempt
def raspberry_get_preview(request):
    """Webes preview lekérése Base64 formátumban."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Csak POST'})

    try:
        with CAMERA_LOCK:
            preview_file = PHOTO_DIR / "preview_tmp.jpg"
            subprocess.run([
                'rpicam-still',
                '--zsl',   # Zero Shutter Lag → gyors preview
                '-o', str(preview_file),
                '--width', '320',
                '--height', '240',
                '--nopreview',
                '--immediate',
                '-q', '50'
            ], check=True, timeout=5)

            with open(preview_file, 'rb') as f:
                jpeg_bytes = f.read()

            base64_image = base64.b64encode(jpeg_bytes).decode("utf-8")

        return JsonResponse({
            'success': True,
            'photo_data': f"data:image/jpeg;base64,{base64_image}",
            'message': 'Valós preview kép'
        })

    except subprocess.TimeoutExpired:
        return JsonResponse({'success': False, 'message': 'A kamera nem válaszolt időben'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
def raspberry_take_photo(request):
    """Fotó készítése és mentése a szerverre."""
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Csak POST"}, status=405)

    if not is_camera_available():
        return JsonResponse({"success": False, "message": "Raspberry kamera nem elérhető"})

    try:
        filepath = capture_photo_file()
        return JsonResponse({"success": True, "file": str(filepath)})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})

# --- Overlay lekérdezés ---
def get_latest_overlay(request):
    try:
        latest_overlay = UploadedImage.objects.filter(is_active=True).order_by('-upload_date').first()
        if not latest_overlay:
            return JsonResponse({'success': False, 'message': 'Nincsenek aktív overlay képek'})

        return JsonResponse({
            'success': True,
            'overlay': {
                'id': latest_overlay.id,
                'url': latest_overlay.image.url,
                'description': latest_overlay.description or "Nincs leírás",
                'upload_date': latest_overlay.upload_date.strftime('%Y.%m.%d %H:%M'),
                'is_latest': True
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# --- Email küldés funkció ---
@csrf_exempt
def kuldes(request):
    if request.method != 'POST':
        return JsonResponse({'siker': False, 'uzenet': 'Csak POST kérések'})

    try:
        data = json.loads(request.body)
        email = data.get('email')
        kep_data = data.get('kep')

        if not email or not kep_data:
            return JsonResponse({'siker': False, 'uzenet': 'Hiányzó adatok'})

        # PhotoSession létrehozása
        photo_session = PhotoSession.objects.create(user_email=email, photo_taken=True)

        latest_overlay = UploadedImage.objects.filter(is_active=True).order_by('-upload_date').first()
        if latest_overlay:
            photo_session.overlay_image = latest_overlay
            photo_session.save()

        photo = Photo.objects.create(photo_session=photo_session, image_base64=kep_data)
        if kep_data.startswith('data:image'):
            photo.save_base64_image(kep_data, email)

        siker, uzenet = kuldo_email(email, kep_data)

        # Admin értesítés
        try:
            admin_settings = AdminSettings.load()
            if admin_settings.admin_email:
                kuldo_email(admin_settings.admin_email, kep_data)
                photo_session.admin_notified = True
                photo_session.save()
        except Exception as admin_error:
            print(f"Admin értesítés hiba: {admin_error}")

        return JsonResponse({
            'siker': siker,
            'uzenet': uzenet,
            'session_id': str(photo_session.session_id),
            'overlay_used': latest_overlay is not None,
            'overlay_id': latest_overlay.id if latest_overlay else None
        })
    except Exception as e:
        return JsonResponse({'siker': False, 'uzenet': str(e)})

# --- QR kód és teszt oldal ---
def generate_qr_code(request):
    base_url = "http://127.0.0.1:8000"
    qr_url = f"{base_url}/"
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/png")

def qr_display_view(request):
    return render(request, 'qr_display.html')

def test_view(request):
    return render(request, "test.html")
