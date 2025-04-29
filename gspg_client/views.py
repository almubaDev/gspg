from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.timezone import now
from django.contrib import messages
from django.utils.dateformat import DateFormat
from django.utils.formats import get_format
from gspg.models import (Estudiante, Profesor, ReunionGrupo, GrupoTrabajo, ActaReunion, 
                         AsistenciaReunion,ComentarioReunion)
from .forms import ActaReunionForm
import json


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
            
            # Inicializar configuración de universidad
            if estudiante.intake and estudiante.intake.magister and estudiante.intake.magister.university:
                from gspg_client.models import Universidad
                from gspg.context_processors import normalizar_nombre
                
                magister = estudiante.intake.magister
                nombre_normalizado = normalizar_nombre(magister.university)
                universidad = Universidad.objects.filter(nombre_normalizado=nombre_normalizado).first()
                
                if universidad:
                    request.session['color_primario'] = universidad.color_primario
                    request.session['color_secundario'] = universidad.color_secundario
                    request.session['logo_url'] = universidad.logo.url if universidad.logo else None
            
            return redirect("gspg_client:dashboard_estudiante")

        elif profesor:
            request.session["tipo"] = "profesor"
            request.session["id"] = profesor.id
            
            # Inicializar configuración de universidad
            # Intentamos obtener el magister del primer grupo del profesor
            grupo = profesor.grupos_trabajo.select_related('magister').first()
            if grupo and grupo.magister and grupo.magister.university:
                from gspg_client.models import Universidad
                from gspg.context_processors import normalizar_nombre
                
                magister = grupo.magister
                nombre_normalizado = normalizar_nombre(magister.university)
                universidad = Universidad.objects.filter(nombre_normalizado=nombre_normalizado).first()
                
                if universidad:
                    request.session['color_primario'] = universidad.color_primario
                    request.session['color_secundario'] = universidad.color_secundario
                    request.session['logo_url'] = universidad.logo.url if universidad.logo else None
            
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
    estudiante = Estudiante.objects.select_related('persona', 'intake__magister').get(id=estudiante_id)

    # Obtener los grupos del estudiante
    grupos = estudiante.grupos_trabajo.select_related('intake__magister').all()
    
    # Obtener la próxima reunión (la más cercana en el futuro)
    proxima_reunion = ReunionGrupo.objects.filter(
        grupo__in=grupos,
        fecha__gte=timezone.now().date()
    ).order_by('fecha', 'hora').first()
    
    # Contar reuniones pendientes (futuras)
    reuniones_pendientes = ReunionGrupo.objects.filter(
        grupo__in=grupos,
        fecha__gte=timezone.now().date()
    ).count()
    
    # Obtener asistencias del estudiante
    asistencias = AsistenciaReunion.objects.filter(
        estudiante=estudiante
    ).select_related('reunion__grupo').order_by('-reunion__fecha')
    
    # Calcular estadísticas de asistencia
    total_reuniones_pasadas = ReunionGrupo.objects.filter(
        grupo__in=grupos,
        fecha__lt=timezone.now().date()
    ).count()
    
    reuniones_asistidas = asistencias.filter(asistio=True).count()
    
    # Calcular porcentaje de asistencia
    porcentaje_asistencia = 0
    if total_reuniones_pasadas > 0:
        porcentaje_asistencia = int((reuniones_asistidas / total_reuniones_pasadas) * 100)
    
    # Obtener actas de reuniones
    actas = ActaReunion.objects.filter(
        reunion__grupo__in=grupos
    ).select_related('reunion', 'reunion__grupo').order_by('-fecha_subida')
    
    # Agrupar actas por grupo
    actas_por_grupo = {}
    for acta in actas:
        grupo_id = acta.reunion.grupo.id
        if grupo_id not in actas_por_grupo:
            actas_por_grupo[grupo_id] = []
        actas_por_grupo[grupo_id].append(acta)
    
    # Obtener el magíster del estudiante
    magister = estudiante.intake.magister if estudiante.intake else None

    context = {
        'estudiante': estudiante,
        'grupos': grupos,
        'proxima_reunion': proxima_reunion,
        'reuniones_pendientes': reuniones_pendientes,
        'reuniones_asistidas': reuniones_asistidas,
        'asistencias': asistencias,
        'porcentaje_asistencia': porcentaje_asistencia,
        'actas': actas,
        'actas_por_grupo': actas_por_grupo,
        'magister': magister,
    }
    return render(request, 'gspg_client/dashboard_estudiante.html', context)

