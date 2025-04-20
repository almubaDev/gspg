from django import forms
from django.db.models import Q
from django.core.validators import FileExtensionValidator
from .models import (Intake, Magister, Persona ,Estudiante, Profesor, GrupoTrabajo, 
                     ReunionGrupo, AsistenciaReunion, ActaReunion
)
import pandas as pd
import openpyxl

class IntakeForm(forms.ModelForm):
    class Meta:
        model = Intake
        fields = ['month', 'year', 'section', 'magister']
        widgets = {
            'month': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'magister': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Si se proporciona un usuario, filtrar los magísteres disponibles
        if user and hasattr(user, 'active_magister') and user.active_magister:
            self.fields['magister'].queryset = Magister.objects.filter(id=user.active_magister.id)
            self.fields['magister'].initial = user.active_magister
            self.fields['magister'].widget.attrs['disabled'] = True
            self.fields['magister'].required = False  # Para que pase la validación de formulario aunque esté deshabilitado
        
        # Si es una edición y ya tiene un magister asignado, bloquear el campo
        elif self.instance and self.instance.pk and self.instance.magister:
            self.fields['magister'].widget.attrs['disabled'] = True
            self.fields['magister'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        # Si el campo de magister está deshabilitado, recuperamos el valor del instance o del user
        if 'magister' not in cleaned_data or not cleaned_data['magister']:
            if self.instance and self.instance.pk and self.instance.magister:
                cleaned_data['magister'] = self.instance.magister
            elif hasattr(self, 'user') and self.user and hasattr(self.user, 'active_magister') and self.user.active_magister:
                cleaned_data['magister'] = self.user.active_magister
        return cleaned_data


class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = [
            'rut',
            'nombre_completo',
            'telefono',
            'correo_institucional',
            'correo_personal'
        ]
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_institucional': forms.EmailInput(attrs={'class': 'form-control'}),
            'correo_personal': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class EstudianteForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
       super().__init__(*args, **kwargs)
       if user and hasattr(user, 'active_magister') and user.active_magister:
           self.fields['intake'].queryset = Intake.objects.filter(magister=user.active_magister)  # Corregido

    class Meta:
        model = Estudiante
        fields = ['intake', 'estado', 'proceso_grado']
        widgets = {
            'intake': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'proceso_grado': forms.Select(attrs={'class': 'form-control'}),
        }


class EstudianteCompletoForm(forms.Form):
    rut = forms.CharField(label="RUT", widget=forms.TextInput(attrs={'class': 'form-control'}))
    nombre_completo = forms.CharField(label="Nombre Completo", widget=forms.TextInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(label="Teléfono", widget=forms.TextInput(attrs={'class': 'form-control'}))
    correo_institucional = forms.EmailField(label="Correo Institucional", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    correo_personal = forms.EmailField(label="Correo Personal", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    intake = forms.ModelChoiceField(queryset=Intake.objects.none(), label="Intake", widget=forms.Select(attrs={'class': 'form-control'}))
    estado = forms.ChoiceField(choices=Estudiante._meta.get_field('estado').choices, widget=forms.Select(attrs={'class': 'form-control'}))
    proceso_grado = forms.ChoiceField(choices=Estudiante._meta.get_field('proceso_grado').choices, widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'active_magister') and user.active_magister:
            self.fields['intake'].queryset = Intake.objects.filter(magister=user.active_magister)


class EstudianteBulkUploadForm(forms.Form):
    intake = forms.ModelChoiceField(queryset=Intake.objects.all(), label="Intake")
    archivo_excel = forms.FileField(label="Archivo Excel", validators=[
        FileExtensionValidator(allowed_extensions=['xls', 'xlsx'])
    ])

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'active_magister') and user.active_magister:
            self.fields['intake'].queryset = Intake.objects.filter(magister=user.active_magister)

    def clean_archivo_excel(self):
        archivo = self.cleaned_data['archivo_excel']
        try:
            df = pd.read_excel(archivo)
        except Exception:
            raise ValidationError("El archivo no es un Excel válido.")

        columnas_requeridas = [
            'rut', 'nombre_completo', 'telefono',
            'correo_institucional', 'correo_personal',
            'estado', 'proceso_grado'
        ]
        for col in columnas_requeridas:
            if col not in df.columns:
                raise ValidationError(f"Falta la columna obligatoria: {col}")

        self.cleaned_data['df'] = df
        return archivo

class ProfesorForm(forms.ModelForm):
    class Meta:
        model = Profesor
        fields = ['rut', 'nombre', 'correo_institucional', 'correo_personal', 'telefono']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sin puntos ni guión'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_institucional': forms.EmailInput(attrs={'class': 'form-control'}),
            'correo_personal': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }
        

class GrupoTrabajoForm(forms.ModelForm):
    class Meta:
        model = GrupoTrabajo
        fields = ['nombre', 'profesor', 'intake', 'estudiantes', 'fecha_inicio', 'fecha_fin', 'observaciones']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'profesor': forms.Select(attrs={'class': 'form-control', 'id': 'id_profesor'}),
            'intake': forms.Select(attrs={'class': 'form-control', 'id': 'id_intake'}),
            'estudiantes': forms.SelectMultiple(attrs={'class': 'form-control', 'id': 'id_estudiantes'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Formatear fechas para HTML5 date input (YYYY-MM-DD)
        if self.instance and self.instance.pk:
            if self.instance.fecha_inicio:
                self.initial['fecha_inicio'] = self.instance.fecha_inicio.strftime('%Y-%m-%d')
            if self.instance.fecha_fin:
                self.initial['fecha_fin'] = self.instance.fecha_fin.strftime('%Y-%m-%d')
        
        # Guardar el usuario para usarlo en clean()
        self.user = user
        
        # Si se proporciona un usuario con magister activo, filtrar por su magíster
        if user and hasattr(user, 'active_magister') and user.active_magister:
            self.fields['profesor'].queryset = Profesor.objects.filter(magisteres=user.active_magister)
            self.fields['intake'].queryset = Intake.objects.filter(magister=user.active_magister)
            
            # Para edición
            if self.instance and self.instance.pk:
                self.fields['intake'].widget.attrs['disabled'] = True
                self.fields['intake'].required = False
                
                # Importante: NO pre-cargamos estudiantes aquí, lo hará el JavaScript
                # Simplemente indicamos un queryset vacío para evitar duplicación
                self.fields['estudiantes'].queryset = Estudiante.objects.none()
            else:
                # Para creación, deshabilitamos estudiantes hasta que seleccionen intake
                self.fields['estudiantes'].widget.attrs['disabled'] = True
                self.fields['estudiantes'].required = False
                self.fields['estudiantes'].help_text = "Primero selecciona un intake para ver los estudiantes disponibles."
                
            # Si el grupo está finalizado, no permitir cambios
            if self.instance and self.instance.pk and self.instance.finalizado:
                for field_name in self.fields:
                    self.fields[field_name].widget.attrs['disabled'] = True
                    self.fields[field_name].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Si el intake está deshabilitado, recuperar su valor del instance
        if 'intake' not in cleaned_data or not cleaned_data['intake']:
            if self.instance and self.instance.pk and self.instance.intake:
                cleaned_data['intake'] = self.instance.intake
        
        # Si el magister no está especificado, usar el magister activo del usuario
        if 'magister' not in cleaned_data or not cleaned_data.get('magister'):
            if hasattr(self, 'user') and self.user and hasattr(self.user, 'active_magister') and self.user.active_magister:
                cleaned_data['magister'] = self.user.active_magister
        
        # Validar que la fecha de finalización sea posterior a la de inicio
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            self.add_error('fecha_fin', "La fecha de finalización debe ser posterior a la fecha de inicio.")
        
        return cleaned_data

class EstudianteAddForm(forms.Form):
    estudiantes = forms.ModelMultipleChoiceField(
        queryset=Estudiante.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=True
    )
    
    def __init__(self, *args, user=None, grupo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'active_magister') and user.active_magister and grupo:
            # Filtrar estudiantes del mismo magíster que no están ya en este grupo
            self.fields['estudiantes'].queryset = Estudiante.objects.filter(
                intake__magister=user.active_magister,
                proceso_grado='pendiente'
            ).exclude(
                pk__in=grupo.estudiantes.all()
            )
            
            


class ReunionGrupoForm(forms.ModelForm):
    class Meta:
        model = ReunionGrupo
        fields = ['fecha', 'hora', 'link', 'comentarios', 'archivo_adjunto']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
            'link': forms.URLInput(attrs={'placeholder': 'https://...'}),
            'comentarios': forms.Textarea(attrs={'rows': 3}),
        }


class AsistenciaReunionForm(forms.ModelForm):
    class Meta:
        model = AsistenciaReunion
        fields = ['asistio', 'comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={'rows': 2}),
        }
        
        


class ActaReunionForm(forms.ModelForm):
    class Meta:
        model = ActaReunion
        fields = ['archivo']
        widgets = {
            'archivo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
            }),
        }
