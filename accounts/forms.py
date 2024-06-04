from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from core.models import Event, Image

User = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class SignInForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'm-8fb7ebe7 mantine-Input-input mantine-TextInput-input',
        'placeholder': 'Username',
        'aria-invalid': 'false',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'm-8fb7ebe7 mantine-Input-input mantine-TextInput-input',
        'placeholder': 'Password',
        'aria-invalid': 'false',
    }))

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name'] 

# class ImageUploadForm(forms.Form):
#     image = forms.ImageField(widget=forms.ClearableFileInput(), required=True)
#     class Meta:
#         model = Image
#         fields = ['image_path']