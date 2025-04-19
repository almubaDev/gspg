from django.urls import path
from . import views

app_name = 'gspg_client'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard-profesor/', views.dashboard_profesor, name='dashboard_profesor'),
    path('dashboard-estudiante/', views.dashboard_estudiante, name='dashboard_estudiante'),
]
