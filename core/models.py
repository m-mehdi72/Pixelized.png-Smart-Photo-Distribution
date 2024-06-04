# File: myapp/models.py

import os
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

class Photographer(AbstractUser):
    email = models.EmailField(unique=True)
    # Add unique related names for groups and user_permissions
    groups = models.ManyToManyField('auth.Group', related_name='custom_user_groups')
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_user_permissions')

    def __str__(self):
        return self.username

class Event(models.Model):
    photographer = models.ForeignKey(Photographer, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=255)
    unique_link = models.SlugField(unique=True, blank=True)
    pin_code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.unique_link:
            self.unique_link = slugify(f"{self.name}-{get_random_string(length=8)}")
        if not self.pin_code:
            self.pin_code = get_random_string(length=6, allowed_chars='0123456789')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
def event_image_path(instance, filename):
    # Generate unique filename based on event and image name
    return os.path.join('eventImages', str(instance.event.id), filename)

class Image(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=event_image_path)
    created_at = models.DateTimeField(auto_now_add=True)

class Attendees(models.Model):
    username = models.CharField(max_length=150)
    # Specify the required fields when creating a new user

    # def is_anonymous(self):
    #     return False

    # def is_authenticated(self):
    #     return True

    def __str__(self):
        return self.username

class FaceRecognition(models.Model):
    user = models.ForeignKey(Attendees, on_delete=models.CASCADE, related_name='face_recognitions')
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='face_recognitions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FaceRecognition for {self.user.username} on image {self.image.id}"