def historial_asistencia(request):
    """
    Vista para mostrar el historial completo de asistencia de un estudiante
    """
    if request.session.get('tipo') != 'estudiante':
        return redirect('gspg_client:login')
        
    estudiante_id = request.session.get('id')
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    
    # Obtener todas las asistencias del estudiante
    asistencias = AsistenciaReunion.objects.filter(
        estudiante=estudiante
    ).select_related('reunion__grupo').order_by('-reunion__fecha')
    
    # Calcular estadísticas
    total_reuniones = asistencias.count()
    reuniones_asistidas = asistencias.filter(asistio=True).count()
    
    # Calcular porcentaje de asistencia
    porcentaje_asistencia = 0
    if total_reuniones > 0:
        porcentaje_asistencia = int((reuniones_asistidas / total_reuniones) * 100)
    
    context = {
        'estudiante': estudiante,
        'asistencias': asistencias,
        'total_reuniones': total_reuniones,
        'reuniones_asistidas': reuniones_asistidas,
        'porcentaje_asistencia': porcentaje_asistencia,
    }
    
    return render(request, 'gspg_client/historial_asistencia.html', context)

def actas_disponibles(request):
    """
    Vista para mostrar todas las actas disponibles para un estudiante
    """
    if request.session.get('tipo') != 'estudiante':
        return redirect('gspg_client:login')
        
    estudiante_id = request.session.get('id')
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    
    # Obtener los grupos del estudiante
    grupos = estudiante.grupos_trabajo.all()
    
    # Obtener todas las actas de reuniones de los grupos del estudiante
    actas = ActaReunion.objects.filter(
        reunion__grupo__in=grupos
    ).select_related('reunion', 'reunion__grupo').order_by('-fecha_subida')
    
    # Agrupar actas por grupo
    actas_por_grupo = {}
    for acta in actas:
        grupo_nombre = acta.reunion.grupo.nombre
        if grupo_nombre not in actas_por_grupo:
            actas_por_grupo[grupo_nombre] = []
        actas_por_grupo[grupo_nombre].append(acta)
    
    context = {
        'estudiante': estudiante,
        'actas': actas,
        'actas_por_grupo': actas_por_grupo,
        'grupos': grupos
    }
    
    return render(request, 'gspg_client/actas_disponibles.html', context)

def ver_grupo_estudiante(request, grupo_id):
    """
    Vista para que un estudiante vea detalles de un grupo específico
    """
    if request.session.get('tipo') != 'estudiante':
        return redirect('gspg_client:login')
        
    estudiante_id = request.session.get('id')
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    
    # Verificar que el estudiante pertenezca al grupo
    grupo = get_object_or_404(GrupoTrabajo, id=grupo_id, estudiantes=estudiante)
    
    # Obtener las reuniones del grupo
    reuniones = ReunionGrupo.objects.filter(grupo=grupo).order_by('-fecha', '-hora')
    reuniones_pasadas = reuniones.filter(fecha__lt=timezone.now().date())
    reuniones_futuras = reuniones.filter(fecha__gte=timezone.now().date())
    
    # Obtener la asistencia del estudiante a las reuniones de este grupo
    asistencias = AsistenciaReunion.objects.filter(
        estudiante=estudiante,
        reunion__grupo=grupo
    )
    
    # Crear un diccionario para facilitar el acceso a la asistencia por reunión
    asistencias_dict = {a.reunion_id: a.asistio for a in asistencias}
    
    # Obtener actas de reuniones de este grupo
    actas = ActaReunion.objects.filter(reunion__grupo=grupo).order_by('-fecha_subida')
    
    context = {
        'estudiante': estudiante,
        'grupo': grupo,
        'reuniones_pasadas': reuniones_pasadas,
        'reuniones_futuras': reuniones_futuras,
        'asistencias_dict': asistencias_dict,
        'actas': actas
    }
    
    return render(request, 'gspg_client/grupo_estudiante.html', context)


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


def crear_reunion_cliente(request, grupo_pk):
    """Vista para crear una reunión desde el cliente"""
    # Verificar que el usuario sea un profesor
    if request.session.get("tipo") != "profesor":
        return redirect("gspg_client:login")

    profesor_id = request.session.get("id")
    profesor = get_object_or_404(Profesor, id=profesor_id)
    grupo = get_object_or_404(GrupoTrabajo, pk=grupo_pk, profesor=profesor)

    # Procesar el formulario si es un POST
    if request.method == 'POST':
        fecha = request.POST.get("fecha")
        hora = request.POST.get("hora")
        
        if fecha and hora:
            try:
                # Crear la reunión con el modelo compartido
                reunion = ReunionGrupo.objects.create(
                    grupo=grupo,
                    fecha=fecha,
                    hora=hora,
                    # Campos opcionales
                    link="",
                    comentarios=""
                )
                messages.success(request, "Reunión programada exitosamente.")
                return redirect("gspg_client:gestion_grupo", grupo_id=grupo_pk)
            except Exception as e:
                messages.error(request, f"Error al programar la reunión: {str(e)}")
        else:
            messages.error(request, "Debe proporcionar fecha y hora para la reunión.")

    # Para GET, mostrar el formulario
    reuniones = ReunionGrupo.objects.filter(grupo=grupo)
    fechas_ocupadas = list(reuniones.values_list('fecha', flat=True))
    fechas_ocupadas_str = [df.strftime('%Y-%m-%d') for df in fechas_ocupadas]

    context = {
        'grupo': grupo,
        'fechas_ocupadas_json': json.dumps(fechas_ocupadas_str)
    }
    return render(request, 'gspg_client/crear_reunion.html', context)


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



