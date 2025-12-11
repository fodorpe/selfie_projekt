from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import base64
import qrcode
from io import BytesIO
from .send_email import kuldo_email
from .models import AdminSettings, PhotoSession




# IMPORTÁLJUK A RASPBERRY KAMERÁT
try:
    from .raspberry_camera import RaspberryCamera
    RASPBERRY_CAMERA_AVAILABLE = True
except ImportError:
    RASPBERRY_CAMERA_AVAILABLE = False
    RaspberryCamera = None








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
    
    # Ellenőrizzük, hogy elérhető-e a Raspberry kamera
    if not RASPBERRY_CAMERA_AVAILABLE:
        return render(request, "error.html", {
            'error': "Raspberry kamera nem elérhető",
            'message': "A rendszer nem találja a Raspberry kamerát. Próbáld a laptop kamerát."
        })
    
    return render(request, "raspberry_camera.html", {
        'email': email,
        'camera_available': RASPBERRY_CAMERA_AVAILABLE
    })






@csrf_exempt
def raspberry_take_photo(request):
    """
    Kép készítése Raspberry Pi kamerával
    """
    try:
        if not RASPBERRY_CAMERA_AVAILABLE:
            return JsonResponse({
                'success': False,
                'message': 'Raspberry kamera nem elérhető'
            })
        
        # Kép készítése
        camera = RaspberryCamera()
        photo_data = camera.take_photo_base64()
        
        if photo_data:
            return JsonResponse({
                'success': True,
                'photo_data': photo_data,
                'message': 'Kép sikeresen készült'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Nem sikerült képet készíteni'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Hiba: {str(e)}'
        })
    















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
    
    # Átadjuk az email címet a template-nek
    return render(request, "selfie.html", {'email': email})




@csrf_exempt
def email_kuldes(request):
    """Email küldés - most már admin emaillel is"""
    
    try:
        import json, smtplib, base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.image import MIMEImage
        from .models import AdminSettings, PhotoSession
        
        # 1. Adatok kiolvasása
        data = json.loads(request.body)
        fogado_email = data.get('email', '')
        kep_data = data.get('kep', '')
        
        print("=" * 50)
        print("[EMAIL] EMAIL KÜLDÉS - ADMIN COPY")
        print("=" * 50)
        
        # 2. Admin beállítások betöltése
        admin_settings = AdminSettings.load()
        admin_email = admin_settings.admin_email
        
        print(f"📍 Küldő: selfiebox.proba@gmail.com")
        print(f"📍 Címzett: {fogado_email}")
        print(f"📍 Admin másolat: {admin_email}")
        
        # 3. PhotoSession létrehozása
        session = PhotoSession.objects.create(
            user_email=fogado_email,
            photo_taken=True
        )
        
        # 4. Email összeállítása (eredeti címzettnek)
        msg_to_user = MIMEMultipart()
        msg_to_user['From'] = 'selfiebox.proba@gmail.com'
        msg_to_user['To'] = fogado_email
        msg_to_user['Subject'] = 'SelfieBox Fotó'
        
        # Szövegtörzs
        body_text = f"Itt a kép a SelfieBox-ból! 🎉\n\nMunkamenet ID: {session.session_id}"
        msg_to_user.attach(MIMEText(body_text, 'plain'))
        
        # 5. Kép csatolása
        if kep_data and kep_data.startswith('data:image'):
            kep_resz = kep_data.split(',')[1]
            kep_binary = base64.b64decode(kep_resz)
            image = MIMEImage(kep_binary, name='selfie_foto.jpg')
            msg_to_user.attach(image)
            print(f"✅ Kép csatolva: {len(kep_binary)} byte")
            
            # 6. Admin email összeállítása (másolat)
            msg_to_admin = MIMEMultipart()
            msg_to_admin['From'] = 'selfiebox.proba@gmail.com'
            msg_to_admin['To'] = admin_email
            msg_to_admin['Subject'] = f'[SelfieBox] Új kép - {fogado_email}'
            
            admin_body = f"""
            Új SelfieBox fotó érkezett!
            
            Felhasználó: {fogado_email}
            Munkamenet ID: {session.session_id}
            Időpont: {session.created_at}
            
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
        
        # 7. SMTP kapcsolat és küldés
        print("-" * 30)
        print("🔗 Kapcsolódás...")
        
        # APP PASSWORD - IDE ÍRD A SAJÁTOD!
        APP_PASSWORD = "xocg izix evbx qrhc"
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('selfiebox.proba@gmail.com', APP_PASSWORD)
        
        # 8. Küldés a FELHASZNÁLÓNAK
        print("📤 Küldés a felhasználónak...")
        server.send_message(msg_to_user)
        
        # 9. Küldés az ADMINNAK (másolat)
        print("📋 Küldés az adminnak (másolat)...")
        server.send_message(msg_to_admin)
        
        server.quit()
        
        # 10. Adatbázis frissítése
        session.admin_notified = True
        session.save()
        
        print("=" * 50)
        print("🎉 EMAIL SIKERESEN ELKÜLDVE!")
        print(f"   ➤ Felhasználó: {fogado_email}")
        print(f"   ➤ Admin: {admin_email}")
        print("=" * 50)
        
        return JsonResponse({
            'siker': True,
            'uzenet': f'✅ Kép elküldve! Másolat: {admin_email}'
        })
        
    except Exception as error:
        print(f"❌ HIBA: {type(error).__name__}: {error}")
        return JsonResponse({
            'siker': False,
            'uzenet': f'Hiba: {type(error).__name__}'
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