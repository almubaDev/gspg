from django.contrib import admin
from .models import Estudiante, Intake, Profesor, GrupoTrabajo, Persona, ReunionGrupo, Magister, AsistenciaReunion



@admin.register(Magister)
class MagisterAdmin(admin.ModelAdmin):
    list_display = ['name', 'faculty', 'university']
    search_fields = ['name', 'faculty', 'university']
    list_filter = ['university']

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_completo',
        'rut',
        'intake',
        'correo_institucional',
        'estado',
        'proceso_grado',
    ]
    list_filter = ['intake', 'estado', 'proceso_grado', 'intake__magister']
    search_fields = [
        'persona__nombre_completo',
        'persona__rut',
        'persona__correo_institucional',
        'persona__correo_personal',
    ]

    def rut(self, obj):
        return obj.persona.rut

    def nombre_completo(self, obj):
        return obj.persona.nombre_completo

    def correo_institucional(self, obj):
        return obj.persona.correo_institucional

    rut.admin_order_field = 'persona__rut'
    nombre_completo.admin_order_field = 'persona__nombre_completo'
    correo_institucional.admin_order_field = 'persona__correo_institucional'

@admin.register(Intake)
class IntakeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'magister']
    list_filter = ['magister']

@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rut', 'correo_institucional', 'telefono']
    search_fields = ['nombre', 'rut', 'correo_institucional']

@admin.register(GrupoTrabajo)
class GrupoTrabajoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'profesor', 'intake', 'finalizado']
    list_filter = ['intake__magister', 'finalizado']
    search_fields = ['nombre', 'profesor__nombre']

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ['rut', 'nombre_completo', 'correo_institucional', 'telefono']
    search_fields = ['rut', 'nombre_completo', 'correo_institucional']

class ReunionGrupoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora', 'link', 'comentarios')
    

@admin.register(AsistenciaReunion)
class AsistenciaReunionAdmin(admin.ModelAdmin):
    list_display = ['reunion', 'estudiante', 'asistio']
    list_filter = ['asistio', 'reunion']
    search_fields = ['reunion__grupo__nombre', 'estudiante__persona__nombre_completo']