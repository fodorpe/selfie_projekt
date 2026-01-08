from django.contrib import admin
from django.utils.safestring import mark_safe  # EZ HIÁNYZOTT!
from .models import AdminSettings, PhotoSession, Photo, UploadedImage










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
    
















@admin.register(UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    """
    Feltöltött képek kezelése
    """
    list_display = ['id', 'get_image_preview', 'upload_date', 'is_active', 'description_short']
    list_filter = ['is_active', 'upload_date']
    list_editable = ['is_active']  # Közvetlenül módosítható a listában
    search_fields = ['description']
    readonly_fields = ['upload_date', 'get_image_detail_preview']
    ordering = ['-upload_date']  # Legújabbak előre
    
    fieldsets = (
        ('Kép információ', {
            'fields': ('description', 'is_active', 'upload_date')
        }),
        ('Kép feltöltése', {
            'fields': ('image',)
        }),
        ('Kép előnézet', {
            'fields': ('get_image_detail_preview',),
            'classes': ('collapse',)  # Összecsukható rész
        }),
    )
    
    # Rövid leírás a listázáshoz
    def description_short(self, obj):
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return "Nincs leírás"
    description_short.short_description = 'Leírás'
    
    # Kép előnézet a listázáshoz - JAVÍTOTT VERZIÓ
    def get_image_preview(self, obj):
        if obj.image:
            try:
                # Ellenőrizzük, hogy van-e fájl
                if not obj.image:
                    return "Nincs kép fájl"
                
                # Lekérjük a relatív URL-t
                image_url = obj.image.url
                
                # Biztosítjuk, hogy a /media/ prefix megfelelő legyen
                if not image_url.startswith('/'):
                    image_url = '/' + image_url
                
                # Kép megjelenítése
                return mark_safe(f'''
                    <div style="width: 80px; height: 60px; overflow: hidden; border-radius: 4px; border: 1px solid #ddd;">
                        <img src="{image_url}" 
                             style="width: 100%; height: 100%; object-fit: cover;"
                             onerror="this.style.display='none'; this.parentElement.innerHTML='<div style=\\'width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#999;\\'>Hiba</div>';">
                    </div>
                ''')
            except Exception as e:
                return f"Hiba: {str(e)[:30]}..."
        return "Nincs kép"
    get_image_preview.short_description = 'Kép'
    
    # Nagyobb kép előnézet a detail view-hoz - JAVÍTOTT VERZIÓ
    def get_image_detail_preview(self, obj):
        if obj.image:
            try:
                # Ellenőrizzük, hogy van-e fájl
                if not obj.image:
                    return "Nincs kép fájl"
                
                # Lekérjük a relatív URL-t
                image_url = obj.image.url
                
                # Biztosítjuk, hogy a /media/ prefix megfelelő legyen
                if not image_url.startswith('/'):
                    image_url = '/' + image_url
                
                # Kép méreteinek lekérése
                try:
                    width = obj.image.width
                    height = obj.image.height
                    dimensions = f"{width}x{height}"
                except:
                    dimensions = "Ismeretlen méret"
                
                # Kép megjelenítése
                return mark_safe(f'''
                    <div style="margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 8px;">
                        <div style="text-align: center; margin-bottom: 10px;">
                            <img src="{image_url}" 
                                 style="max-width: 100%; max-height: 400px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
                                 onerror="this.style.display='none'; this.parentElement.innerHTML='<div style=\\'padding:20px;color:#d00;background:#ffe6e6;border-radius:6px;\\'>Hiba a kép betöltésében</div>';">
                        </div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px;">
                            <p><strong>Fájlnév:</strong> {obj.image.name}</p>
                            <p><strong>Méret:</strong> {dimensions}</p>
                            <p><strong>Elérési út:</strong> {image_url}</p>
                        </div>
                    </div>
                ''')
            except Exception as e:
                return f"Hiba a kép betöltésében: {str(e)}"
        return "Nincs kép"
    get_image_detail_preview.short_description = 'Kép előnézet'
    
    # Batch action: képek aktiválása
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} kép aktiválva lett.')
    make_active.short_description = "Aktív státusz beállítása"
    
    # Batch action: képek deaktiválása
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} kép deaktiválva lett.')
    make_inactive.short_description = "Inaktív státusz beállítása"
    
    actions = ['make_active', 'make_inactive']



