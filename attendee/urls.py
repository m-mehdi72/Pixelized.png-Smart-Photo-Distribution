from django.urls import path
from . import views

urlpatterns = [
    path('', views.enter_name, name='attendeeView'),
    path('camera_capture/', views.camera_capture, name='camera_capture'),
    path('capture_face/<str:name>/', views.capture_face, name='capture_face'),
    path('process_face/', views.process_face, name='process_face'),
    path('matched_images/<str:pin_code>/', views.matched_images_view, name='matched_images'),

] 
