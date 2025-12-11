# app_selfie/send_email.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import base64

def kuldo_email(kinek, kep_data):
    """Nagyon egyszerű email küldő"""
    
    # 1. Email összeállítása
    uzenet = MIMEMultipart()
    uzenet['From'] = 'selfiebox.proba@gmail.com'
    uzenet['To'] = kinek
    uzenet['Subject'] = 'SelfieBox Fotó'
    
    # 2. Szöveg hozzáadása
    szoveg = MIMEText('Itt a kép.')
    uzenet.attach(szoveg)
    
    # 3. Kép hozzáadása
    # Eltávolítjuk a "data:image/jpeg;base64," részt
    kep_resz = kep_data.split(',')[1]
    kep_binary = base64.b64decode(kep_resz)
    
    kep = MIMEImage(kep_binary, name='selfie.jpg')
    uzenet.attach(kep)
    
    # 4. Küldés
    try:
        # Csatlakozás Gmail-hez
        szerver = smtplib.SMTP('smtp.gmail.com', 587)
        szerver.starttls()
        
        # BEJELENTKEZÉS - IDE ÍRD A JELSZAVAD!
        szerver.login('selfiebox.proba@gmail.com', 'selfie2000')
        
        # Küldés
        szerver.send_message(uzenet)
        szerver.quit()
        
        return True, "Sikeres"
        
    except Exception as hiba:
        return False, str(hiba)