from django.urls import path
from . import views

app_name = 'gspg_client'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard-profesor/', views.dashboard_profesor, name='dashboard_profesor'),
    path('dashboard-estudiante/', views.dashboard_estudiante, name='dashboard_estudiante'),
    path("grupo/<int:grupo_id>/", views.gestion_grupo, name="gestion_grupo"),
    path('reunion/<int:reunion_id>/', views.reunion_detalle, name='reunion_detalle'),
    path("reunion/<int:reunion_id>/subir-acta/", views.subir_acta, name="subir_acta"),
    

]
