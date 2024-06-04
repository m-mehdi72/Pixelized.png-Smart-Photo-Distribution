from django import forms
from core.models import Attendees

class AttendeeForm(forms.ModelForm):
    class Meta:
        model = Attendees
        fields = ['username'] 