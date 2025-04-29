from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import pandas as pd
import xlsxwriter
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from .models import Intake, Estudiante, Persona, Profesor, GrupoTrabajo, ReunionGrupo, AsistenciaReunion, ActaReunion
from .forms import (IntakeForm, PersonaForm, EstudianteForm, EstudianteCompletoForm, EstudianteBulkUploadForm, ProfesorForm, 
                    GrupoTrabajoForm, EstudianteAddForm, ReunionGrupoForm, AsistenciaReunionForm, ActaReunionForm)

@login_required
def dashboard(request):
    """Vista principal del dashboard"""
    # Mostrar solo los intakes del magister activo del usuario
    user_magister = None
    if hasattr(request.user, 'active_magister'):
        user_magister = request.user.active_magister
    
    context = {
        'page_title': 'Dashboard',
        'user_magister': request.user.active_magister,
        'user_magisteres': request.user.magisteres.all()
    }
    # Si el usuario tiene un magister activo, añadir los intakes disponibles
    if user_magister:
        intakes = Intake.objects.filter(magister=user_magister)
        context['intakes'] = intakes
    # Si no tiene magister activo pero sí tiene magisteres asignados
    elif hasattr(request.user, 'magisteres') and request.user.magisteres.exists():
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno de tus programas.")
        
    return render(request, 'gspg/dashboard.html', context)

@login_required
def intake_list(request):
    """Lista de Intakes"""
    # Solo mostrar intakes relacionados con el magister activo del usuario
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    intakes = Intake.objects.filter(magister=request.user.active_magister)
    
    context = {
        'page_title': 'Intakes',
        'intakes': intakes,
    }
    return render(request, 'gspg/intake_list.html', context)

@login_required
def intake_create(request):
    """Crear nuevo Intake"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    if request.method == 'POST':
        form = IntakeForm(request.POST, user=request.user)
        
        if form.is_valid():
            # Asegurarse de que el magister sea el del usuario actual
            intake = form.save(commit=False)
            intake.magister = request.user.active_magister
            
            try:
                intake.save()
                messages.success(request, "Intake creado exitosamente.")
                return redirect('gspg:intake_list')
            except Exception as e:
                messages.error(request, f"Error al crear el intake: {str(e)}")
    else:
        form = IntakeForm(user=request.user)
    
    context = {
        'page_title': 'Nuevo Intake',
        'form': form,
    }
    return render(request, 'gspg/intake_form.html', context)

@login_required
def intake_edit(request, pk):
    """Editar Intake existente"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el intake y verificar que pertenezca al magister activo del usuario
    intake = get_object_or_404(Intake, pk=pk, magister=request.user.active_magister)
    
    if request.method == 'POST':
        form = IntakeForm(request.POST, instance=intake, user=request.user)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Intake actualizado exitosamente.")
                return redirect('gspg:intake_list')
            except Exception as e:
                messages.error(request, f"Error al actualizar el intake: {str(e)}")
    else:
        form = IntakeForm(instance=intake, user=request.user)
    
    context = {
        'page_title': 'Editar Intake',
        'form': form,
        'intake': intake,
    }
    return render(request, 'gspg/intake_form.html', context)

