from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path
from datetime import datetime
import subprocess
import threading
import json
import base64
from io import BytesIO
from PIL import Image
import qrcode

from .send_email import kuldo_email
from .models import PhotoSession, Photo, AdminSettings, UploadedImage
from .raspberry_camera import RaspberryCamera, check_camera, take_photo

# Globális fotó mentési könyvtár
PHOTO_DIR = Path("/home/peti/Desktop/projekt/asd")
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

# Kamera lock a párhuzamos hívásokhoz
CAMERA_LOCK = threading.Lock()

# Inicializáljuk a Raspberry kamerát
camera = RaspberryCamera()


# ---------------------------------------------------------------------------
# Fotó készítése (rpicam-jpeg subprocess hívással)
# ---------------------------------------------------------------------------
@csrf_exempt
def capture_view(request):
    if request.method != "POST":
        return JsonResponse({"saved": False, "error": "Csak POST kérés engedélyezett"}, status=405)

    save_dir = PHOTO_DIR
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime("photo_%Y%m%d_%H%M%S.jpg")
    filepath = save_dir / filename

    try:
        with CAMERA_LOCK:
            subprocess.run([
                "rpicam-jpeg",
                "-o", str(filepath),
                "--width", "640",
                "--height", "480",
                "--nopreview",
                "--immediate",
                "-q", "95"
            ], check=True, timeout=5)

        return JsonResponse({"saved": True, "file": str(filepath)})
    except subprocess.TimeoutExpired:
        return JsonResponse({"saved": False, "error": "A kamera nem válaszolt időben"})
    except Exception as e:
        return JsonResponse({"saved": False, "error": str(e)})


# ---------------------------------------------------------------------------
# Fotó készítése függvényből
# ---------------------------------------------------------------------------
def take_photo_view(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Csak POST kérés engedélyezett"}, status=405)
    try:
        filepath = take_photo(str(PHOTO_DIR))
        return JsonResponse({"success": True, "file": filepath})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# ---------------------------------------------------------------------------
# Preview indítása / leállítása
# ---------------------------------------------------------------------------
@csrf_exempt
def raspberry_start_preview(request):
    if request.method == "POST":
        subprocess.Popen(['rpicam-hello', '--width', '640', '--height', '480', '--timeout', '30000'])
        return JsonResponse({'success': True, 'message': 'Preview elindítva'})


@csrf_exempt
def raspberry_stop_preview(request):
    if request.method == "POST":
        subprocess.run(['pkill', 'rpicam-hello'])
        return JsonResponse({'success': True, 'message': 'Preview leállítva'})


# ---------------------------------------------------------------------------
# Preview kép lekérése base64-ban
# ---------------------------------------------------------------------------
@csrf_exempt
def raspberry_get_preview(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Csak POST kérés engedélyezett'})

    try:
        with CAMERA_LOCK:
            preview_file = PHOTO_DIR / "preview_tmp.jpg"
            subprocess.run([
                'rpicam-jpeg',
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


# ---------------------------------------------------------------------------
# Raspberry kamera oldal
# ---------------------------------------------------------------------------
def raspberry_camera_view(request):
    email = request.GET.get('email', '')

    if not email:
        return HttpResponse("""
            <html>
            <body style="text-align: center; padding: 50px;">
                <h1>⚠️ Nincs email cím!</h1>
                <p>Kérjük, add meg az email címed.</p>
                <a href="/">⬅️ Vissza az email oldalra</a>
            </body>
            </html>
        """)

    camera = RaspberryCamera()
    return render(request, "raspberry_camera.html", {
        'email': email,
        'camera_available': camera.available
    })


# ---------------------------------------------------------------------------
# Selfie készítése Raspberry kamerával
# ---------------------------------------------------------------------------
@csrf_exempt
def raspberry_take_photo(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Csak POST"}, status=405)

    camera = RaspberryCamera()
    if not camera.available:
        return JsonResponse({"success": False, "message": f"Raspberry kamera nem elérhető. Kamera típus: {camera.camera_type}"})

    result = camera.capture_photo()  # dict: success/photo_data/camera_type/message
    return JsonResponse(result)


# ---------------------------------------------------------------------------
# Email és selfie oldalak
# ---------------------------------------------------------------------------
def email_view(request):
    return render(request, "email.html")


def selfie_view(request):
    email = request.GET.get('email', '')

    if not email:
        return HttpResponse("""
            <html>
            <body style="text-align: center; padding: 50px;">
                <h1>⚠️ Nincs email cím!</h1>
                <p>Kérjük, add meg az email címed az előző oldalon.</p>
                <a href="/">⬅️ Vissza az email oldalra</a>
            </body>
            </html>
        """)

    latest_overlay = UploadedImage.objects.filter(is_active=True).order_by('-upload_date').first()
    overlay_url = latest_overlay.image.url if latest_overlay else None

    context = {
        'email': email,
        'overlay_image': latest_overlay,
        'overlay_url': overlay_url,
        'has_overlay': latest_overlay is not None
    }

    return render(request, 'selfie.html', context)


def get_latest_overlay(request):
    try:
        latest_overlay = UploadedImage.objects.filter(is_active=True).order_by('-upload_date').first()
        if not latest_overlay:
            return JsonResponse({'success': False, 'message': 'Nincsenek aktív háttérképek'})

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


# ---------------------------------------------------------------------------
# Selfie email küldés
# ---------------------------------------------------------------------------
@csrf_exempt
def kuldes(request):
    if request.method != 'POST':
        return JsonResponse({'siker': False, 'uzenet': 'Csak POST kérések'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        kep_data = data.get('kep')

        if not email or not kep_data:
            return JsonResponse({'siker': False, 'uzenet': 'Hiányzó adatok'})

        photo_session = PhotoSession.objects.create(user_email=email, photo_taken=True)
        latest_overlay = UploadedImage.objects.filter(is_active=True).order_by('-upload_date').first()
        if latest_overlay:
            photo_session.overlay_image = latest_overlay
            photo_session.save()

        photo = Photo.objects.create(photo_session=photo_session, image_base64=kep_data)
        if kep_data.startswith('data:image'):
            photo.save_base64_image(kep_data, email)

        siker, uzenet = kuldo_email(email, kep_data)

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


# ---------------------------------------------------------------------------
# QR kód generálás és megjelenítés
# ---------------------------------------------------------------------------
def generate_qr_code(request):
    base_url = "http://127.0.0.1:8000"
    qr_url = f"{base_url}/"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/png")


def qr_display_view(request):
    return render(request, 'qr_display.html')


# ---------------------------------------------------------------------------
# Teszt és admin oldalak
# ---------------------------------------------------------------------------
def test_view(request):
    return render(request, "test.html")


def admin2_view(request):
    return render(request, "admin.html")


# ---------------------------------------------------------------------------
# LED Controller (ha van)
# ---------------------------------------------------------------------------
led_controller = None

def init_led_controller():
    global led_controller
    try:
        from .raspberry_led_controller import LEDController
        led_controller = LEDController()
        print("✅ LED Controller inicializálva")
        return True
    except Exception as e:
        print(f"⚠️ LED Controller nem elérhető: {e}")
        led_controller = None
        return False


def raspberry_led_test(request):
    if not led_controller:
        return JsonResponse({'success': False, 'message': 'LED controller nincs inicializálva'})

    try:
        def run_led_sequence():
            led_controller.countdown_sequence(5)
        thread = threading.Thread(target=run_led_sequence)
        thread.start()
        return JsonResponse({'success': True, 'message': 'LED visszaszámlálás indítva (5 másodperc)'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hiba: {str(e)}'})
