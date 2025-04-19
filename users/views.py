from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from gspg.models import Magister

from .forms import CustomUserCreationForm, LoginForm

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Si el usuario tiene magisteres asignados, establecer el primero como activo
            if user.magisteres.exists():
                user.active_magister = user.magisteres.first()
                user.save()
            login(request, user)
            messages.success(request, "Registro exitoso.")
            return redirect('home')  # Redirige a la página principal
        else:
            messages.error(request, "Error en el registro. Por favor corrige los errores.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                
                # Si el usuario no tiene un magister activo pero tiene magisteres asignados
                if not user.active_magister and user.magisteres.exists():
                    user.active_magister = user.magisteres.first()
                    user.save()
                
                messages.success(request, "Inicio de sesión exitoso.")
                
                # Obtener la URL de redirección
                next_url = request.GET.get('next', None)
                if next_url:
                    return redirect(next_url)
                return redirect('gspg:dashboard')  # Usa el namespace
            else:
                messages.error(request, "Email o contraseña inválidos.")
        else:
            messages.error(request, "Formulario inválido. Por favor corrige los errores.")
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('users:login')

@login_required
def profile_view(request):
    return render(request, 'users/profile.html')

@login_required
def set_active_programa(request, magister_id):
    """Establece el programa activo del usuario actual"""
    magister = get_object_or_404(Magister, pk=magister_id)
    
    # Verificar que el usuario tenga acceso a este programa
    if not request.user.magisteres.filter(id=magister_id).exists():
        messages.error(request, "No tienes acceso a este programa.")
        return redirect('gspg:dashboard')
    
    # Establecer como programa activo
    request.user.active_magister = magister
    request.user.save()
    
    messages.success(request, f"Has cambiado al programa: {magister.name}")
    
    # Redirigir a la misma página o a dashboard
    next_url = request.GET.get('next', 'gspg:dashboard')
    return redirect(next_url)