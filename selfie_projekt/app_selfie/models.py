# app_selfie/models.py
from django.db import models
import uuid
import os




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

# Photo modellt később adjuk hozzá, ha az AdminSettings működik