from django.contrib import admin
from .models import Universidad

@admin.register(Universidad)
class UniversidadAdmin(admin.ModelAdmin):
    list_display = ('nombre_normalizado', 'color_primario', 'color_secundario')
    search_fields = ('nombre_normalizado',)
