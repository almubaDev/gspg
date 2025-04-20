import unicodedata
from gspg_client.models import Universidad

def normalizar_nombre(nombre):
    if not nombre:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', nombre)
    sin_tildes = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return sin_tildes.upper().strip()

def user_magister_context(request):
    context = {}

    if request.user.is_authenticated:
        active_magister = getattr(request.user, 'active_magister', None)
        context['user_magister'] = active_magister
        context['magisteres_asignados'] = getattr(request.user, 'magisteres', []).all()

        if active_magister and active_magister.university:
            nombre_normalizado = normalizar_nombre(active_magister.university)
            universidad = Universidad.objects.filter(nombre_normalizado=nombre_normalizado).first()

            if universidad:
                # Guardar en sesión para gspg_client
                request.session['color_primario'] = universidad.color_primario
                request.session['color_secundario'] = universidad.color_secundario
                request.session['logo_url'] = universidad.logo.url if universidad.logo else None

                # También lo devolvemos en el context (por compatibilidad con gspg)
                context['logo_url_universidad'] = universidad.logo.url if universidad.logo else None
            else:
                request.session['color_primario'] = '#1e40af'
                request.session['color_secundario'] = '#3b82f6'
                request.session['logo_url'] = None
                context['logo_url_universidad'] = None

    return context
