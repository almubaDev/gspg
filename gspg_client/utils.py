import unicodedata
from .models import Universidad

def normalizar_nombre(nombre):
    if not nombre:
        return ""
    # Eliminar tildes y pasar a mayúsculas
    nfkd_form = unicodedata.normalize('NFKD', nombre)
    sin_tildes = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return sin_tildes.upper().strip()

def obtener_configuracion_universidad(nombre_universidad):
    nombre_normalizado = normalizar_nombre(nombre_universidad)
    universidad = Universidad.objects.filter(nombre_normalizado=nombre_normalizado).first()
    if universidad:
        return {
            'logo_url': universidad.logo.url if universidad.logo else None,
            'color_primario': universidad.color_primario,
            'color_secundario': universidad.color_secundario,
        }
    return {
        'logo_url': None,
        'color_primario': '#1e40af',
        'color_secundario': '#3b82f6',
    }

def cargar_configuracion_universidad(request, universidad):
    config = obtener_configuracion_universidad(universidad)
    request.session["logo_url"] = config["logo_url"]
    request.session["color_primario"] = config["color_primario"]
    request.session["color_secundario"] = config["color_secundario"]