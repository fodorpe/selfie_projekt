from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import base64
import qrcode
from io import BytesIO
from .send_email import kuldo_email
from .models import PhotoSession, Photo, AdminSettings, UploadedImage


from PIL import Image
import io
from django.core.files.base import ContentFile











import subprocess


# IMPORTÁLJUK A RASPBERRY KAMERÁT
from .raspberry_camera import RaspberryCamera

from .raspberry_camera import check_camera, take_photo

from pathlib import Path
from datetime import datetime
import time
from picamera2 import Picamera2


SAVE_DIR = "/home/pi/photos"




import threading
CAMERA_LOCK = threading.Lock()

with CAMERA_LOCK:
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    time.sleep(0.2)
    frame = picam2.capture_array()
    picam2.stop()
    picam2.close()
    camera_lock = threading.Lock()











try:
    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration())
    picam2.start()
    camera_available = True
except Exception as e:
    print("Camera init error:", e)
    camera_available = False


def capture_view(request):
    if not camera_available:
        return JsonResponse(
            {"saved": False, "error": "Camera not available"},
            status=500
        )

    with camera_lock:
        save_dir = Path("/home/pi/photos")
        save_dir.mkdir(parents=True, exist_ok=True)

        filename = datetime.now().strftime("photo_%Y%m%d_%H%M%S.jpg")
        filepath = save_dir / filename

        time.sleep(0.2)
        picam2.capture_file(str(filepath))

    return JsonResponse({"saved": True, "file": str(filepath)})









def take_photo(save_dir: str) -> str:
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    filename = datetime.now().strftime("photo_%Y%m%d_%H%M%S.jpg")
    fullpath = save_path / filename

    picam2 = Picamera2()

    # Egyszerű still config (a kamera a legnagyobb támogatott felbontást is tudja,
    # de itt lehet explicit beállítani)
    config = picam2.create_still_configuration()
    picam2.configure(config)

    picam2.start()
    time.sleep(0.2)  # rövid "warm-up", hogy stabil legyen az expo/awb
    picam2.capture_file(str(fullpath))
    picam2.stop()
    picam2.close()

    return str(fullpath)

if __name__ == "__main__":
    print(take_photo("/home/pi/photos"))



















@csrf_exempt
def raspberry_start_preview(request):
    """Preview indítása - EMOJI NÉLKÜL"""
    print(f"[START PREVIEW] /raspberry-start-preview/ - {request.method}")
    
    if request.method == 'POST':
        try:
            # Itt a kamera indítás kódja
            print("Kamera preview indítása...")
            
            return JsonResponse({
                'success': True,
                'message': 'Preview elindítva'
            })
        except Exception as e:
            print(f"HIBA: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Hiba: {str(e)}'
            })
    
    return JsonResponse({
        'success': True,
        'message': 'GET kérés - POST-ot használj'
    })

@csrf_exempt
def raspberry_stop_preview(request):
    """Preview leállítása - EMOJI NÉLKÜL"""
    print(f"[STOP PREVIEW] /raspberry-stop-preview/ - {request.method}")
    
    if request.method == 'POST':
        print("Kamera preview leállítása...")
        return JsonResponse({
            'success': True,
            'message': 'Preview leállítva'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Csak POST'
    })

