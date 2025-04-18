from django.contrib import admin
from .models import Magister, Intake, Estudiante, Profesor, GrupoTrabajo, ReunionGrupo

@admin.register(Magister)
class MagisterAdmin(admin.ModelAdmin):
    list_display = ['name', 'faculty', 'university']
    search_fields = ['name', 'faculty', 'university']
    list_filter = ['university', 'faculty']

@admin.register(Intake)
class IntakeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'magister', 'year', 'month', 'section']
    list_filter = ['magister', 'year', 'month']
    search_fields = ['magister__name', 'year']

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'rut', 'intake', 'correo_institucional', 'estado', 'proceso_grado']
    list_filter = ['intake', 'estado', 'proceso_grado', 'intake__magister']
    search_fields = ['nombre_completo', 'rut', 'correo_institucional', 'correo_personal']

@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rut', 'correo_institucional', 'telefono']
    search_fields = ['nombre', 'rut', 'correo_institucional', 'correo_personal']
    filter_horizontal = ['magisteres']
    
@admin.register(GrupoTrabajo)
class GrupoTrabajoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'profesor', 'magister', 'fecha_inicio', 'fecha_fin', 'finalizado']
    list_filter = ['magister', 'finalizado', 'fecha_inicio']
    search_fields = ['nombre', 'profesor__nombre', 'estudiantes__nombre_completo']
    filter_horizontal = ['estudiantes']
    
@admin.register(ReunionGrupo)
class ReunionGrupoAdmin(admin.ModelAdmin):
    list_display = ['grupo', 'fecha', 'hora', 'estado', 'link_reunion']
    list_filter = ['estado', 'fecha', 'grupo__magister']
    search_fields = ['grupo__nombre', 'comentario']
    date_hierarchy = 'fecha'