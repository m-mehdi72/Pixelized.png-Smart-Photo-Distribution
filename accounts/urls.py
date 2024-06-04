from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', views.signin, name='login'),
    path('signup/', views.signup, name='signup'),
    path('profile/<slug:username>/events/', views.dashboard, name = 'dashboard'),
    path('profile/<slug:username>/events/<int:event_id>/', views.event_details, name = 'event_details'),

] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)