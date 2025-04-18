from django.urls import path
from . import views

app_name = 'gspg'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Rutas para Intakes
    path('intakes/', views.intake_list, name='intake_list'),
    path('intakes/new/', views.intake_create, name='intake_create'),
    path('intakes/<int:pk>/edit/', views.intake_edit, name='intake_edit'),
    path('intakes/<int:pk>/delete/', views.intake_delete, name='intake_delete'),
    
    # Rutas para Estudiantes
    path('estudiantes/', views.estudiante_list, name='estudiante_list'),
    path('estudiantes/new/', views.estudiante_create, name='estudiante_create'),
    path('estudiantes/<int:pk>/edit/', views.estudiante_edit, name='estudiante_edit'),
    path('estudiantes/<int:pk>/delete/', views.estudiante_delete, name='estudiante_delete'),
    path('estudiantes/upload/', views.estudiante_bulk_upload, name='estudiante_bulk_upload'),
    path('estudiantes/export/excel/', views.estudiante_export_excel, name='estudiante_export_excel'),
    path('estudiantes/export/pdf/', views.estudiante_export_pdf, name='estudiante_export_pdf'),
    
    # Rutas para profesores
    path('profesores/', views.profesor_list, name='profesor_list'),
    path('profesores/new/', views.profesor_create, name='profesor_create'),
    path('profesores/<int:pk>/edit/', views.profesor_edit, name='profesor_edit'),
    path('profesores/<int:pk>/delete/', views.profesor_delete, name='profesor_delete'),
    
    # Rutas para grupos de trabajo
    path('grupos/', views.grupo_trabajo_list, name='grupo_trabajo_list'),
    path('grupos/new/', views.grupo_trabajo_create, name='grupo_trabajo_create'),
    path('grupos/<int:pk>/', views.grupo_trabajo_detail, name='grupo_trabajo_detail'),
    path('grupos/<int:pk>/edit/', views.grupo_trabajo_edit, name='grupo_trabajo_edit'),
    path('grupos/<int:pk>/delete/', views.grupo_trabajo_delete, name='grupo_trabajo_delete'),
    path('grupos/<int:pk>/finalizar/', views.grupo_trabajo_finalizar, name='grupo_trabajo_finalizar'),
    path('grupos/<int:pk>/add-estudiantes/', views.grupo_trabajo_add_estudiantes, name='grupo_trabajo_add_estudiantes'),
    path('grupos/<int:grupo_pk>/remove-estudiante/<int:estudiante_pk>/', views.grupo_trabajo_remove_estudiante, name='grupo_trabajo_remove_estudiante'),
    path('grupos/get-estudiantes/', views.get_estudiantes_por_intake, name='get_estudiantes_por_intake'),
    
    # Rutas para Reuniones
    path('grupos/<int:grupo_pk>/reuniones/', views.reunion_list, name='reunion_list'),
    path('grupos/<int:grupo_pk>/reuniones/new/', views.reunion_create, name='reunion_create'),
    path('reuniones/<int:reunion_pk>/edit/', views.reunion_edit, name='reunion_edit'),
    path('reuniones/<int:reunion_pk>/delete/', views.reunion_delete, name='reunion_delete'),
]