from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.http import HttpRequest
from django.conf import settings
from django.conf.urls.static import static

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
    path('app/', include('gspg_client.urls')),
] 
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)