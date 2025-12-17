from django.contrib import admin
from django.utils.safestring import mark_safe  # EZ HIÁNYZOTT!
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




from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import AdminSettings, PhotoSession, Photo

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'photo_session', 'created_at', 'get_image_preview']  # get_image_preview
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'get_image_preview_field']  # külön field
    search_fields = ['photo_session__user_email']
    
    fieldsets = (
        ('Alap információk', {
            'fields': ('photo_session', 'created_at')
        }),
        ('Kép', {
            'fields': ('image_file', 'get_image_preview_field', 'image_base64')
        }),
    )
    
    # 1. Listázáshoz
    def get_image_preview(self, obj):
        if obj.image_file:
            try:
                return mark_safe(f'<img src="{obj.image_file.url}" width="50" height="50" style="object-fit: cover;" />')
            except:
                return "Fájl nem található"
        elif obj.image_base64:
            return mark_safe(f'<img src="{obj.image_base64}" width="50" height="50" style="object-fit: cover;" />')
        return "Nincs kép"
    get_image_preview.short_description = 'Kép'
    
    # 2. Detail view-hoz (readonly_fields)
    def get_image_preview_field(self, obj):
        if obj.image_file:
            try:
                return mark_safe(f'<img src="{obj.image_file.url}" width="200" height="200" style="object-fit: cover;" />')
            except:
                return "Fájl nem található"
        elif obj.image_base64:
            return mark_safe(f'<img src="{obj.image_base64}" width="200" height="200" style="object-fit: cover;" />')
        return "Nincs kép"
    get_image_preview_field.short_description = 'Kép előnézet'
    



# A mark_safe importálása
from django.utils.safestring import mark_safe



