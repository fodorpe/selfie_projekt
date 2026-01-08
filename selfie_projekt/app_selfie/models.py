import uuid
import os
from django.db import models
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import base64
from datetime import datetime

class AdminSettings(models.Model):
    """
    Admin beállítások - csak egy példány lehet
    """
    admin_email = models.EmailField(
        default="admin@example.com",
        help_text="Ez az email cím minden képet megkap másolatként"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Csak egy beállítási objektum lehet
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Nem lehet törölni, csak módosítani
        pass
    
    @classmethod
    def load(cls):
        # Betölti vagy létrehozza a beállításokat
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return f"Admin beállítások - {self.admin_email}"

class PhotoSession(models.Model):
    """
    Fotó munkamenet - a felhasználók adatai
    """
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    user_email = models.EmailField()
    photo_taken = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    admin_notified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user_email} - {self.created_at}"


class Photo(models.Model):
    """
    Elmentett fotók
    """
    photo_session = models.ForeignKey(PhotoSession, on_delete=models.CASCADE, related_name='photos')
    image_base64 = models.TextField(blank=True, null=True, help_text="Base64 kódolt kép")
    image_file = models.ImageField(upload_to='photos/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save_base64_image(self, base64_string, email=None):
        """
        Base64 string mentése fájlba és adatbázisba
        """
        try:
            if not base64_string or not base64_string.startswith('data:image'):
                return False
            
            # Kivágjuk a base64 részt
            image_data = base64.b64decode(base64_string.split(',')[1])
            
            # Fájlnév generálása
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"selfie_{timestamp}_{email or 'unknown'}.jpg"
            
            # Mentés Django ImageField-be
            self.image_file.save(filename, ContentFile(image_data))
            
            # Base64 mentése is (opcionális)
            self.image_base64 = base64_string
            
            self.save()
            return True
            
        except Exception as e:
            print(f"Hiba a kép mentésekor: {str(e)}")
            return False
    
    def get_image_url(self):
        """Kép URL-je"""
        if self.image_file:
            return self.image_file.url
        return None
    
    def __str__(self):
        return f"Photo {self.id} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Fotó'
        verbose_name_plural = 'Fotók'


class UploadedImage(models.Model):
    """
    Képek feltöltésére és tárolására szolgáló modell
    """
    # Kép fájl
    image = models.ImageField(
        upload_to='uploaded_images/%Y/%m/%d/',
        verbose_name='Kép fájl'
    )
    
    # Leírás
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Leírás',
        help_text='Opcionális leírás a képhez'
    )
    
    # Aktív-e a kép (használható-e)
    is_active = models.BooleanField(
        default=True,
        verbose_name='Aktív',
        help_text='A kép használható-e'
    )
    
    # Feltöltés dátuma (automatikusan)
    upload_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Feltöltés dátuma'
    )
    
    class Meta:
        verbose_name = 'Feltöltött kép'
        verbose_name_plural = 'Feltöltött képek'
        ordering = ['-upload_date']  # Legújabbak előre
    
    def __str__(self):
        return f"Kép #{self.id} - {self.upload_date.strftime('%Y.%m.%d %H:%M')}"
    
    def get_image_url(self):
        """Visszaadja a kép URL-jét"""
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return None
    
    @property
    def image_dimensions(self):
        """Visszaadja a kép méreteit (szélesség x magasság)"""
        if self.image and hasattr(self.image, 'width') and hasattr(self.image, 'height'):
            return f"{self.image.width}x{self.image.height}"
        return "Ismeretlen"