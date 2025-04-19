import unicodedata
from gspg_client.models import Universidad  # ← modelo que creaste en la PWA

def normalizar_nombre(nombre):
    if not nombre:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', nombre)
    sin_tildes = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return sin_tildes.upper().strip()

def user_magister_context(request):
    """
    Añade el magíster activo, la lista de magísteres y el logo de la universidad asociada.
    """
    context = {}

    if request.user.is_authenticated:
        active_magister = getattr(request.user, 'active_magister', None)
        context['user_magister'] = active_magister
        context['magisteres_asignados'] = getattr(request.user, 'magisteres', []).all()


        if active_magister and active_magister.university:
            nombre_normalizado = normalizar_nombre(active_magister.university)
            universidad = Universidad.objects.filter(nombre_normalizado=nombre_normalizado).first()
            if universidad and universidad.logo:
                context['logo_url_universidad'] = universidad.logo.url
            else:
                context['logo_url_universidad'] = None

    return context
