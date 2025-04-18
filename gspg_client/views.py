from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.timezone import now
from django.contrib import messages
from gspg.models import Estudiante, Profesor, ReunionGrupo, GrupoTrabajo, ActaReunion
from .forms import ActaReunionForm




# -----------------------------
# LOGIN VIEW (BASADO EN SESIÓN SIMPLE)
# -----------------------------

from django.shortcuts import render, redirect
from django.contrib import messages
from gspg.models import Estudiante, Profesor

def login_view(request):
    if request.method == "POST":
        correo = request.POST.get("email") or ""
        rut = request.POST.get("rut") or ""

        # Buscar estudiante
        estudiante = Estudiante.objects.filter(
            persona__correo_institucional__iexact=correo.strip(),
            persona__rut__iexact=rut.strip()
        ).first()

        # Buscar profesor
        profesor = Profesor.objects.filter(
            correo_institucional__iexact=correo.strip(),
            rut__iexact=rut.strip()
        ).first()

        if estudiante:
            request.session["tipo"] = "estudiante"
            request.session["id"] = estudiante.id
            return redirect("gspg_client:dashboard_estudiante")

        elif profesor:
            request.session["tipo"] = "profesor"
            request.session["id"] = profesor.id
            return redirect("gspg_client:dashboard_profesor")

        else:
            messages.error(request, "Correo o RUT incorrecto.")

    return render(request, "gspg_client/login.html")

# -----------------------------
# LOGOUT VIEW (BORRAR SESIÓN)
# -----------------------------

def logout_view(request):
    request.session.flush()
    return redirect('gspg_client:login')


# -----------------------------
# DASHBOARD ESTUDIANTE
# -----------------------------
def dashboard_estudiante(request):
    if request.session.get('tipo') != 'estudiante':
        return redirect('gspg_client:login')

    estudiante_id = request.session.get('id')
    estudiante = Estudiante.objects.select_related('persona').get(id=estudiante_id)

    grupos = estudiante.grupos_trabajo.select_related('intake__magister').all()
    reuniones_proximas = ReunionGrupo.objects.filter(
        grupo__in=grupos,
        fecha__gte=timezone.now().date()
    ).order_by('fecha')[:5]

    # Asumimos que todos los grupos del estudiante son del mismo magíster
    magister = grupos[0].intake.magister if grupos else None

    context = {
        'estudiante': estudiante,
        'grupos': grupos,
        'reuniones_proximas': reuniones_proximas,
        'magister': magister,
    }
    return render(request, 'gspg_client/dashboard_estudiante.html', context)


# -----------------------------
# DASHBOARD PROFESOR
# -----------------------------

def dashboard_profesor(request):
    if request.session.get("tipo") != "profesor":
        return redirect("gspg_client:login")

    profesor_id = request.session.get("id")
    profesor = get_object_or_404(Profesor, id=profesor_id)

    # Obtener grupos del profesor
    grupos = profesor.grupos_trabajo.select_related("intake", "magister").all()

    # Obtener magíster activo del primer grupo (asumimos uno principal)
    magister = grupos.first().magister if grupos.exists() else None

    # Obtener la reunión más próxima asociada a alguno de sus grupos
    reuniones = ReunionGrupo.objects.filter(grupo__in=grupos, fecha__gte=now()).order_by("fecha", "hora")
    proxima_reunion = reuniones.first() if reuniones.exists() else None

    context = {
        "profesor": profesor,
        "grupos": grupos,
        "magister": magister,
        "proxima_reunion": proxima_reunion,
    }

    return render(request, "gspg_client/dashboard_profesor.html", context)




# -----------------------------
# Gestion de gurpos
# -----------------------------

def gestion_grupo(request, grupo_id):
    if request.session.get("tipo") != "profesor":
        return redirect("gspg_client:login")

    profesor_id = request.session.get("id")
    profesor = get_object_or_404(Profesor, id=profesor_id)
    grupo = get_object_or_404(GrupoTrabajo, id=grupo_id, profesor=profesor)

    reuniones = ReunionGrupo.objects.filter(grupo=grupo).order_by("-fecha", "-hora")

    return render(request, "gspg_client/gestion_grupo.html", {
        "profesor": profesor,
        "grupo": grupo,
        "reuniones": reuniones,
    })


def reunion_detalle(request, reunion_id):
    if request.session.get('tipo') not in ['profesor', 'estudiante']:
        return redirect('gspg_client:login')

    reunion = get_object_or_404(
        ReunionGrupo.objects.select_related('grupo__intake__magister'),
        id=reunion_id
    )

    grupo = reunion.grupo
    intake = grupo.intake
    magister = intake.magister
    usuario_tipo = request.session.get('tipo')

    context = {
        'reunion': reunion,
        'grupo': grupo,
        'intake': intake,
        'magister': magister,
        'usuario_tipo': usuario_tipo,
    }
    return render(request, 'gspg_client/reunion_detalle.html', context)


def subir_acta(request, reunion_id):
    reunion = get_object_or_404(ReunionGrupo, id=reunion_id)

    if request.method == "POST":
        form = ActaReunionForm(request.POST, request.FILES)
        if form.is_valid():
            acta = form.save(commit=False)
            acta.reunion = reunion
            acta.subido_por = request.user.profesor if hasattr(request.user, "profesor") else None
            acta.save()
            messages.success(request, "Acta subida correctamente.")
            return redirect("gspg_client:gestion_grupo", grupo_id=reunion.grupo.id)
    else:
        form = ActaReunionForm()

    return render(request, "gspg_client/subir_acta_reunion.html", {
        "reunion": reunion,
        "form": form,
    })

