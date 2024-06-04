from django.contrib import admin
from .models import Photographer, Event, Attendees, Image, FaceRecognition

@admin.register(Attendees)
class AttendeesAdmin(admin.ModelAdmin):
    list_display = ['username']
    # search_fields = ('name', 'email')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'photographer', 'unique_link', 'pin_code', 'created_at')
    search_fields = ('name', 'unique_link', 'pin_code')
    list_filter = ('created_at', 'photographer')

@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'event', 'created_at']  # Make sure 'created_at' is a field in the Image model
    list_filter = ['event__created_at']  # Assuming 'created_at' is a field in the 'Event' model

@admin.register(FaceRecognition)
class FaceRecognitionAdmin(admin.ModelAdmin):
    list_display = ('user', 'image', 'created_at')
    search_fields = ('user__username', 'image__id')
    list_filter = ('created_at', 'user', 'image')
