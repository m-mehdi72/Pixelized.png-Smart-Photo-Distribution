from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import SignUpForm, SignInForm, EventForm
from django.shortcuts import render, get_object_or_404
from core.models import Event, Image, Photographer
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your views here.
def signin(request):
    if request.method == 'POST':
        form = SignInForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(reverse('dashboard', kwargs={'username': username}))  # Redirect to a success page.
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = SignInForm()
    
    return render(request, 'sign-in.html', {'form': form})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'sign-up.html', {'form': form})


@login_required
def dashboard(request, username):

    events = Event.objects.filter(photographer=request.user)
    user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.photographer = request.user  # Set the photographer to the current user
            event.save()
            return render(request, 'dashboard.html', {'user': user,
                                              'events': events,
                                              'form': form,
                                              'username': username
                                              })
    else:
        form = EventForm()

    return render(request, 'dashboard.html', {'user': user,
                                              'events': events,
                                              'form': form,
                                              'username': username
                                              })

@login_required
def event_details(request, username, event_id):
    event = get_object_or_404(Event, id=event_id, photographer__username=username)
    # media = get_object_or_404(Image, image= image)
    images = request.FILES.getlist('images')

    if request.method == 'POST':
        images = request.FILES.getlist('images')
        image_list = []
        for image in images:
            photo = Image(
                event=event,
                image=image
            )
            photo.save()    
            image_list.append(photo.image.url)
        print(image_list)
        context = {
            # 'images': image_list,
            'event': event,
        }
        return render(request, 'event-details.html', context)
    # imagess = event.images.all()
    context = {
        'event': event, 
        # 'images': imagess,
    }
    return render(request, 'event-details.html', context)