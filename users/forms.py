from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from django import forms

from .models import CustomUser
from gspg.models import Magister

class CustomUserCreationForm(UserCreationForm):
    """
    Formulario para crear nuevos usuarios. Incluye todos los campos requeridos,
    más un campo repetido para verificación de contraseña.
    """
    magisteres = forms.ModelMultipleChoiceField(
        queryset=Magister.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        help_text="Selecciona los programas a los que tendrá acceso este usuario."
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'magisteres')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nombres'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Apellidos'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})


class CustomUserChangeForm(UserChangeForm):
    """
    Formulario para actualizar usuarios. Incluye todos los campos de usuario,
    pero reemplaza el campo de contraseña con el de contraseña admin deshabilitado.
    """
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'magisteres', 'active_magister')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        if 'magisteres' in self.fields:
            self.fields['magisteres'].widget.attrs.update({'class': 'form-control'})
        if 'active_magister' in self.fields:
            self.fields['active_magister'].widget.attrs.update({'class': 'form-control'})
            self.fields['active_magister'].queryset = Magister.objects.all()
            # Si el usuario ya tiene magisteres, filtrar el active_magister por esos magisteres
            if self.instance.pk and self.instance.magisteres.exists():
                self.fields['active_magister'].queryset = self.instance.magisteres.all()


class LoginForm(forms.Form):
    """
    Formulario de inicio de sesión personalizado con email
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )