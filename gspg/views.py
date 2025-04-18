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
from .models import Intake, Estudiante, Profesor, GrupoTrabajo, ReunionGrupo
from .forms import (IntakeForm, EstudianteForm, EstudianteBulkUploadForm, ProfesorForm, GrupoTrabajoForm, 
                    EstudianteAddForm, ReunionGrupoForm)

@login_required
def dashboard(request):
    """Vista principal del dashboard"""
    # Mostrar solo los intakes del magister del usuario actual
    user_magister = request.user.magister
    
    context = {
        'page_title': 'Dashboard',
        'user_magister': user_magister,
    }
    
    # Si el usuario tiene un magister asignado, añadir los intakes disponibles
    if user_magister:
        intakes = Intake.objects.filter(magister=user_magister)
        context['intakes'] = intakes
        
    return render(request, 'gspg/dashboard.html', context)

@login_required
def intake_list(request):
    """Lista de Intakes"""
    # Solo mostrar intakes relacionados con el magister del usuario
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    intakes = Intake.objects.filter(magister=request.user.magister)
    
    context = {
        'page_title': 'Intakes',
        'intakes': intakes,
    }
    return render(request, 'gspg/intake_list.html', context)

@login_required
def intake_create(request):
    """Crear nuevo Intake"""
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    if request.method == 'POST':
        form = IntakeForm(request.POST, user=request.user)
        
        if form.is_valid():
            # Asegurarse de que el magister sea el del usuario actual
            intake = form.save(commit=False)
            intake.magister = request.user.magister
            
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el intake y verificar que pertenezca al magister del usuario
    intake = get_object_or_404(Intake, pk=pk, magister=request.user.magister)
    
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el intake y verificar que pertenezca al magister del usuario
    intake = get_object_or_404(Intake, pk=pk, magister=request.user.magister)
    
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Filtro por intake, estado y proceso de grado
    intake_id = request.GET.get('intake', '')
    estado = request.GET.get('estado', '')
    proceso_grado = request.GET.get('proceso_grado', '')  # Nuevo filtro
    search = request.GET.get('search', '')
    
    # Obtener estudiantes del magíster del usuario
    estudiantes = Estudiante.objects.filter(intake__magister=request.user.magister)
    
    # Aplicar filtros adicionales
    if intake_id:
        estudiantes = estudiantes.filter(intake_id=intake_id)
    if estado:
        estudiantes = estudiantes.filter(estado=estado)
    if proceso_grado:  # Aplicar el nuevo filtro
        estudiantes = estudiantes.filter(proceso_grado=proceso_grado)
    if search:
        estudiantes = estudiantes.filter(
            Q(nombre_completo__icontains=search) | 
            Q(rut__icontains=search) | 
            Q(correo_institucional__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(estudiantes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener intakes para el filtro
    intakes = Intake.objects.filter(magister=request.user.magister)
    
    context = {
        'page_title': 'Estudiantes',
        'page_obj': page_obj,
        'intakes': intakes,
        'estados': Estudiante.ESTADO_CHOICES,
        'procesos_grado': Estudiante.PROCESO_GRADO_CHOICES,  # Para el filtro
        'selected_intake': intake_id,
        'selected_estado': estado,
        'selected_proceso_grado': proceso_grado,  # Para mantener selección
        'search': search,
    }
    return render(request, 'gspg/estudiante_list.html', context)

@login_required
def estudiante_create(request):
    """Crear nuevo Estudiante"""
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    if request.method == 'POST':
        form = EstudianteForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                # Verificar que el intake pertenezca al magíster del usuario
                intake = form.cleaned_data['intake']
                if intake.magister != request.user.magister:
                    messages.error(request, "El intake seleccionado no pertenece a tu magíster.")
                    return redirect('gspg:estudiante_list')
                
                form.save()
                messages.success(request, "Estudiante creado exitosamente.")
                return redirect('gspg:estudiante_list')
            except Exception as e:
                messages.error(request, f"Error al crear el estudiante: {str(e)}")
    else:
        form = EstudianteForm(user=request.user)
    
    context = {
        'page_title': 'Nuevo Estudiante',
        'form': form,
    }
    return render(request, 'gspg/estudiante_form.html', context)

@login_required
def estudiante_edit(request, pk):
    """Editar Estudiante existente"""
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el estudiante y verificar que pertenezca al magister del usuario
    estudiante = get_object_or_404(Estudiante, pk=pk, intake__magister=request.user.magister)
    
    if request.method == 'POST':
        form = EstudianteForm(request.POST, instance=estudiante, user=request.user)
        
        if form.is_valid():
            try:
                # Verificar que el intake pertenezca al magíster del usuario
                intake = form.cleaned_data['intake']
                if intake.magister != request.user.magister:
                    messages.error(request, "El intake seleccionado no pertenece a tu magíster.")
                    return redirect('gspg:estudiante_list')
                
                form.save()
                messages.success(request, "Estudiante actualizado exitosamente.")
                return redirect('gspg:estudiante_list')
            except Exception as e:
                messages.error(request, f"Error al actualizar el estudiante: {str(e)}")
    else:
        form = EstudianteForm(instance=estudiante, user=request.user)
    
    context = {
        'page_title': 'Editar Estudiante',
        'form': form,
        'estudiante': estudiante,
    }
    return render(request, 'gspg/estudiante_form.html', context)

@login_required
def estudiante_delete(request, pk):
    """Eliminar Estudiante"""
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el estudiante y verificar que pertenezca al magister del usuario
    estudiante = get_object_or_404(Estudiante, pk=pk, intake__magister=request.user.magister)
    
    if request.method == 'POST':
        try:
            estudiante.delete()
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    if request.method == 'POST':
        form = EstudianteBulkUploadForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            try:
                intake = form.cleaned_data['intake']
                
                # Verificar que el intake pertenezca al magíster del usuario
                if intake.magister != request.user.magister:
                    messages.error(request, "El intake seleccionado no pertenece a tu magíster.")
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
                        
                        # Validar estado
                        if estado not in dict(Estudiante.ESTADO_CHOICES):
                            estado = 'activo'
                        
                        # Buscar si el estudiante ya existe por RUT
                        estudiante, created_flag = Estudiante.objects.update_or_create(
                            rut=row['rut'],
                            defaults={
                                'intake': intake,
                                'nombre_completo': row['nombre_completo'],
                                'telefono': telefono,
                                'correo_institucional': row['correo_institucional'],
                                'correo_personal': correo_personal,
                                'estado': estado
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Filtros (los mismos que en la lista)
    intake_id = request.GET.get('intake', '')
    estado = request.GET.get('estado', '')
    proceso_grado = request.GET.get('proceso_grado', '')
    search = request.GET.get('search', '')
    
    # Obtener estudiantes del magíster del usuario
    estudiantes = Estudiante.objects.filter(intake__magister=request.user.magister)
    
    # Aplicar filtros adicionales
    if intake_id:
        estudiantes = estudiantes.filter(intake_id=intake_id)
    if estado:
        estudiantes = estudiantes.filter(estado=estado)
    if proceso_grado:
        estudiantes = estudiantes.filter(proceso_grado=proceso_grado)
    if search:
        estudiantes = estudiantes.filter(
            Q(nombre_completo__icontains=search) | 
            Q(rut__icontains=search) | 
            Q(correo_institucional__icontains=search)
        )
    
    # Crear un buffer en memoria
    output = BytesIO()
    
    # Crear un libro de trabajo y una hoja
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Estudiantes')
    
    # Formatos - Aquí está la corrección
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#16325B',
        'font_color': 'white',  # Cambiar 'color' a 'font_color'
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
        worksheet.write(row_num, 0, estudiante.rut, row_format)
        worksheet.write(row_num, 1, estudiante.nombre_completo, row_format)
        worksheet.write(row_num, 2, estudiante.telefono, row_format)
        worksheet.write(row_num, 3, estudiante.correo_institucional, row_format)
        worksheet.write(row_num, 4, estudiante.correo_personal, row_format)
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Filtros (los mismos que en la lista)
    intake_id = request.GET.get('intake', '')
    estado = request.GET.get('estado', '')
    search = request.GET.get('search', '')
    
    # Obtener estudiantes del magíster del usuario
    estudiantes = Estudiante.objects.filter(intake__magister=request.user.magister)
    
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
            Q(nombre_completo__icontains=search) | 
            Q(rut__icontains=search) | 
            Q(correo_institucional__icontains=search)
        )
    
    # Crear un buffer en memoria
    buffer = BytesIO()
    
    # Crear el PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Título
    title = f"Lista de Estudiantes - {request.user.magister.name}"
    
    # Datos para la tabla
    data = [['RUT', 'Nombre', 'Correo', 'Estado', 'Proceso Grado', 'Intake']]
    
    for e in estudiantes:
        data.append([
            e.rut,
            e.nombre_completo,
            e.correo_institucional,
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
@login_required
def profesor_list(request):
    """Lista de Profesores"""
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Buscar profesores relacionados con el magíster del usuario
    profesores = Profesor.objects.filter(magisteres=request.user.magister)
    
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
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
                if request.user.magister not in profesor_existente.magisteres.all():
                    profesor_existente.magisteres.add(request.user.magister)
                    messages.success(request, f"El profesor {profesor_existente.nombre} ha sido asociado a tu magíster.")
                else:
                    messages.info(request, f"El profesor {profesor_existente.nombre} ya estaba asociado a tu magíster.")
                
                return redirect('gspg:profesor_list')
            else:
                # Crear nuevo profesor
                profesor = form.save()
                
                try:
                    # Asociar al magíster actual
                    profesor.magisteres.add(request.user.magister)
                    
                    messages.success(request, "Profesor creado y asociado a tu magíster exitosamente.")
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el profesor y verificar que pertenezca al magister del usuario
    profesor = get_object_or_404(Profesor, pk=pk, magisteres=request.user.magister)
    
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el profesor y verificar que pertenezca al magister del usuario
    profesor = get_object_or_404(Profesor, pk=pk, magisteres=request.user.magister)
    
    if request.method == 'POST':
        try:
            # No eliminamos el profesor, solo lo desasociamos del magíster actual
            profesor.magisteres.remove(request.user.magister)
            messages.success(request, f"El profesor {profesor.nombre} ha sido desasociado de tu magíster.")
            
            # Si el profesor ya no está asociado a ningún magíster, lo eliminamos
            if profesor.magisteres.count() == 0:
                profesor.delete()
                messages.info(request, f"El profesor {profesor.nombre} ha sido eliminado porque no estaba asociado a ningún otro magíster.")
                
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
    
    if not request.user.magister:
        print("Error: Usuario sin magíster asignado")
        return JsonResponse({'error': 'No tienes un magíster asignado'}, status=400)
    
    intake_id = request.GET.get('intake_id')
    grupo_id = request.GET.get('grupo_id')
    
    print(f"Parámetros recibidos: intake_id={intake_id}, grupo_id={grupo_id}")
    
    if not intake_id:
        print("Error: No se proporcionó un intake_id")
        return JsonResponse({'error': 'No se proporcionó un intake'}, status=400)
    
    try:
        # Verificar que el intake pertenezca al magíster del usuario
        intake = Intake.objects.get(pk=intake_id)
        
        print(f"Intake encontrado: {intake} (ID: {intake.id})")
        print(f"Magíster del intake: {intake.magister.name} (ID: {intake.magister.id})")
        print(f"Magíster del usuario: {request.user.magister.name} (ID: {request.user.magister.id})")
        
        if intake.magister != request.user.magister:
            print("Error: El intake no pertenece al magíster del usuario")
            return JsonResponse({'error': 'El intake no pertenece a tu magíster'}, status=403)
        
        # Estudiantes que pertenecen a este intake específico
        todos_estudiantes = Estudiante.objects.filter(intake=intake)
        print(f"Total estudiantes en el intake: {todos_estudiantes.count()}")
        
        # Mostrar todos los estudiantes para depuración
        for i, e in enumerate(todos_estudiantes):
            print(f"Estudiante {i+1}: {e.nombre_completo} ({e.rut}) - Proceso: {e.proceso_grado}")
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
                    print(f"Estudiante del grupo {i+1}: {e.nombre_completo} ({e.rut})")
                
                # Modificar la consulta para incluir a los estudiantes del grupo actual
                query |= Q(grupos_trabajo=grupo)
            except GrupoTrabajo.DoesNotExist:
                print(f"Error: No se encontró el grupo con ID {grupo_id}")
        
        # Estudiantes disponibles (pendientes o ya en este grupo)
        estudiantes_disponibles = Estudiante.objects.filter(query).distinct()
        
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
            print(f"Añadiendo a resultado: {e.nombre_completo} ({e.rut})")
            estudiantes_data.append({
                'id': e.id,
                'text': f"{e.nombre_completo} ({e.rut})"
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Filtros
    profesor_id = request.GET.get('profesor', '')
    finalizado = request.GET.get('finalizado', '')
    search = request.GET.get('search', '')
    
    # Obtener grupos de trabajo del magíster del usuario
    grupos = GrupoTrabajo.objects.filter(magister=request.user.magister)
    
    # Aplicar filtros adicionales
    if profesor_id:
        grupos = grupos.filter(profesor_id=profesor_id)
    if finalizado:
        grupos = grupos.filter(finalizado=(finalizado == 'true'))
    if search:
        grupos = grupos.filter(
            Q(nombre__icontains=search) | 
            Q(profesor__nombre__icontains=search) |
            Q(estudiantes__nombre_completo__icontains=search)
        ).distinct()
    
    # Paginación
    paginator = Paginator(grupos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener profesores para el filtro
    profesores = Profesor.objects.filter(magisteres=request.user.magister)
    
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    if request.method == 'POST':
        form = GrupoTrabajoForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                # Verificar que el profesor pertenezca al magíster del usuario
                profesor = form.cleaned_data['profesor']
                if request.user.magister not in profesor.magisteres.all():
                    messages.error(request, "El profesor seleccionado no pertenece a tu magíster.")
                    return redirect('gspg:grupo_trabajo_list')
                
                # Verificar que el intake pertenezca al magíster del usuario
                intake = form.cleaned_data['intake']
                if intake.magister != request.user.magister:
                    messages.error(request, "El intake seleccionado no pertenece a tu magíster.")
                    return redirect('gspg:grupo_trabajo_list')
                
                # Verificar que los estudiantes pertenezcan al intake seleccionado
                estudiantes = form.cleaned_data['estudiantes']
                for estudiante in estudiantes:
                    if estudiante.intake != intake:
                        messages.error(request, "Uno o más estudiantes no pertenecen al intake seleccionado.")
                        return redirect('gspg:grupo_trabajo_list')
                
                # Crear el grupo de trabajo
                grupo = form.save(commit=False)
                grupo.magister = request.user.magister
                grupo.save()
                
                # Guardar relaciones ManyToMany
                form.save_m2m()
                
                messages.success(request, "Grupo de trabajo creado exitosamente.")
                return redirect('gspg:grupo_trabajo_list')
            except Exception as e:
                messages.error(request, f"Error al crear el grupo de trabajo: {str(e)}")
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=pk, magister=request.user.magister)
    
    # Si el grupo está finalizado, no permitir edición
    if grupo.finalizado:
        messages.warning(request, "No se puede editar un grupo con proceso finalizado.")
        return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
    
    if request.method == 'POST':
        form = GrupoTrabajoForm(request.POST, instance=grupo, user=request.user)
        
        if form.is_valid():
            try:
                # Verificar que el profesor pertenezca al magíster del usuario
                profesor = form.cleaned_data['profesor']
                if request.user.magister not in profesor.magisteres.all():
                    messages.error(request, "El profesor seleccionado no pertenece a tu magíster.")
                    return redirect('gspg:grupo_trabajo_list')
                
                # Verificar que los estudiantes pertenezcan al magíster del usuario
                estudiantes = form.cleaned_data['estudiantes']
                for estudiante in estudiantes:
                    if estudiante.intake.magister != request.user.magister:
                        messages.error(request, "Uno o más estudiantes no pertenecen a tu magíster.")
                        return redirect('gspg:grupo_trabajo_list')
                
                # Guardar cambios
                form.save()
                
                messages.success(request, "Grupo de trabajo actualizado exitosamente.")
                return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
            except Exception as e:
                messages.error(request, f"Error al actualizar el grupo de trabajo: {str(e)}")
    else:
        form = GrupoTrabajoForm(instance=grupo, user=request.user)
    
    context = {
        'page_title': 'Editar Grupo de Trabajo',
        'form': form,
        'grupo': grupo,
    }
    return render(request, 'gspg/grupo_trabajo_form.html', context)

@login_required
def grupo_trabajo_detail(request, pk):
    """Ver detalles de un Grupo de Trabajo"""
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=pk, magister=request.user.magister)
    
    # Verificar si el proceso puede ser finalizado (fecha actual >= fecha fin)
    from datetime import date
    puede_finalizar = not grupo.finalizado and date.today() >= grupo.fecha_fin
    
    context = {
        'page_title': 'Detalle de Grupo de Trabajo',
        'grupo': grupo,
        'puede_finalizar': puede_finalizar,
    }
    return render(request, 'gspg/grupo_trabajo_detail.html', context)

@login_required
def grupo_trabajo_delete(request, pk):
    """Eliminar Grupo de Trabajo"""
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=pk, magister=request.user.magister)
    
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=pk, magister=request.user.magister)
    
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=pk, magister=request.user.magister)
    
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=grupo_pk, magister=request.user.magister)
    
    # Si el grupo está finalizado, no permitir eliminar estudiantes
    if grupo.finalizado:
        messages.warning(request, "No se pueden eliminar estudiantes de un grupo con proceso finalizado.")
        return redirect('gspg:grupo_trabajo_detail', pk=grupo.pk)
    
    # Obtener el estudiante y verificar que pertenezca al grupo
    estudiante = get_object_or_404(Estudiante, pk=estudiante_pk, grupos_trabajo=grupo)
    
    if request.method == 'POST':
        try:
            # Eliminar estudiante del grupo
            grupo.estudiantes.remove(estudiante)
            
            # Actualizar estado de proceso de grado
            estudiante.proceso_grado = 'pendiente'
            estudiante.save()
            
            messages.success(request, f"El estudiante {estudiante.nombre_completo} ha sido eliminado del grupo.")
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=grupo_pk, magister=request.user.magister)
    
    # Obtener las reuniones del grupo
    reuniones = ReunionGrupo.objects.filter(grupo=grupo)
    
    # Filtrar reuniones pasadas y futuras
    from datetime import date
    hoy = date.today()
    reuniones_pasadas = reuniones.filter(fecha__lt=hoy).order_by('-fecha', '-hora')
    reuniones_futuras = reuniones.filter(fecha__gte=hoy).order_by('fecha', 'hora')
    
    context = {
        'page_title': f'Reuniones - {grupo.nombre}',
        'grupo': grupo,
        'reuniones_futuras': reuniones_futuras,
        'reuniones_pasadas': reuniones_pasadas,
    }
    return render(request, 'gspg/reunion_list.html', context)

@login_required
def reunion_create(request, grupo_pk):
    """Crear nueva Reunión para un Grupo"""
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener el grupo y verificar que pertenezca al magister del usuario
    grupo = get_object_or_404(GrupoTrabajo, pk=grupo_pk, magister=request.user.magister)
    
    # Verificar si el grupo está finalizado
    if grupo.finalizado:
        messages.warning(request, "No se pueden crear reuniones para un grupo finalizado.")
        return redirect('gspg:reunion_list', grupo_pk=grupo.pk)
    
    if request.method == 'POST':
        form = ReunionGrupoForm(request.POST)
        
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener la reunión y verificar que pertenezca al magister del usuario
    reunion = get_object_or_404(ReunionGrupo, pk=reunion_pk, grupo__magister=request.user.magister)
    grupo = reunion.grupo
    
    # Verificar si el grupo está finalizado
    if grupo.finalizado:
        messages.warning(request, "No se pueden editar reuniones de un grupo finalizado.")
        return redirect('gspg:reunion_list', grupo_pk=grupo.pk)
    
    if request.method == 'POST':
        form = ReunionGrupoForm(request.POST, instance=reunion)
        
        if form.is_valid():
            try:
                # Si cambia la fecha u hora, marcamos como reprogramada
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
    if not request.user.magister:
        messages.warning(request, "No tienes un magíster asignado. Contacta al administrador.")
        return redirect('gspg:dashboard')
    
    # Obtener la reunión y verificar que pertenezca al magister del usuario
    reunion = get_object_or_404(ReunionGrupo, pk=reunion_pk, grupo__magister=request.user.magister)
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