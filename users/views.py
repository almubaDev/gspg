from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import CustomUserCreationForm, LoginForm

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
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
    return redirect('login')

@login_required
def profile_view(request):
    return render(request, 'users/profile.html')