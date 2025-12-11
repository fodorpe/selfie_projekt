from django.contrib import admin
from .models import AdminSettings, PhotoSession

@admin.register(AdminSettings)
class AdminSettingsAdmin(admin.ModelAdmin):
    """
    Admin beállítások kezelése
    """
    list_display = ['admin_email', 'updated_at']
    
    # Csak egy objektum lehet
    def has_add_permission(self, request):
        return not AdminSettings.objects.exists()
    
    # Nem lehet törölni
    def has_delete_permission(self, request, obj=None):
        return False
    
    actions = None  # Nincs törlés

@admin.register(PhotoSession)
class PhotoSessionAdmin(admin.ModelAdmin):
    """
    Fotó munkamenetek kezelése
    """
    list_display = ['user_email', 'session_id', 'photo_taken', 'admin_notified', 'created_at']
    list_filter = ['photo_taken', 'admin_notified', 'created_at']
    search_fields = ['user_email', 'session_id']
    readonly_fields = ['session_id', 'created_at']
    
    fieldsets = (
        ('Alap információk', {
            'fields': ('user_email', 'session_id', 'created_at')
        }),
        ('Státusz', {
            'fields': ('photo_taken', 'admin_notified')
        }),
    )