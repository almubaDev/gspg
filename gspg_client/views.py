from django.shortcuts import render, redirect
from django.utils import timezone
from gspg.models import Profesor, Estudiante, ReunionGrupo
from .utils import obtener_configuracion_universidad


# 🔐 LOGIN
def login_view(request):
    error = None

    if request.method == 'POST':
        correo = request.POST.get('correo')
        rut = request.POST.get('rut')

        # Buscar profesor
        profesor = Profesor.objects.filter(correo_institucional=correo).first()
        if not profesor:
            profesor = Profesor.objects.filter(correo_personal=correo).first()

        if profesor and profesor.rut == rut:
            request.session['tipo'] = 'profesor'
            request.session['id'] = profesor.id

            uni_info = obtener_configuracion_universidad(profesor.magister.university)
            request.session['logo_url'] = uni_info['logo_url']
            request.session['color_primario'] = uni_info['color_primario']
            request.session['color_secundario'] = uni_info['color_secundario']

            return redirect('gspg_client:dashboard_profesor')

        # Buscar estudiante
        estudiante = Estudiante.objects.select_related('persona', 'intake__magister').filter(
            persona__correo_institucional=correo
        ).first()
        if not estudiante:
            estudiante = Estudiante.objects.select_related('persona', 'intake__magister').filter(
                persona__correo_personal=correo
            ).first()

        if estudiante and estudiante.persona.rut == rut:
            request.session['tipo'] = 'estudiante'
            request.session['id'] = estudiante.id

            uni_info = obtener_configuracion_universidad(estudiante.intake.magister.university)
            request.session['logo_url'] = uni_info['logo_url']
            request.session['color_primario'] = uni_info['color_primario']
            request.session['color_secundario'] = uni_info['color_secundario']

            return redirect('gspg_client:dashboard_estudiante')

        error = "Correo o RUT incorrecto."

    return render(request, 'gspg_client/login.html', {'error': error})



# 🔓 LOGOUT
def logout_view(request):
    request.session.flush()
    return redirect('gspg_client:login')


def dashboard_profesor(request):
    profesor_id = request.session.get('id')
    profesor = Profesor.objects.get(id=profesor_id)

    grupos = GrupoTrabajo.objects.filter(profesor=profesor)

    reuniones_proximas = ReunionGrupo.objects.filter(
        grupo__in=grupos,
        fecha__gte=timezone.now().date()
    ).order_by('fecha')[:5]

    context = {
        'profesor': profesor,
        'grupos': grupos,
        'reuniones_proximas': reuniones_proximas,
    }
    return render(request, 'gspg_client/dashboard_profesor.html', context)



def dashboard_estudiante(request):
    estudiante_id = request.session.get('id')
    estudiante = Estudiante.objects.select_related('intake', 'persona').get(id=estudiante_id)

    # Obtener grupo (asumimos relación directa)
    grupo = estudiante.grupo_trabajo

    # Reuniones futuras
    reuniones_proximas = ReunionGrupo.objects.filter(
        grupo=grupo,
        fecha__gte=timezone.now().date()
    ).order_by('fecha')[:5]

    context = {
        'estudiante': estudiante,
        'grupo': grupo,
        'reuniones_proximas': reuniones_proximas,
    }
    return render(request, 'gspg_client/dashboard_estudiante.html', context)