@login_required
def intake_delete(request, pk):
    """Eliminar Intake"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el intake y verificar que pertenezca al magister activo del usuario
    intake = get_object_or_404(Intake, pk=pk, magister=request.user.active_magister)
    
    if request.method == 'POST':
        try:
            intake.delete()
            messages.success(request, "Intake eliminado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al eliminar el intake: {str(e)}")
        return redirect('gspg:intake_list')
    
    context = {
        'page_title': 'Eliminar Intake',
        'intake': intake,
    }
    return render(request, 'gspg/intake_confirm_delete.html', context)

@login_required
def estudiante_list(request):
    """Lista de Estudiantes"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Filtro por intake, estado y proceso de grado
    intake_id = request.GET.get('intake', '')
    estado = request.GET.get('estado', '')
    proceso_grado = request.GET.get('proceso_grado', '')  # Nuevo filtro
    search = request.GET.get('search', '')
    
    # Obtener estudiantes del magíster activo del usuario con select_related para evitar consultas N+1
    estudiantes = Estudiante.objects.select_related('persona', 'intake').filter(intake__magister=request.user.active_magister)
    
    # Aplicar filtros adicionales
    if intake_id:
        estudiantes = estudiantes.filter(intake_id=intake_id)
    if estado:
        estudiantes = estudiantes.filter(estado=estado)
    if proceso_grado:  # Aplicar el nuevo filtro
        estudiantes = estudiantes.filter(proceso_grado=proceso_grado)
    if search:
        estudiantes = estudiantes.filter(
            Q(persona__nombre_completo__icontains=search) | 
            Q(persona__rut__icontains=search) | 
            Q(persona__correo_institucional__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(estudiantes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener intakes para el filtro
    intakes = Intake.objects.filter(magister=request.user.active_magister)
    
    context = {
        'page_title': 'Estudiantes',
        'page_obj': page_obj,
        'intakes': intakes,
        'estados': Estudiante._meta.get_field('estado').choices,
        'procesos_grado': Estudiante._meta.get_field('proceso_grado').choices,
        'selected_intake': intake_id,
        'selected_estado': estado,
        'selected_proceso_grado': proceso_grado,  # Para mantener selección
        'search': search,
    }
    return render(request, 'gspg/estudiante_list.html', context)

@login_required
def estudiante_create(request):
    if not request.user.active_magister:
        messages.error(request, "Debe seleccionar un programa activo.")
        return redirect("gspg:dashboard")

    if request.method == "POST":
        form = EstudianteCompletoForm(request.POST, user=request.user)
        if form.is_valid():
            rut = form.cleaned_data['rut']

            # Buscar o crear Persona
            persona, creada = Persona.objects.get_or_create(
                rut=rut,
                defaults={
                    'nombre_completo': form.cleaned_data['nombre_completo'],
                    'telefono': form.cleaned_data['telefono'],
                    'correo_institucional': form.cleaned_data['correo_institucional'],
                    'correo_personal': form.cleaned_data['correo_personal'],
                }
            )

            if not creada:
                persona.nombre_completo = form.cleaned_data['nombre_completo']
                persona.telefono = form.cleaned_data['telefono']
                persona.correo_institucional = form.cleaned_data['correo_institucional']
                persona.correo_personal = form.cleaned_data['correo_personal']
                persona.save()

            # Validar duplicado por persona + intake
            if Estudiante.objects.filter(persona=persona, intake=form.cleaned_data['intake']).exists():
                messages.warning(request, "Este estudiante ya está registrado en ese intake.")
                return redirect("gspg:estudiante_list")

            # Crear Estudiante
            Estudiante.objects.create(
                persona=persona,
                intake=form.cleaned_data['intake'],
                estado=form.cleaned_data['estado'],
                proceso_grado=form.cleaned_data['proceso_grado'],
            )

            messages.success(request, "Estudiante registrado correctamente.")
            return redirect("gspg:estudiante_list")
    else:
        form = EstudianteCompletoForm(user=request.user)

    return render(request, "gspg/estudiante_form.html", {
        "form": form,
        "titulo": "Nuevo Estudiante",
        "modo_creacion": True,
    })

@login_required
def estudiante_edit(request, pk):
    """Editar Estudiante existente"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el estudiante y verificar que pertenezca al magister activo del usuario
    estudiante = get_object_or_404(Estudiante.objects.select_related('persona'), pk=pk, intake__magister=request.user.active_magister)
    
    if request.method == 'POST':
        # Crear formulario para EstudianteCompletoForm que maneja tanto datos de persona como estudiante
        form = EstudianteCompletoForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                # Verificar que el intake pertenezca al magíster activo del usuario
                intake = form.cleaned_data['intake']
                if intake.magister != request.user.active_magister:
                    messages.error(request, "El intake seleccionado no pertenece a tu programa activo.")
                    return redirect('gspg:estudiante_list')
                
                # Actualizar datos de persona
                persona = estudiante.persona
                persona.rut = form.cleaned_data['rut']
                persona.nombre_completo = form.cleaned_data['nombre_completo']
                persona.telefono = form.cleaned_data['telefono']
                persona.correo_institucional = form.cleaned_data['correo_institucional']
                persona.correo_personal = form.cleaned_data['correo_personal']
                persona.save()
                
                # Actualizar datos del estudiante
                estudiante.intake = intake
                estudiante.estado = form.cleaned_data['estado']
                estudiante.proceso_grado = form.cleaned_data['proceso_grado']
                estudiante.save()
                
                messages.success(request, "Estudiante actualizado exitosamente.")
                return redirect('gspg:estudiante_list')
            except Exception as e:
                messages.error(request, f"Error al actualizar el estudiante: {str(e)}")
    else:
        # Inicializar el formulario con datos combinados
        initial_data = {
            'rut': estudiante.persona.rut,
            'nombre_completo': estudiante.persona.nombre_completo,
            'telefono': estudiante.persona.telefono,
            'correo_institucional': estudiante.persona.correo_institucional,
            'correo_personal': estudiante.persona.correo_personal,
            'intake': estudiante.intake,
            'estado': estudiante.estado,
            'proceso_grado': estudiante.proceso_grado,
        }
        form = EstudianteCompletoForm(initial=initial_data, user=request.user)
    
    context = {
        'page_title': 'Editar Estudiante',
        'form': form,
        'estudiante': estudiante,
        'titulo': 'Editar Estudiante',
        'modo_creacion': False,
    }
    return render(request, 'gspg/estudiante_form.html', context)

@login_required
def estudiante_delete(request, pk):
    """Eliminar Estudiante"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el estudiante y verificar que pertenezca al magister activo del usuario
    estudiante = get_object_or_404(Estudiante.objects.select_related('persona'), pk=pk, intake__magister=request.user.active_magister)
    
    if request.method == 'POST':
        try:
            # Nota: dependiendo de la configuración on_delete, puede que necesitemos manejar
            # la eliminación de la persona asociada si no tiene más estudiantes
            persona = estudiante.persona
            estudiante.delete()
            
            # Comprobar si la persona tiene más estudiantes asociados
            if not persona.estudiantes.exists():
                persona.delete()
                messages.info(request, "También se eliminó el registro de persona ya que no tenía más estudiantes asociados.")
            
            messages.success(request, "Estudiante eliminado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al eliminar el estudiante: {str(e)}")
        return redirect('gspg:estudiante_list')
    
    context = {
        'page_title': 'Eliminar Estudiante',
        'estudiante': estudiante,
    }
    return render(request, 'gspg/estudiante_confirm_delete.html', context)

@login_required
def estudiante_bulk_upload(request):
    """Carga masiva de estudiantes desde Excel"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    if request.method == 'POST':
        form = EstudianteBulkUploadForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            try:
                intake = form.cleaned_data['intake']
                
                # Verificar que el intake pertenezca al magíster activo del usuario
                if intake.magister != request.user.active_magister:
                    messages.error(request, "El intake seleccionado no pertenece a tu programa activo.")
                    return redirect('gspg:estudiante_list')
                
                # Procesar el DataFrame
                df = form.cleaned_data['df']
                
                # Estadísticas
                total = len(df)
                created = 0
                updated = 0
                errors = []
                
                # Procesar cada fila
                for index, row in df.iterrows():
                    try:
                        # Valores predeterminados para columnas opcionales
                        telefono = row.get('telefono', '')
                        correo_personal = row.get('correo_personal', '')
                        estado = row.get('estado', 'activo')
                        proceso_grado = row.get('proceso_grado', 'pendiente')
                        
                        # Validar estado
                        if estado not in dict(Estudiante.ESTADO_CHOICES):
                            estado = 'activo'
                        
                        # Validar proceso_grado
                        if proceso_grado not in dict(Estudiante.PROCESO_GRADO_CHOICES):
                            proceso_grado = 'pendiente'
                        
                        # Buscar o crear Persona primero
                        persona, created_persona = Persona.objects.get_or_create(
                            rut=row['rut'],
                            defaults={
                                'nombre_completo': row['nombre_completo'],
                                'telefono': telefono,
                                'correo_institucional': row['correo_institucional'],
                                'correo_personal': correo_personal,
                            }
                        )
                        
                        # Si la persona ya existía, actualizar sus datos
                        if not created_persona:
                            persona.nombre_completo = row['nombre_completo']
                            persona.telefono = telefono
                            persona.correo_institucional = row['correo_institucional']
                            persona.correo_personal = correo_personal
                            persona.save()
                        
                        # Buscar si el estudiante ya existe para esta persona e intake
                        estudiante, created_flag = Estudiante.objects.update_or_create(
                            persona=persona,
                            intake=intake,
                            defaults={
                                'estado': estado,
                                'proceso_grado': proceso_grado
                            }
                        )
                        
                        if created_flag:
                            created += 1
                        else:
                            updated += 1
                            
                    except Exception as e:
                        errors.append(f"Fila {index+2}: {str(e)}")
                
                # Mensaje de resultado
                if errors:
                    messages.warning(
                        request, 
                        f"Proceso completado con {len(errors)} errores. {created} creados, {updated} actualizados."
                    )
                    for error in errors[:10]:  # Mostrar los primeros 10 errores
                        messages.error(request, error)
                    if len(errors) > 10:
                        messages.error(request, f"... y {len(errors) - 10} errores más.")
                else:
                    messages.success(
                        request, 
                        f"Proceso completado exitosamente. {created} estudiantes creados, {updated} actualizados."
                    )
                
                return redirect('gspg:estudiante_list')
                
            except Exception as e:
                messages.error(request, f"Error al procesar el archivo: {str(e)}")
    else:
        form = EstudianteBulkUploadForm(user=request.user)
    
    context = {
        'page_title': 'Carga Masiva de Estudiantes',
        'form': form,
    }
    return render(request, 'gspg/estudiante_bulk_upload.html', context)

@login_required
def estudiante_export_excel(request):
    """Exportar estudiantes a Excel"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Filtros (los mismos que en la lista)
    intake_id = request.GET.get('intake', '')
    estado = request.GET.get('estado', '')
    proceso_grado = request.GET.get('proceso_grado', '')
    search = request.GET.get('search', '')
    
    # Obtener estudiantes del magíster activo del usuario con select_related para optimizar
    estudiantes = Estudiante.objects.select_related('persona', 'intake').filter(intake__magister=request.user.active_magister)
    
    # Aplicar filtros adicionales
    if intake_id:
        estudiantes = estudiantes.filter(intake_id=intake_id)
    if estado:
        estudiantes = estudiantes.filter(estado=estado)
    if proceso_grado:
        estudiantes = estudiantes.filter(proceso_grado=proceso_grado)
    if search:
        estudiantes = estudiantes.filter(
            Q(persona__nombre_completo__icontains=search) | 
            Q(persona__rut__icontains=search) | 
            Q(persona__correo_institucional__icontains=search)
        )
    
    # Crear un buffer en memoria
    output = BytesIO()
    
    # Crear un libro de trabajo y una hoja
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Estudiantes')
    
    # Formatos
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#16325B',
        'font_color': 'white',
        'border': 1
    })
    
    row_format = workbook.add_format({
        'border': 1
    })
    
    # Encabezados
    headers = ['RUT', 'Nombre Completo', 'Teléfono', 'Correo Institucional', 
               'Correo Personal', 'Estado', 'Proceso de Grado', 'Intake', 'Fecha Registro']
    
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)
    
    # Datos
    for row_num, estudiante in enumerate(estudiantes, 1):
        worksheet.write(row_num, 0, estudiante.persona.rut, row_format)
        worksheet.write(row_num, 1, estudiante.persona.nombre_completo, row_format)
        worksheet.write(row_num, 2, estudiante.persona.telefono, row_format)
        worksheet.write(row_num, 3, estudiante.persona.correo_institucional, row_format)
        worksheet.write(row_num, 4, estudiante.persona.correo_personal, row_format)
        worksheet.write(row_num, 5, dict(Estudiante.ESTADO_CHOICES)[estudiante.estado], row_format)
        worksheet.write(row_num, 6, dict(Estudiante.PROCESO_GRADO_CHOICES)[estudiante.proceso_grado], row_format)
        worksheet.write(row_num, 7, str(estudiante.intake), row_format)
        worksheet.write(row_num, 8, estudiante.fecha_registro.strftime('%d/%m/%Y %H:%M'), row_format)
    
    # Ajustar anchos de columna
    for i, header in enumerate(headers):
        worksheet.set_column(i, i, len(header) + 5)
    
    # Cerrar el libro
    workbook.close()
    
    # Preparar la respuesta
    output.seek(0)
    
    # Crear nombre de archivo con filtros aplicados
    filename = "Estudiantes"
    if intake_id:
        intake = Intake.objects.get(pk=intake_id)
        filename += f"_{intake.get_short_name()}"
    if estado:
        filename += f"_{dict(Estudiante.ESTADO_CHOICES)[estado]}"
    if proceso_grado:
        filename += f"_{dict(Estudiante.PROCESO_GRADO_CHOICES)[proceso_grado]}"
    filename += ".xlsx"
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def estudiante_export_pdf(request):
    """Exportar estudiantes a PDF"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Filtros (los mismos que en la lista)
    intake_id = request.GET.get('intake', '')
    estado = request.GET.get('estado', '')
    search = request.GET.get('search', '')
    
    # Obtener estudiantes del magíster activo del usuario con select_related
    estudiantes = Estudiante.objects.select_related('persona', 'intake').filter(intake__magister=request.user.active_magister)
    
    # Aplicar filtros adicionales
    if intake_id:
        estudiantes = estudiantes.filter(intake_id=intake_id)
        intake_name = Intake.objects.get(pk=intake_id).get_short_name()
    else:
        intake_name = "Todos"
    
    if estado:
        estudiantes = estudiantes.filter(estado=estado)
        estado_name = dict(Estudiante.ESTADO_CHOICES)[estado]
    else:
        estado_name = "Todos"
        
    if search:
        estudiantes = estudiantes.filter(
            Q(persona__nombre_completo__icontains=search) | 
            Q(persona__rut__icontains=search) | 
            Q(persona__correo_institucional__icontains=search)
        )
    
    # Crear un buffer en memoria
    buffer = BytesIO()
    
    # Crear el PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Título
    title = f"Lista de Estudiantes - {request.user.active_magister.name}"
    
    # Datos para la tabla
    data = [['RUT', 'Nombre', 'Correo', 'Estado', 'Proceso Grado', 'Intake']]
    
    for e in estudiantes:
        data.append([
            e.persona.rut,
            e.persona.nombre_completo,
            e.persona.correo_institucional,
            dict(Estudiante.ESTADO_CHOICES)[e.estado],
            dict(Estudiante.PROCESO_GRADO_CHOICES)[e.proceso_grado],
            e.intake.get_short_name()
        ])
    
    # Crear tabla
    table = Table(data)
    
    # Estilo de tabla
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16325B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ])
    
    # Aplicar estilo
    table.setStyle(style)
    
    # Añadir tabla al documento
    elements.append(table)
    
    # Construir PDF
    doc.build(elements)
    
    # Preparar la respuesta
    buffer.seek(0)
    
    # Crear nombre de archivo con filtros aplicados
    filename = "Estudiantes"
    if intake_id:
        filename += f"_{intake_name}"
    if estado:
        filename += f"_{estado_name}"
    filename += ".pdf"
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# Vistas para Profesores
# Vistas para Profesores
@login_required
def profesor_list(request):
    """Lista de Profesores"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Buscar profesores relacionados con el magíster activo del usuario
    profesores = Profesor.objects.filter(magisteres=request.user.active_magister)
    
    # Búsqueda por texto
    search = request.GET.get('search', '')
    if search:
        profesores = profesores.filter(
            Q(nombre__icontains=search) | 
            Q(rut__icontains=search) |
            Q(correo_institucional__icontains=search) |
            Q(correo_personal__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(profesores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Profesores',
        'page_obj': page_obj,
        'search': search,
    }
    return render(request, 'gspg/profesor_list.html', context)

@login_required
def profesor_create(request):
    """Crear nuevo Profesor o asociarlo al magíster actual"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    if request.method == 'POST':
        form = ProfesorForm(request.POST)
        
        if form.is_valid():
            rut = form.cleaned_data.get('rut')
            
            # Comprobar si ya existe un profesor con este RUT
            profesor_existente = None
            try:
                profesor_existente = Profesor.objects.get(rut=rut)
            except Profesor.DoesNotExist:
                pass
            
            if profesor_existente:
                # Si el profesor ya existe, simplemente añadir el magíster actual
                if request.user.active_magister not in profesor_existente.magisteres.all():
                    profesor_existente.magisteres.add(request.user.active_magister)
                    messages.success(request, f"El profesor {profesor_existente.nombre} ha sido asociado a tu programa.")
                else:
                    messages.info(request, f"El profesor {profesor_existente.nombre} ya estaba asociado a tu programa.")
                
                return redirect('gspg:profesor_list')
            else:
                # Crear nuevo profesor
                profesor = form.save()
                
                try:
                    # Asociar al magíster actual
                    profesor.magisteres.add(request.user.active_magister)
                    
                    messages.success(request, "Profesor creado y asociado a tu programa exitosamente.")
                    return redirect('gspg:profesor_list')
                except Exception as e:
                    messages.error(request, f"Error al crear el profesor: {str(e)}")
    else:
        form = ProfesorForm()
    
    context = {
        'page_title': 'Nuevo Profesor',
        'form': form,
    }
    return render(request, 'gspg/profesor_form.html', context)

@login_required
def profesor_edit(request, pk):
    """Editar Profesor existente"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el profesor y verificar que pertenezca al magister activo del usuario
    profesor = get_object_or_404(Profesor, pk=pk, magisteres=request.user.active_magister)
    
    if request.method == 'POST':
        form = ProfesorForm(request.POST, instance=profesor)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Profesor actualizado exitosamente.")
                return redirect('gspg:profesor_list')
            except Exception as e:
                messages.error(request, f"Error al actualizar el profesor: {str(e)}")
    else:
        form = ProfesorForm(instance=profesor)
    
    context = {
        'page_title': 'Editar Profesor',
        'form': form,
        'profesor': profesor,
    }
    return render(request, 'gspg/profesor_form.html', context)

@login_required
def profesor_delete(request, pk):
    """Desasociar Profesor del magíster actual"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el profesor y verificar que pertenezca al magister activo del usuario
    profesor = get_object_or_404(Profesor, pk=pk, magisteres=request.user.active_magister)
    
    if request.method == 'POST':
        try:
            # No eliminamos el profesor, solo lo desasociamos del magíster actual
            profesor.magisteres.remove(request.user.active_magister)
            messages.success(request, f"El profesor {profesor.nombre} ha sido desasociado de tu programa.")
            
            # Si el profesor ya no está asociado a ningún magíster, lo eliminamos
            if profesor.magisteres.count() == 0:
                profesor.delete()
                messages.info(request, f"El profesor {profesor.nombre} ha sido eliminado porque no estaba asociado a ningún otro programa.")
                
            return redirect('gspg:profesor_list')
        except Exception as e:
            messages.error(request, f"Error al desasociar el profesor: {str(e)}")
            return redirect('gspg:profesor_list')
    
    context = {
        'page_title': 'Desasociar Profesor',
        'profesor': profesor,
    }
    return render(request, 'gspg/profesor_confirm_delete.html', context)

@login_required
def get_estudiantes_por_intake(request):
    """Vista AJAX para obtener estudiantes disponibles por intake"""
    print("=== INICIANDO get_estudiantes_por_intake ===")
    
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        print("Error: Usuario sin programa activo")
        return JsonResponse({'error': 'No tienes un programa activo'}, status=400)
    
    intake_id = request.GET.get('intake_id')
    grupo_id = request.GET.get('grupo_id')
    
    print(f"Parámetros recibidos: intake_id={intake_id}, grupo_id={grupo_id}")
    
    if not intake_id:
        print("Error: No se proporcionó un intake_id")
        return JsonResponse({'error': 'No se proporcionó un intake'}, status=400)
    
    try:
        # Verificar que el intake pertenezca al magíster activo del usuario
        intake = Intake.objects.get(pk=intake_id)
        
        print(f"Intake encontrado: {intake} (ID: {intake.id})")
        print(f"Magíster del intake: {intake.magister.name} (ID: {intake.magister.id})")
        print(f"Magíster activo del usuario: {request.user.active_magister.name} (ID: {request.user.active_magister.id})")
        
        if intake.magister != request.user.active_magister:
            print("Error: El intake no pertenece al programa activo del usuario")
            return JsonResponse({'error': 'El intake no pertenece a tu programa activo'}, status=403)
        
        # Estudiantes que pertenecen a este intake específico (con select_related)
        todos_estudiantes = Estudiante.objects.select_related('persona').filter(intake=intake)
        print(f"Total estudiantes en el intake: {todos_estudiantes.count()}")
        
        # Mostrar todos los estudiantes para depuración
        for i, e in enumerate(todos_estudiantes):
            print(f"Estudiante {i+1}: {e.persona.nombre_completo} ({e.persona.rut}) - Proceso: {e.proceso_grado}")
            grupos = e.grupos_trabajo.all()
            if grupos:
                print(f"  En grupos: {', '.join([g.nombre for g in grupos])}")
            else:
                print("  No está en ningún grupo")
        
        # Consulta base: estudiantes del intake especificado con proceso pendiente
        query = Q(intake=intake, proceso_grado='pendiente')
        
        # Si estamos editando un grupo, incluir sus estudiantes actuales sin importar su estado
        if grupo_id:
            try:
                grupo = GrupoTrabajo.objects.get(pk=grupo_id)
                print(f"Grupo encontrado: {grupo.nombre} (ID: {grupo.id})")
                
                # Estudiantes actuales del grupo
                estudiantes_grupo = grupo.estudiantes.all()
                print(f"Estudiantes actuales en el grupo: {estudiantes_grupo.count()}")
                
                # Mostrar estudiantes del grupo
                for i, e in enumerate(estudiantes_grupo):
                    print(f"Estudiante del grupo {i+1}: {e.persona.nombre_completo} ({e.persona.rut})")
                
                # Modificar la consulta para incluir a los estudiantes del grupo actual
                query |= Q(grupos_trabajo=grupo)
            except GrupoTrabajo.DoesNotExist:
                print(f"Error: No se encontró el grupo con ID {grupo_id}")
        
        # Estudiantes disponibles (pendientes o ya en este grupo)
        estudiantes_disponibles = Estudiante.objects.select_related('persona').filter(query).distinct()
        
        # Ahora excluir estudiantes que ya están en otros grupos (excepto los del grupo actual)
        if grupo_id:
            estudiantes_en_otros_grupos = Estudiante.objects.filter(
                intake=intake,
                grupos_trabajo__isnull=False
            ).exclude(grupos_trabajo__id=grupo_id).distinct()
            
            print(f"Estudiantes en otros grupos: {estudiantes_en_otros_grupos.count()}")
            estudiantes_disponibles = estudiantes_disponibles.exclude(pk__in=estudiantes_en_otros_grupos)
        else:
            # Si no estamos editando, excluir todos los que ya están en cualquier grupo
            estudiantes_disponibles = estudiantes_disponibles.filter(grupos_trabajo__isnull=True)
        
        print(f"Estudiantes disponibles final: {estudiantes_disponibles.count()}")
        
        # Crear la lista de estudiantes para el resultado JSON
        estudiantes_data = []
        for e in estudiantes_disponibles:
            print(f"Añadiendo a resultado: {e.persona.nombre_completo} ({e.persona.rut})")
            estudiantes_data.append({
                'id': e.id,
                'text': f"{e.persona.nombre_completo} ({e.persona.rut})"
            })
        
        print(f"Total estudiantes en respuesta JSON: {len(estudiantes_data)}")
        return JsonResponse({'estudiantes': estudiantes_data})
    
    except Intake.DoesNotExist:
        print(f"Error: No se encontró el intake con ID {intake_id}")
        return JsonResponse({'error': f'No se encontró el intake con ID {intake_id}'}, status=404)
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def grupo_trabajo_list(request):
    """Lista de Grupos de Trabajo"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Filtros
    profesor_id = request.GET.get('profesor', '')
    finalizado = request.GET.get('finalizado', '')
    search = request.GET.get('search', '')
    
    # Obtener grupos de trabajo del magíster activo del usuario
    grupos = GrupoTrabajo.objects.filter(magister=request.user.active_magister)
    
    # Aplicar filtros adicionales
    if profesor_id:
        grupos = grupos.filter(profesor_id=profesor_id)
    if finalizado:
        grupos = grupos.filter(finalizado=(finalizado == 'true'))
    if search:
        # Actualizado para buscar por campos de persona
        grupos = grupos.filter(
            Q(nombre__icontains=search) | 
            Q(profesor__nombre__icontains=search) |
            Q(estudiantes__persona__nombre_completo__icontains=search)
        ).distinct()
    
    # Paginación
    paginator = Paginator(grupos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener profesores para el filtro
    profesores = Profesor.objects.filter(magisteres=request.user.active_magister)
    
    context = {
        'page_title': 'Grupos de Trabajo',
        'page_obj': page_obj,
        'profesores': profesores,
        'selected_profesor': profesor_id,
        'selected_finalizado': finalizado,
        'search': search,
    }
    return render(request, 'gspg/grupo_trabajo_list.html', context)

@login_required
def grupo_trabajo_create(request):
    """Crear nuevo Grupo de Trabajo"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    if request.method == 'POST':
        # Verificar integridad de datos en POST antes de procesar
        print("POST data:", request.POST)
        print("Estudiantes en POST:", request.POST.getlist('estudiantes'))
        
        form = GrupoTrabajoForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                # Verificar que el profesor pertenezca al magíster activo del usuario
                profesor = form.cleaned_data['profesor']
                if request.user.active_magister not in profesor.magisteres.all():
                    messages.error(request, "El profesor seleccionado no pertenece a tu programa activo.")
                    return redirect('gspg:grupo_trabajo_list')
                
                # Verificar que el intake pertenezca al magíster activo del usuario
                intake = form.cleaned_data['intake']
                if intake.magister != request.user.active_magister:
                    messages.error(request, "El intake seleccionado no pertenece a tu programa activo.")
                    return redirect('gspg:grupo_trabajo_list')
                
                # Verificar que los estudiantes pertenezcan al intake seleccionado
                estudiantes = form.cleaned_data.get('estudiantes', [])
                for estudiante in estudiantes:
                    if estudiante.intake != intake:
                        messages.error(request, f"El estudiante {estudiante.persona.nombre_completo} no pertenece al intake seleccionado.")
                        return redirect('gspg:grupo_trabajo_list')
                
                # Crear el grupo de trabajo
                grupo = form.save(commit=False)
                grupo.magister = request.user.active_magister
                grupo.save()
                
                # Guardar relaciones ManyToMany - esto añade los estudiantes
                form.save_m2m()
                
                # Actualizar el estado de proceso de grado de los estudiantes
                if estudiantes:
                    for estudiante in estudiantes:
                        estudiante.proceso_grado = 'proceso'
                        estudiante.save()
                
                messages.success(request, "Grupo de trabajo creado exitosamente.")
                return redirect('gspg:grupo_trabajo_list')
            except Exception as e:
                print(f"Error detallado: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"Error al crear el grupo de trabajo: {str(e)}")
        else:
            print("Form errors:", form.errors)
            # Intento de recuperación si el formulario es inválido pero hay datos suficientes
            if 'nombre' in request.POST and request.POST.get('profesor') and request.POST.get('intake') and request.POST.getlist('estudiantes'):
                try:
                    # Obtener datos necesarios
                    intake = Intake.objects.get(id=request.POST.get('intake'))
                    profesor = Profesor.objects.get(id=request.POST.get('profesor'))
                    estudiante_ids = request.POST.getlist('estudiantes')
                    
                    # Crear grupo manualmente
                    grupo = GrupoTrabajo(
                        nombre=request.POST.get('nombre'),
                        profesor=profesor,
                        intake=intake,
                        fecha_inicio=request.POST.get('fecha_inicio'),
                        fecha_fin=request.POST.get('fecha_fin'),
                        observaciones=request.POST.get('observaciones', ''),
                        magister=request.user.active_magister
                    )
                    grupo.save()
                    
                    # Añadir estudiantes
                    estudiantes = Estudiante.objects.filter(id__in=estudiante_ids)
                    grupo.estudiantes.set(estudiantes)
                    
                    # Actualizar estado de estudiantes
                    for estudiante in estudiantes:
                        estudiante.proceso_grado = 'proceso'
                        estudiante.save()
                    
                    messages.success(request, "Grupo de trabajo creado manualmente con éxito.")
                    return redirect('gspg:grupo_trabajo_list')
                except Exception as e:
                    print(f"Error en recuperación manual: {str(e)}")
                    messages.error(request, f"No se pudo crear manualmente: {str(e)}")
    else:
        form = GrupoTrabajoForm(user=request.user)
    
    context = {
        'page_title': 'Nuevo Grupo de Trabajo',
        'form': form,
    }
    return render(request, 'gspg/grupo_trabajo_form.html', context)


@login_required
def grupo_trabajo_edit(request, pk):
    """Editar Grupo de Trabajo existente"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister activo del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=pk, magister=request.user.active_magister)
    
    # Si el grupo está finalizado, no permitir edición
    if grupo.finalizado:
        messages.warning(request, "No se puede editar un grupo con proceso finalizado.")
        return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
    
    if request.method == 'POST':
        # Verificar integridad de datos en POST antes de procesar
        print("POST data:", request.POST)
        print("Estudiantes en POST:", request.POST.getlist('estudiantes'))
        
        form = GrupoTrabajoForm(request.POST, instance=grupo, user=request.user)
        
        if form.is_valid():
            try:
                # Verificar que el profesor pertenezca al magíster activo del usuario
                profesor = form.cleaned_data['profesor']
                if request.user.active_magister not in profesor.magisteres.all():
                    messages.error(request, "El profesor seleccionado no pertenece a tu programa activo.")
                    return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
                
                # Verificar que los estudiantes pertenezcan al magíster activo del usuario
                estudiantes = form.cleaned_data.get('estudiantes', [])
                for estudiante in estudiantes:
                    if estudiante.intake.magister != request.user.active_magister:
                        messages.error(request, f"El estudiante {estudiante.persona.nombre_completo} no pertenece a tu programa activo.")
                        return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
                
                # Obtener estudiantes antes de la actualización
                estudiantes_antiguos = set(grupo.estudiantes.all())
                
                # Guardar cambios
                form.save()
                
                # Obtener estudiantes después de la actualización
                estudiantes_nuevos = set(estudiantes)
                
                # Estudiantes que se quitaron
                estudiantes_eliminados = estudiantes_antiguos - estudiantes_nuevos
                for estudiante in estudiantes_eliminados:
                    estudiante.proceso_grado = 'pendiente'
                    estudiante.save()
                
                # Estudiantes que se añadieron
                estudiantes_agregados = estudiantes_nuevos - estudiantes_antiguos
                for estudiante in estudiantes_agregados:
                    estudiante.proceso_grado = 'proceso'
                    estudiante.save()
                
                messages.success(request, "Grupo de trabajo actualizado exitosamente.")
                return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
            except Exception as e:
                print(f"Error detallado: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"Error al actualizar el grupo de trabajo: {str(e)}")
        else:
            print("Form errors:", form.errors)
            # Intento de recuperación si el formulario es inválido pero hay datos suficientes
            if request.POST.get('nombre') and request.POST.get('profesor') and request.POST.getlist('estudiantes'):
                try:
                    # Obtener datos necesarios
                    profesor = Profesor.objects.get(id=request.POST.get('profesor'))
                    estudiante_ids = request.POST.getlist('estudiantes')
                    
                    # Actualizar campos básicos
                    grupo.nombre = request.POST.get('nombre')
                    grupo.profesor = profesor
                    grupo.fecha_inicio = request.POST.get('fecha_inicio')
                    grupo.fecha_fin = request.POST.get('fecha_fin')
                    grupo.observaciones = request.POST.get('observaciones', '')
                    grupo.save()
                    
                    # Obtener estudiantes anteriores
                    estudiantes_antiguos = set(grupo.estudiantes.all())
                    
                    # Actualizar estudiantes
                    estudiantes_nuevos = Estudiante.objects.filter(id__in=estudiante_ids)
                    grupo.estudiantes.set(estudiantes_nuevos)
                    
                    # Estudiantes que se quitaron
                    estudiantes_eliminados = estudiantes_antiguos - set(estudiantes_nuevos)
                    for estudiante in estudiantes_eliminados:
                        estudiante.proceso_grado = 'pendiente'
                        estudiante.save()
                    
                    # Estudiantes que se añadieron
                    estudiantes_agregados = set(estudiantes_nuevos) - estudiantes_antiguos
                    for estudiante in estudiantes_agregados:
                        estudiante.proceso_grado = 'proceso'
                        estudiante.save()
                    
                    messages.success(request, "Grupo de trabajo actualizado manualmente con éxito.")
                    return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
                except Exception as e:
                    print(f"Error en recuperación manual: {str(e)}")
                    messages.error(request, f"No se pudo actualizar manualmente: {str(e)}")
    else:
        form = GrupoTrabajoForm(instance=grupo, user=request.user)
    
    context = {
        'page_title': 'Editar Grupo de Trabajo',
        'form': form,
        'grupo': grupo,
    }
    return render(request, 'gspg/grupo_trabajo_form.html', context)

def grupo_trabajo_detail(request, pk):
    """Ver detalles de un Grupo de Trabajo"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister activo del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=pk, magister=request.user.active_magister)
    
    # Verificar si el proceso puede ser finalizado (fecha actual >= fecha fin)
    from datetime import date
    puede_finalizar = not grupo.finalizado and date.today() >= grupo.fecha_fin
    
    # Calcular estadísticas de asistencia
    estadisticas_asistencia = calcular_estadisticas_asistencia(grupo)
    
    context = {
        'page_title': 'Detalle de Grupo de Trabajo',
        'grupo': grupo,
        'puede_finalizar': puede_finalizar,
        'estadisticas_asistencia': estadisticas_asistencia,
    }
    return render(request, 'gspg/grupo_trabajo_detail.html', context)

@login_required
def grupo_trabajo_delete(request, pk):
    """Eliminar Grupo de Trabajo"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister activo del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=pk, magister=request.user.active_magister)
    
    if request.method == 'POST':
        try:
            # Actualizar el estado de proceso de grado de los estudiantes
            grupo.estudiantes.all().update(proceso_grado='pendiente')
            
            # Eliminar el grupo
            grupo.delete()
            messages.success(request, "Grupo de trabajo eliminado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al eliminar el grupo de trabajo: {str(e)}")
        return redirect('gspg:grupo_trabajo_list')
    
    context = {
        'page_title': 'Eliminar Grupo de Trabajo',
        'grupo': grupo,
    }
    return render(request, 'gspg/grupo_trabajo_confirm_delete.html', context)

@login_required
def grupo_trabajo_finalizar(request, pk):
    """Finalizar proceso de grado para un grupo"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister activo del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=pk, magister=request.user.active_magister)
    
    # Verificar si el proceso puede ser finalizado (fecha actual >= fecha fin)
    from datetime import date
    if grupo.finalizado:
        messages.warning(request, "El proceso ya ha sido finalizado.")
        return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
    
    if date.today() < grupo.fecha_fin:
        messages.warning(request, "Aún no se ha alcanzado la fecha de finalización.")
        return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
    
    if request.method == 'POST':
        try:
            # Finalizar el proceso
            grupo.finalizar_proceso()
            messages.success(request, "Proceso de grado finalizado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al finalizar el proceso: {str(e)}")
        return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
    
    context = {
        'page_title': 'Finalizar Proceso de Grado',
        'grupo': grupo,
    }
    return render(request, 'gspg/grupo_trabajo_confirm_finalizar.html', context)

@login_required
def grupo_trabajo_add_estudiantes(request, pk):
    """Añadir estudiantes a un grupo existente"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister activo del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=pk, magister=request.user.active_magister)
    
    # Si el grupo está finalizado, no permitir añadir estudiantes
    if grupo.finalizado:
        messages.warning(request, "No se pueden añadir estudiantes a un grupo con proceso finalizado.")
        return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
    
    if request.method == 'POST':
        form = EstudianteAddForm(request.POST, user=request.user, grupo=grupo)
        
        if form.is_valid():
            try:
                estudiantes = form.cleaned_data['estudiantes']
                
                # Añadir los estudiantes al grupo
                for estudiante in estudiantes:
                    grupo.estudiantes.add(estudiante)
                
                # Actualizar estado de proceso de grado
                estudiantes.update(proceso_grado='proceso')
                
                messages.success(request, f"Se han añadido {estudiantes.count()} estudiantes al grupo.")
                return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
            except Exception as e:
                messages.error(request, f"Error al añadir estudiantes: {str(e)}")
    else:
        form = EstudianteAddForm(user=request.user, grupo=grupo)
    
    context = {
        'page_title': 'Añadir Estudiantes al Grupo',
        'form': form,
        'grupo': grupo,
    }
    return render(request, 'gspg/grupo_trabajo_add_estudiantes.html', context)

@login_required
def grupo_trabajo_remove_estudiante(request, grupo_pk, estudiante_pk):
    """Eliminar un estudiante de un grupo"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister activo del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=grupo_pk, magister=request.user.active_magister)
    
    # Si el grupo está finalizado, no permitir eliminar estudiantes
    if grupo.finalizado:
        messages.warning(request, "No se pueden eliminar estudiantes de un grupo con proceso finalizado.")
        return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
    
    # Obtener el estudiante y verificar que pertenezca al grupo
    estudiante = get_object_or_404(Estudiante.objects.select_related('persona'), pk=estudiante_pk, grupos_trabajo=grupo)
    
    if request.method == 'POST':
        try:
            # Eliminar estudiante del grupo
            grupo.estudiantes.remove(estudiante)
            
            # Actualizar estado de proceso de grado
            estudiante.proceso_grado = 'pendiente'
            estudiante.save()
            
            messages.success(request, f"El estudiante {estudiante.persona.nombre_completo} ha sido eliminado del grupo.")
        except Exception as e:
            messages.error(request, f"Error al eliminar el estudiante: {str(e)}")
        return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
    
    context = {
        'page_title': 'Eliminar Estudiante del Grupo',
        'grupo': grupo,
        'estudiante': estudiante,
    }
    return render(request, 'gspg/grupo_trabajo_remove_estudiante.html', context)

@login_required
def reunion_list(request, grupo_pk):
    """Lista de Reuniones de un Grupo"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister activo del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=grupo_pk, magister=request.user.active_magister)
    
    # Obtener las reuniones del grupo
    reuniones = ReunionGrupo.objects.filter(grupo=grupo)
    
    # Filtrar reuniones pasadas y futuras
    from datetime import date
    hoy = date.today()
    reuniones_pasadas = reuniones.filter(fecha__lt=hoy).order_by('-fecha', '-hora')
    reuniones_futuras = reuniones.filter(fecha__gte=hoy).order_by('fecha', 'hora')
    
    # Obtener todas las actas para el modal
    from django.db.models import Prefetch
    reuniones_con_actas = ReunionGrupo.objects.filter(
        grupo=grupo, 
        actas__isnull=False
    ).prefetch_related(
        'actas', 'actas__subido_por'
    ).distinct()
    
    context = {
        'page_title': f'Reuniones - {grupo.nombre}',
        'grupo': grupo,
        'reuniones_futuras': reuniones_futuras,
        'reuniones_pasadas': reuniones_pasadas,
        'reuniones_con_actas': reuniones_con_actas,
    }
    return render(request, 'gspg/reunion_list.html', context)

@login_required
def reunion_create(request, grupo_pk):
    """Crear nueva Reunión para un Grupo"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    grupo = get_object_or_404(GrupoTrabajo, pk=grupo_pk, magister=request.user.active_magister)
    
    if grupo.finalizado:
        messages.warning(request, "No se pueden crear reuniones para un grupo finalizado.")
        return redirect('gspg:reunion_list', grupo_pk=grupo.pk)
    
    if request.method == 'POST':
        form = ReunionGrupoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                reunion = form.save(commit=False)
                reunion.grupo = grupo
                reunion.estado = 'programada'
                reunion.save()
                messages.success(request, "Reunión creada exitosamente.")
                return redirect('gspg:reunion_list', grupo_pk=grupo.pk)
            except Exception as e:
                messages.error(request, f"Error al crear la reunión: {str(e)}")
    else:
        form = ReunionGrupoForm()
    
    context = {
        'page_title': f'Nueva Reunión - {grupo.nombre}',
        'form': form,
        'grupo': grupo,
    }
    return render(request, 'gspg/reunion_form.html', context)


@login_required
def reunion_edit(request, reunion_pk):
    """Editar Reunión existente"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    reunion = get_object_or_404(ReunionGrupo, pk=reunion_pk, grupo__magister=request.user.active_magister)
    grupo = reunion.grupo
    
    if grupo.finalizado:
        messages.warning(request, "No se pueden editar reuniones de un grupo finalizado.")
        return redirect('gspg:reunion_list', grupo_pk=grupo.pk)
    
    if request.method == 'POST':
        form = ReunionGrupoForm(request.POST, request.FILES, instance=reunion)
        if form.is_valid():
            try:
                if (reunion.fecha != form.cleaned_data['fecha'] or 
                    reunion.hora != form.cleaned_data['hora']):
                    reunion.estado = 'reprogramada'
                form.save()
                messages.success(request, "Reunión actualizada exitosamente.")
                return redirect('gspg:reunion_list', grupo_pk=grupo.pk)
            except Exception as e:
                messages.error(request, f"Error al actualizar la reunión: {str(e)}")
    else:
        form = ReunionGrupoForm(instance=reunion)
    
    context = {
        'page_title': f'Editar Reunión - {grupo.nombre}',
        'form': form,
        'reunion': reunion,
        'grupo': grupo,
    }
    return render(request, 'gspg/reunion_form.html', context)

@login_required
def reunion_delete(request, reunion_pk):
    """Eliminar Reunión"""
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "No tienes un programa activo. Por favor, selecciona uno.")
        return redirect('gspg:dashboard')
    
    # Obtener la reunión y verificar que pertenezca al magister activo del usuario
    reunion = get_object_or_404(ReunionGrupo, pk=reunion_pk, grupo__magister=request.user.active_magister)
    grupo = reunion.grupo
    
    # Verificar si el grupo está finalizado
    if grupo.finalizado:
        messages.warning(request, "No se pueden eliminar reuniones de un grupo finalizado.")
        return redirect('gspg:reunion_list', grupo_pk=grupo.pk)
    
    if request.method == 'POST':
        try:
            reunion.delete()
            messages.success(request, "Reunión eliminada exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al eliminar la reunión: {str(e)}")
        return redirect('gspg:reunion_list', grupo_pk=grupo.pk)
    
    context = {
        'page_title': f'Eliminar Reunión - {grupo.nombre}',
        'reunion': reunion,
        'grupo': grupo,
    }
    return render(request, 'gspg/reunion_confirm_delete.html', context)


@login_required
def confirmar_asistencia(request, reunion_id):
    """Permitir al estudiante confirmar asistencia a una reunión"""
    reunion = get_object_or_404(ReunionGrupo, id=reunion_id)

    # Verificar que el usuario tenga un magíster activo
    if not hasattr(request.user, 'active_magister') or not request.user.active_magister:
        messages.warning(request, "Debes tener un programa activo para confirmar asistencia.")
        return redirect('gspg:dashboard')

    # Verificar que el usuario sea un estudiante válido del grupo
    try:
        estudiante = Estudiante.objects.get(user=request.user, intake__magister=request.user.active_magister)
    except Estudiante.DoesNotExist:
        messages.error(request, "No estás registrado como estudiante en este programa.")
        return redirect('gspg:dashboard')

    asistencia, _ = AsistenciaReunion.objects.get_or_create(
        reunion=reunion,
        estudiante=estudiante
    )

    if request.method == 'POST':
        form = AsistenciaReunionForm(request.POST, instance=asistencia)
        if form.is_valid():
            form.save()
            messages.success(request, "Asistencia confirmada correctamente.")
            return redirect('gspg:reunion_list', grupo_pk=reunion.grupo.pk)
    else:
        form = AsistenciaReunionForm(instance=asistencia)

    context = {
        'form': form,
        'reunion': reunion,
        'grupo': reunion.grupo,
        'page_title': "Confirmar Asistencia",
    }

    return render(request, 'gspg/confirmar_asistencia.html', context)



def calcular_estadisticas_asistencia(grupo):
    """
    Calcula estadísticas de asistencia para cada estudiante del grupo.
    Retorna un diccionario donde la clave es el ID del estudiante y el valor
    contiene sus estadísticas de asistencia.
    """
    # Obtener todas las reuniones del grupo
    reuniones = ReunionGrupo.objects.filter(grupo=grupo)
    total_reuniones = reuniones.count()
    
    # Si no hay reuniones, retornar un diccionario vacío
    if total_reuniones == 0:
        return {}
    
    # Inicializar estadísticas para cada estudiante
    estudiantes = grupo.estudiantes.all()
    estadisticas = {}
    
    for estudiante in estudiantes:
        # Obtener registros de asistencia del estudiante
        asistencias = AsistenciaReunion.objects.filter(
            reunion__grupo=grupo,
            estudiante=estudiante
        )
        
        # Contar presentes y ausentes
        presentes = asistencias.filter(asistio=True).count()
        ausentes = asistencias.filter(asistio=False).count()
        
        # Calcular porcentaje (evitar división por cero)
        porcentaje = (presentes / total_reuniones) * 100 if total_reuniones > 0 else 0
        
        # Reuniones sin registro de asistencia
        sin_registro = total_reuniones - (presentes + ausentes)
        
        # Guardar estadísticas
        estadisticas[estudiante.id] = {
            'estudiante': estudiante,
            'presentes': presentes,
            'ausentes': ausentes,
            'sin_registro': sin_registro,
            'total_reuniones': total_reuniones,
            'porcentaje': round(porcentaje, 1)
        }
    
    return estadisticas

from django.http import FileResponse
import os

@login_required
def descargar_acta(request, acta_id):
    acta = get_object_or_404(ActaReunion, id=acta_id)
    
    try:
        file_path = acta.archivo.path
        
        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        else:
            messages.error(request, "El archivo no existe en el servidor.")
    except Exception as e:
        import traceback
        print(f"Error en descargar_acta: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"Error al descargar el archivo: {str(e)}")
    
    # Redirección en caso de error
    return redirect('gspg:reunion_list', grupo_pk=acta.reunion.grupo.pk)






@login_required
def set_active_programa(request, magister_id):
    if request.user.set_active_magister(magister_id):
        messages.success(request, "Programa activo actualizado correctamente.")
    else:
        messages.error(request, "No tienes acceso a ese programa.")
    return redirect('gspg:dashboard')


def subir_acta(request, reunion_id):
    if request.session.get('tipo') != 'profesor':
        messages.warning(request, "No tienes permiso para acceder a esta página.")
        return redirect('gspg_client:login')

    reunion = get_object_or_404(ReunionGrupo, id=reunion_id)
    profesor_id = request.session.get('id')
    profesor = get_object_or_404(Profesor, id=profesor_id)

    if request.method == 'POST':
        form = ActaReunionForm(request.POST, request.FILES)
        if form.is_valid():
            acta = form.save(commit=False)
            acta.reunion = reunion
            acta.subido_por = profesor
            acta.save()
            messages.success(request, "Acta subida correctamente.")
            return redirect('gspg_client:reunion_detalle', reunion_id=reunion.id)
    else:
        form = ActaReunionForm()

    return render(request, 'gspg/subir_act_reunion.html', {
        'form': form,
        'reunion': reunion
    })