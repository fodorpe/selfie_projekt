
from django.contrib import admin
from django.urls import path, include
from app_selfie import views

from django.conf import settings
from django.conf.urls.static import static





urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.email_view, name='email_view'),
    path('selfie/', views.selfie_view, name='selfie_view'),
    path('raspberry/', views.raspberry_camera_view, name='raspberry_camera'),
    path('raspberry-take-photo/', views.raspberry_take_photo, name='raspberry_take_photo'),
    path('kuldes/', views.email_kuldes, name='email_kuldes'),
    path('qr-code/', views.generate_qr_code, name='generate_qr_code'),
    path('qr/', views.qr_display_view, name='qr_display'),
    path('admin2/', views.admin2_view, name='admin2'),
    path('test/', views.test_view, name='test'),
    path('get-latest-overlay/', views.get_latest_overlay, name='get_latest_overlay'),
    path('kuldes/', views.kuldes, name='kuldes'),




    path('raspberry-start-preview/', views.raspberry_start_preview, name='raspberry_start_preview'),
    path('raspberry-stop-preview/', views.raspberry_stop_preview, name='raspberry_stop_preview'),
    path('raspberry-get-preview/', views.raspberry_get_preview, name='raspberry_get_preview'),
    path('raspberry-take-photo/', views.raspberry_take_photo, name='raspberry_take_photo'),






]



# MÉDIA FÁJLOK KISZOLGÁLÁSA DEVELOPMENT MÓDBAN
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)