@csrf_exempt
def raspberry_get_preview(request):
    print(f"[GET PREVIEW] /raspberry-get-preview/ - {request.method}")

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Csak POST'
        })

    try:
        print("Preview kép készítése...")

        picam2 = Picamera2()

        # Preview-hoz kisebb felbontás → gyorsabb
        config = picam2.create_preview_configuration(
            main={"size": (640, 480)}
        )
        picam2.configure(config)

        picam2.start()
        time.sleep(0.2)

        # Kép beolvasása numpy array-ként
        frame = picam2.capture_array()

        picam2.stop()
        picam2.close()

        # Numpy → PIL Image
        image = Image.fromarray(frame)

        # JPEG memóriába
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        jpeg_bytes = buffer.getvalue()

        # Base64
        base64_image = base64.b64encode(jpeg_bytes).decode("utf-8")

        return JsonResponse({
            'success': True,
            'photo_data': f"data:image/jpeg;base64,{base64_image}",
            'message': 'Valós preview kép'
        })

    except Exception as e:
        print(f"HIBA: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


























def raspberry_view(request):
    email = request.GET.get('email', '')
    return render(request, 'camera.html', {
        'email': email,
        'camera_available': check_camera()
    })

def take_photo_view(request):
    if request.method == 'POST':
        result = take_photo()
        return JsonResponse(result)






def raspberry_camera_view(request):
    """
    Raspberry Pi kamera felület
    """
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
    
    # Ellenőrizzük, hogy elérhető-e a Raspberry kamera - DINAMIKUSAN!
    camera = RaspberryCamera()

    
    if not camera.available:
        return render(request, "error.html", {
            'error': "Raspberry kamera nem elérhető",
            'message': "A kamera nem válaszol a rpicam-hello hívásra." #itt volt libcamera-helo
    })
    
    return render(request, "raspberry_camera.html", {
        'email': email,
        'camera_available': camera_available
    })







@csrf_exempt
def raspberry_take_photo(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Csak POST"}, status=405)

    camera = RaspberryCamera()

    # Itt inkább ezt használd:
    if not camera.available:
        return JsonResponse({
            "success": False,
            "message": f"Raspberry kamera nem elérhető. Kamera típus: {camera.camera_type}"
        })

    result = camera.capture_photo()  # ez egy dict: success/photo_data/camera_type/message

    # Visszaadjuk úgy, ahogy van
    return JsonResponse(result)

    















def email_view(request):
    """Email cím bekérése és kamera választás"""
    return render(request, "email.html")



def selfie_view(request):
    """Selfie/kamera oldal"""
    # Kiolvassuk az email címet a GET paraméterből
    email = request.GET.get('email', '')
    
    if not email:
        # Ha nincs email, visszaküldjük az email oldalra
        return HttpResponse("""
            <html>
            <body style="text-align: center; padding: 50px;">
                <h1>⚠️ Nincs email cím!</h1>
                <p>Kérjük, add meg az email címed az előző oldalon.</p>
                <a href="/">⬅️ Vissza az email oldalra</a>
            </body>
            </html>
        """)
    
    # Legutóbbi aktív overlay kép kiválasztása
    latest_overlay = None
    overlay_url = None
    
    try:
        latest_overlay = UploadedImage.objects.filter(
            is_active=True
        ).order_by('-upload_date').first()
        
        if latest_overlay:
            overlay_url = latest_overlay.image.url
            
            # ÜZENET A KONZOLRA (debug célokra)
            print(f"[INFO] Legutóbbi overlay: {latest_overlay.id} - {latest_overlay.description}")
            print(f"[INFO] Overlay URL: {overlay_url}")
    except Exception as e:
        print(f"[HIBA] Overlay betöltés: {e}")
    
    # Az email cím átadása a template-nek
    context = {
        'email': email,
        'overlay_image': latest_overlay,  # Az egész objektum
        'overlay_url': overlay_url,       # Vagy csak az URL
        'has_overlay': latest_overlay is not None
    }
    
    return render(request, 'selfie.html', context)




    # Átadjuk az email címet a template-nek
    return render(request, "selfie.html", {'email': email})






def get_latest_overlay(request):
    """Visszaadja a legutóbb feltöltött aktív overlay képet"""
    try:
        # Csökkenő sorrendben rendezzük, és az elsőt vesszük
        latest_overlay = UploadedImage.objects.filter(
            is_active=True
        ).order_by('-upload_date').first()
        
        if not latest_overlay:
            return JsonResponse({
                'success': False,
                'message': 'Nincsenek aktív háttérképek'
            })
        
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
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@csrf_exempt
def kuldes(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            kep_data = data.get('kep')
            
            if not email or not kep_data:
                return JsonResponse({'siker': False, 'uzenet': 'Hiányzó adatok'})
            
            # 1. PhotoSession létrehozása
            photo_session = PhotoSession.objects.create(
                user_email=email,
                photo_taken=True
            )
            
            # 2. LEGUTÓBBI AKTÍV OVERLAY KÉP KIVÁLASZTÁSA
            latest_overlay = UploadedImage.objects.filter(
                is_active=True
            ).order_by('-upload_date').first()
            
            if latest_overlay:
                photo_session.overlay_image = latest_overlay
                photo_session.save()  # MENTÉS IDE
            
            # 3. Photo létrehozása és mentése
            photo = Photo.objects.create(
                photo_session=photo_session,
                image_base64=kep_data
            )
            
            # Base64 kép fájlba mentése
            if kep_data.startswith('data:image'):
                photo.save_base64_image(kep_data, email)
            
            # 4. Email küldése
            siker, uzenet = kuldo_email(email, kep_data)
            
            # 5. Admin értesítése
            try:
                admin_settings = AdminSettings.load()
                if admin_settings.admin_email:
                    kuldo_email(admin_settings.admin_email, kep_data)
                    photo_session.admin_notified = True
                    photo_session.save()  # MENTÉS IDE
            except Exception as admin_error:
                print(f"Admin értesítés hiba: {admin_error}")
                # Ne álljon meg a folyamat, csak logold a hibát
            
            return JsonResponse({
                'siker': siker, 
                'uzenet': uzenet,
                'session_id': str(photo_session.session_id),
                'overlay_used': latest_overlay is not None,
                'overlay_id': latest_overlay.id if latest_overlay else None
            })
            
        except Exception as e:
            return JsonResponse({'siker': False, 'uzenet': str(e)})
    
    return JsonResponse({'siker': False, 'uzenet': 'Csak POST kérések'})












@csrf_exempt
def email_kuldes(request):
    """Email küldés - most már admin emaillel is ÉS kép mentéssel"""
    
    try:
        import json, smtplib, base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.image import MIMEImage
        from .models import AdminSettings, PhotoSession, Photo  # Photo importálása
        
        # 1. Adatok kiolvasása
        data = json.loads(request.body)
        fogado_email = data.get('email', '')
        kep_data = data.get('kep', '')
        
        print("=" * 50)
        print("EMAIL KÜLDÉS - ADMIN COPY ÉS KÉP MENTÉS")
        print("=" * 50)
        
        # 2. Admin beállítások betöltése
        admin_settings = AdminSettings.load()
        admin_email = admin_settings.admin_email
        
        print(f"Küldő: selfiebox.proba@gmail.com")
        print(f"Címzett: {fogado_email}")
        print(f"Admin másolat: {admin_email}")
        
        # 3. PhotoSession létrehozása
        session = PhotoSession.objects.create(
            user_email=fogado_email,
            photo_taken=True
        )
        
        # 4. KÉP MENTÉSE AZ ADATBÁZISBA - EZ AZ ÚJ RÉSZ!
        photo_saved = False
        if kep_data and kep_data.startswith('data:image'):
            try:
                # Photo objektum létrehozása
                photo = Photo.objects.create(
                    photo_session=session
                )
                
                # Base64 kép mentése
                photo_saved = photo.save_base64_image(kep_data, fogado_email)
                
                if photo_saved:
                    print(f"✅ Kép mentve az adatbázisba: Photo ID {photo.id}")
                else:
                    print("⚠️ Kép mentése sikertelen")
                    
            except Exception as save_error:
                print(f"⚠️ Hiba a kép mentésekor: {save_error}")
        
        # 5. Email összeállítása (eredeti címzettnek)
        msg_to_user = MIMEMultipart()
        msg_to_user['From'] = 'selfiebox.proba@gmail.com'
        msg_to_user['To'] = fogado_email
        msg_to_user['Subject'] = 'SelfieBox Fotó'
        
        # Szövegtörzs
        body_text = f"""Itt a kép a SelfieBox-ból! 🎉

Munkamenet ID: {session.session_id}
Időpont: {session.created_at.strftime('%Y.%m.%d %H:%M:%S')}
"""
        msg_to_user.attach(MIMEText(body_text, 'plain'))
        
        # 6. Kép csatolása
        if kep_data and kep_data.startswith('data:image'):
            kep_resz = kep_data.split(',')[1]
            kep_binary = base64.b64decode(kep_resz)
            image = MIMEImage(kep_binary, name='selfie_foto.jpg')
            msg_to_user.attach(image)
            print(f"✅ Kép csatolva: {len(kep_binary)} byte")
            
            # 7. Admin email összeállítása (másolat)
            msg_to_admin = MIMEMultipart()
            msg_to_admin['From'] = 'selfiebox.proba@gmail.com'
            msg_to_admin['To'] = admin_email
            msg_to_admin['Subject'] = f'[SelfieBox] Új kép - {fogado_email}'
            
            admin_body = f"""
            Új SelfieBox fotó érkezett!
            
            Felhasználó: {fogado_email}
            Munkamenet ID: {session.session_id}
            Időpont: {session.created_at}
            Kép mentve az adatbázisba: {'IGEN' if photo_saved else 'NEM'}
            
            A kép csatolva van.
            """
            
            msg_to_admin.attach(MIMEText(admin_body, 'plain'))
            msg_to_admin.attach(MIMEImage(kep_binary, name=f'selfie_{session.session_id}.jpg'))
        else:
            print("⚠️ Nincs kép adat")
            return JsonResponse({
                'siker': False,
                'uzenet': 'Nincs kép adat!'
            })
        
        # 8. SMTP kapcsolat és küldés
        print("-" * 30)
        print("Kapcsolódás...")
        
        # APP PASSWORD
        APP_PASSWORD = "xocg izix evbx qrhc"
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('selfiebox.proba@gmail.com', APP_PASSWORD)
        
        # 9. Küldés a FELHASZNÁLÓNAK
        print("Küldés a felhasználónak...")
        server.send_message(msg_to_user)
        
        # 10. Küldés az ADMINNAK (másolat)
        print("Küldés az adminnak (másolat)...")
        server.send_message(msg_to_admin)
        
        server.quit()
        
        # 11. Adatbázis frissítése
        session.admin_notified = True
        session.save()
        
        print("=" * 50)
        print("EMAIL SIKERESEN ELKÜLDVE ÉS KÉP ELMENTVE!")
        print(f"   Felhasználó: {fogado_email}")
        print(f"   Admin: {admin_email}")
        print(f"   Kép mentve: {'IGEN' if photo_saved else 'NEM'}")
        print("=" * 50)
        
        return JsonResponse({
            'siker': True,
            'uzenet': f'✅ Kép elküldve! Másolat: {admin_email}',
            'photo_saved': photo_saved,
            'session_id': str(session.session_id)
        })
        
    except Exception as error:
        print(f"HIBA: {type(error).__name__}: {error}")
        return JsonResponse({
            'siker': False,
            'uzenet': f'Hiba: {type(error).__name__}'
        })






# Globális LED controller (ha van)
led_controller = None

def init_led_controller():
    """LED controller inicializálása (ha Raspberry Pi-en fut)"""
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
    """LED teszt endpoint"""
    if not led_controller:
        return JsonResponse({
            'success': False,
            'message': 'LED controller nincs inicializálva'
        })
    
    try:
        # Szálban futtatjuk, hogy ne blokkolja a web kérést
        def run_led_sequence():
            led_controller.countdown_sequence(5)
        
        thread = threading.Thread(target=run_led_sequence)
        thread.start()
        
        return JsonResponse({
            'success': True,
            'message': 'LED visszaszámlálás indítva (5 másodperc)'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Hiba: {str(e)}'
        })






















'''
@csrf_exempt
def email_kuldes(request):
    """Email küldés selfiebox.proba@gmail.com címmel"""
    
    try:
        import json, smtplib, base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.image import MIMEImage
        
        # Adatok kiolvasása
        adat = json.loads(request.body)
        kinek = adat.get('email')  # Címzett (pl: petivadasz06@gmail.com)
        kep_data = adat.get('kep')
        
        print(f"✉️ Küldés: selfiebox.proba@gmail.com → {kinek}")
        
        # 1. Email összeállítása
        uzenet = MIMEMultipart()
        uzenet['From'] = 'selfiebox.proba@gmail.com'  # ÚJ EMAIL
        uzenet['To'] = kinek
        uzenet['Subject'] = 'SelfieBox Fotó'
        
        # 2. Szöveg
        uzenet.attach(MIMEText('Itt a kép.', 'plain'))
        
        # 3. Kép hozzáadása
        if kep_data and kep_data.startswith('data:image'):
            kep_resz = kep_data.split(',')[1]
            kep_binary = base64.b64decode(kep_resz)
            kep = MIMEImage(kep_binary, name='selfie.jpg')
            uzenet.attach(kep)
            print(f"📷 Kép csatolva: {len(kep_binary)} byte")
        else:
            print("⚠️ Nincs kép adat, vagy hibás formátum")
        
        # 4. SMTP kapcsolat
        print("🔗 Kapcsolódás Gmail-hez...")
        
        szerver = smtplib.SMTP('smtp.gmail.com', 587)
        szerver.starttls()
        
        # JELSZÓ - fontos: NINCS ÉKEZET!
        # App password-t kell generálni ehhez az emailhez is!
        jelszo = "xocg izix evbx qrhc "  # selfiebox.proba@gmail.com app password
        
        # Jelszó tisztítása (nincs ékezet)
        jelszo_tiszta = ''.join(c for c in jelszo if ord(c) < 128)
        print(f"🔐 Bejelentkezés: selfiebox.proba@gmail.com")
        print(f"   Jelszó hossz: {len(jelszo_tiszta)}")
        
        szerver.login('selfiebox.proba@gmail.com', jelszo_tiszta)
        
        print("✅ Bejelentkezve, küldés...")
        szerver.send_message(uzenet)
        szerver.quit()
        
        print("✅ Email sikeresen elküldve!")
        return JsonResponse({'siker': True, 'uzenet': 'Email elküldve!'})
        
    except smtplib.SMTPAuthenticationError as auth_error:
        print(f"❌ Bejelentkezési hiba: {auth_error}")
        return JsonResponse({
            'siker': False, 
            'uzenet': 'Hibás email cím vagy jelszó!'
        })
        
    except Exception as hiba:
        print(f"❌ HIBA: {type(hiba).__name__}: {str(hiba)[:100]}")
        return JsonResponse({
            'siker': False, 
            'uzenet': f'Hiba: {type(hiba).__name__}'
        })
'''


def test_view(request):
    """Teszt oldal"""
    return render(request, "test.html")





def generate_qr_code(request):
    """QR kód generálása - LOKÁLIS TESZTHEZ"""
    
    # Csak localhost - laptopon tesztelünk
    base_url = "http://127.0.0.1:8000"
    qr_url = f"{base_url}/"
    
    print(f"💻 QR kód URL (lokális): {qr_url}")
    
    # QR kód generálása
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Kép mentése bufferbe
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return HttpResponse(buffer.getvalue(), content_type="image/png")







def qr_display_view(request):
    """QR kód megjelenítő oldal"""
    return render(request, 'qr_display.html')











def admin2_view(request):
    """Admin oldal"""
    return render(request, "admin.html")