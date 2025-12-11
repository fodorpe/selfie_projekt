
from django.contrib import admin
from django.urls import path
from app_selfie import views

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

]