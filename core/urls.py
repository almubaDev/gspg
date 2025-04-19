from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.http import HttpRequest

def home_redirect(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('gspg:dashboard')
    return redirect('users:login')

urlpatterns = [
    path('', home_redirect, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include(('gspg.urls', 'gspg'), namespace='gspg')),
    path('', include(('users.urls', 'users'), namespace='users')),
]