def actualizar_link_reunion(request, reunion_id):
    reunion = get_object_or_404(ReunionGrupo, id=reunion_id)

    if request.method == "POST":
        link = request.POST.get("link", "").strip()
        reunion.link = link
        reunion.save()
    return redirect("gspg_client:reunion_detalle", reunion_id=reunion.id)


def subir_acta(request, reunion_id):
    reunion = get_object_or_404(ReunionGrupo, id=reunion_id)

    # Subida de nueva acta
    if request.method == 'POST':
        form = ActaReunionForm(request.POST, request.FILES)
        if form.is_valid():
            acta = form.save(commit=False)
            acta.reunion = reunion
            acta.save()
            messages.success(request, "Acta subida correctamente.")
            return redirect('gspg_client:subir_acta', reunion_id=reunion.id)
        else:
            messages.error(request, "Error al subir el acta.")
    else:
        form = ActaReunionForm()

    actas = ActaReunion.objects.filter(reunion=reunion).order_by('-fecha_subida')

    return render(request, 'gspg_client/subir_acta_reunion.html', {
        'form': form,
        'reunion': reunion,
        'actas': actas
    })
    
    
def registrar_asistencia(request, reunion_id):
    reunion = get_object_or_404(ReunionGrupo, id=reunion_id)
    estudiantes = reunion.grupo.estudiantes.all()

    if request.method == 'POST':
        for estudiante in estudiantes:
            valor = request.POST.get(f"asistencia_{estudiante.id}")
            asistio = True if valor == "True" else False

            # Debug en consola
            print(f"[DEBUG] Estudiante {estudiante.id} - Valor POST: {valor} - asistio: {asistio}")

            AsistenciaReunion.objects.update_or_create(
                reunion=reunion,
                estudiante=estudiante,
                defaults={'asistio': asistio}
            )

        return redirect('gspg_client:reunion_detalle', reunion_id=reunion.id)

    # Mostrar asistencias actuales
    asistencias = {
        asistencia.estudiante.id: asistencia.asistio
        for asistencia in AsistenciaReunion.objects.filter(reunion=reunion)
    }

    context = {
        'reunion': reunion,
        'estudiantes': estudiantes,
        'asistencias': asistencias,
    }
    return render(request, 'gspg_client/registrar_asistencia.html', context)




def comentarios_reunion(request, reunion_id):
    reunion = get_object_or_404(ReunionGrupo, id=reunion_id)
    persona = get_persona_sesion(request)  # profesor o estudiante

    if request.method == 'POST':
        contenido = request.POST.get('comentario', '').strip()
        if contenido:
            ComentarioReunion.objects.create(
                reunion=reunion,
                autor=persona,
                contenido=contenido
            )
        return redirect('gspg_client:comentarios_reunion', reunion_id=reunion.id)

    comentarios = reunion.comentarioreunion_set.select_related('autor').order_by('creado_en')

    return render(request, 'gspg_client/comentarios_reunion.html', {
        'reunion': reunion,
        'comentarios': comentarios,
        'persona': persona,
    })


def get_persona_sesion(request):
    """
    Obtiene el objeto Persona (Profesor o Estudiante) basado en la sesión actual.
    """
    tipo = request.session.get('tipo')
    usuario_id = request.session.get('id')
    
    if tipo == 'profesor':
        return get_object_or_404(Profesor, id=usuario_id)
    elif tipo == 'estudiante':
        estudiante = get_object_or_404(Estudiante, id=usuario_id)
        return estudiante.persona
    else:
        return None
    
    
def comentarios_reunion(request, reunion_id):
    reunion = get_object_or_404(ReunionGrupo, id=reunion_id)
    tipo_usuario = request.session.get('tipo')
    usuario_id = request.session.get('id')
    
    # Obtener el autor según el tipo de usuario
    autor_persona = None
    autor_profesor = None
    if tipo_usuario == 'estudiante':
        estudiante = get_object_or_404(Estudiante, id=usuario_id)
        autor_persona = estudiante.persona
    elif tipo_usuario == 'profesor':
        autor_profesor = get_object_or_404(Profesor, id=usuario_id)

    if request.method == 'POST':
        contenido = request.POST.get('comentario', '').strip()
        if contenido:
            # Crear el comentario con el autor correcto
            ComentarioReunion.objects.create(
                reunion=reunion,
                autor_persona=autor_persona,
                autor_profesor=autor_profesor,
                contenido=contenido
            )
        return redirect('gspg_client:comentarios_reunion', reunion_id=reunion.id)

    # Obtener los comentarios de la reunión
    comentarios = ComentarioReunion.objects.filter(reunion=reunion).order_by('creado_en')

    return render(request, 'gspg_client/comentarios_reunion.html', {
        'reunion': reunion,
        'comentarios': comentarios,
        'es_profesor': tipo_usuario == 'profesor',
        'autor_persona': autor_persona,
        'autor_profesor': autor_profesor,
    })