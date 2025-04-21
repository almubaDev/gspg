from django.urls import path
from . import views

app_name = 'gspg_client'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard-profesor/', views.dashboard_profesor, name='dashboard_profesor'),
    path('dashboard-estudiante/', views.dashboard_estudiante, name='dashboard_estudiante'),
    path("grupo/<int:grupo_id>/", views.gestion_grupo, name="gestion_grupo"),
    path('grupo/<int:grupo_pk>/crear-reunion/', views.crear_reunion_cliente, name='crear_reunion_cliente'),
    path('reunion/<int:reunion_id>/', views.reunion_detalle, name='reunion_detalle'),
    path('reunion/<int:reunion_id>/actualizar-link/', views.actualizar_link_reunion, name='actualizar_link_reunion'),
    path('reunion/<int:reunion_id>/subir-acta/', views.subir_acta, name='subir_acta'),
    path('reunion/<int:reunion_id>/confirmar-asistencia/', views.registrar_asistencia, name='registrar_asistencia'),
    path('reunion/<int:reunion_id>/comentarios/', views.comentarios_reunion, name='comentarios_reunion'),



    

]
