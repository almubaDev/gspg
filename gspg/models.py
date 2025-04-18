from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

class Magister(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    faculty = models.CharField(max_length=200, verbose_name="Facultad")
    university = models.CharField(max_length=200, verbose_name="Universidad")
    
    class Meta:
        verbose_name = "Magíster"
        verbose_name_plural = "Magísteres"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.university}"
    
    
    from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Magister(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    faculty = models.CharField(max_length=200, verbose_name="Facultad")
    university = models.CharField(max_length=200, verbose_name="Universidad")
    
    class Meta:
        verbose_name = "Magíster"
        verbose_name_plural = "Magísteres"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.university}"


class Intake(models.Model):
    MONTH_CHOICES = [
        (1, 'Enero'),
        (2, 'Febrero'),
        (3, 'Marzo'),
        (4, 'Abril'),
        (5, 'Mayo'),
        (6, 'Junio'),
        (7, 'Julio'),
        (8, 'Agosto'),
        (9, 'Septiembre'),
        (10, 'Octubre'),
        (11, 'Noviembre'),
        (12, 'Diciembre'),
    ]
    
    SECTION_CHOICES = [
        (1, '1'),
        (2, '2'),
    ]
    
    month = models.IntegerField(
        choices=MONTH_CHOICES,
        verbose_name="Mes de inicio"
    )
    year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        verbose_name="Año"
    )
    section = models.IntegerField(
        choices=SECTION_CHOICES,
        verbose_name="Sección"
    )
    magister = models.ForeignKey(
        Magister,
        on_delete=models.CASCADE,
        related_name='intakes',
        verbose_name="Magíster"
    )
    
    class Meta:
        verbose_name = "Intake"
        verbose_name_plural = "Intakes"
        ordering = ['-year', '-month', 'section']
        # Asegura que no pueda haber dos intakes con la misma combinación de mes, año, sección y magíster
        unique_together = ['month', 'year', 'section', 'magister']
    
    def __str__(self):
        month_name = dict(self.MONTH_CHOICES)[self.month]
        return f"{month_name} {self.year} - Sección {self.section} ({self.magister.name})"
    
    def get_short_name(self):
        month_name = dict(self.MONTH_CHOICES)[self.month]
        return f"{month_name[:3]} {self.year} - S{self.section}"
    


class Estudiante(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inhabilitado', 'Inhabilitado'),
        ('retirado', 'Retirado'),
    ]
    
    PROCESO_GRADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('finalizado', 'Finalizado'),
    ]
    
    intake = models.ForeignKey(
        Intake,
        on_delete=models.CASCADE,
        related_name='estudiantes',
        verbose_name="Intake"
    )
    rut = models.CharField(
        max_length=13,
        validators=[
            RegexValidator(
                regex=r'^\d{1,13}$',
                message="El RUT debe contener solo números, sin puntos ni guión."
            )
        ],
        unique=True,
        verbose_name="RUT"
    )
    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre Completo")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    correo_institucional = models.EmailField(verbose_name="Correo Institucional")
    correo_personal = models.EmailField(blank=True, verbose_name="Correo Personal")
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='activo',
        verbose_name="Estado"
    )
    proceso_grado = models.CharField(
        max_length=15,
        choices=PROCESO_GRADO_CHOICES,
        default='pendiente',
        verbose_name="Proceso de Grado"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    
    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['nombre_completo']
        
    def __str__(self):
        return f"{self.nombre_completo} - {self.rut}"
    
    
    
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

class Magister(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    faculty = models.CharField(max_length=200, verbose_name="Facultad")
    university = models.CharField(max_length=200, verbose_name="Universidad")
    
    class Meta:
        verbose_name = "Programa"
        verbose_name_plural = "Programas"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.university}"


class Intake(models.Model):
    MONTH_CHOICES = [
        (1, 'Enero'),
        (2, 'Febrero'),
        (3, 'Marzo'),
        (4, 'Abril'),
        (5, 'Mayo'),
        (6, 'Junio'),
        (7, 'Julio'),
        (8, 'Agosto'),
        (9, 'Septiembre'),
        (10, 'Octubre'),
        (11, 'Noviembre'),
        (12, 'Diciembre'),
    ]
    
    SECTION_CHOICES = [
        (1, '1'),
        (2, '2'),
    ]
    
    month = models.IntegerField(
        choices=MONTH_CHOICES,
        verbose_name="Mes de inicio"
    )
    year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        verbose_name="Año"
    )
    section = models.IntegerField(
        choices=SECTION_CHOICES,
        verbose_name="Sección"
    )
    magister = models.ForeignKey(
        Magister,
        on_delete=models.CASCADE,
        related_name='intakes',
        verbose_name="Magíster"
    )
    
    class Meta:
        verbose_name = "Intake"
        verbose_name_plural = "Intakes"
        ordering = ['-year', '-month', 'section']
        unique_together = ['month', 'year', 'section', 'magister']
    
    def __str__(self):
        month_name = dict(self.MONTH_CHOICES)[self.month]
        return f"{month_name} {self.year} - Sección {self.section} ({self.magister.name})"
    
    def get_short_name(self):
        month_name = dict(self.MONTH_CHOICES)[self.month]
        return f"{month_name[:3]} {self.year} - S{self.section}"


class Estudiante(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inhabilitado', 'Inhabilitado'),
        ('retirado', 'Retirado'),
    ]
    
    PROCESO_GRADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('proceso', 'En proceso'),
        ('finalizado', 'Finalizado'),
    ]
    
    intake = models.ForeignKey(
        Intake,
        on_delete=models.CASCADE,
        related_name='estudiantes',
        verbose_name="Intake"
    )
    rut = models.CharField(
        max_length=13,
        validators=[
            RegexValidator(
                regex=r'^\d{1,13}$',
                message="El RUT debe contener solo números, sin puntos ni guión."
            )
        ],
        unique=True,
        verbose_name="RUT"
    )
    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre Completo")
    telefono = models.CharField(max_length=20, blank=False, null=False, verbose_name="Teléfono")
    correo_institucional = models.EmailField(verbose_name="Correo Institucional")
    correo_personal = models.EmailField(blank=True, verbose_name="Correo Personal")
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='activo',
        verbose_name="Estado"
    )
    proceso_grado = models.CharField(
        max_length=15,
        choices=PROCESO_GRADO_CHOICES,
        default='pendiente',
        verbose_name="Proceso de Grado"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    
    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['nombre_completo']
        
    def __str__(self):
        return f"{self.nombre_completo} - {self.rut}"


class Profesor(models.Model):
    rut = models.CharField(
        max_length=13,
        validators=[
            RegexValidator(
                regex=r'^\d{1,13}$',
                message="El RUT debe contener solo números, sin puntos ni guión."
            )
        ],
        unique=True,
        verbose_name="RUT"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    correo_institucional = models.EmailField(blank=True, null=True, verbose_name="Correo Institucional")
    correo_personal = models.EmailField(blank=True, null=True, verbose_name="Correo Personal")
    telefono = models.CharField(max_length=20, blank=False, null=False, verbose_name="Teléfono")
    magisteres = models.ManyToManyField(Magister, related_name='profesores', verbose_name="Magísteres")
    
    class Meta:
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.rut}"
    
    
    
class GrupoTrabajo(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Grupo")
    profesor = models.ForeignKey(
        Profesor, 
        on_delete=models.CASCADE,
        related_name='grupos_trabajo',
        verbose_name="Profesor Guía"
    )
    intake = models.ForeignKey(
        Intake,
        on_delete=models.CASCADE,
        related_name='grupos_trabajo',
        verbose_name="Intake",
    )
    estudiantes = models.ManyToManyField(
        Estudiante,
        related_name='grupos_trabajo',
        verbose_name="Estudiantes"
    )
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Finalización")
    magister = models.ForeignKey(
        Magister,
        on_delete=models.CASCADE,
        related_name='grupos_trabajo',
        verbose_name="Magíster"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    finalizado = models.BooleanField(default=False, verbose_name="Proceso Finalizado")
    
    class Meta:
        verbose_name = "Grupo de Trabajo"
        verbose_name_plural = "Grupos de Trabajo"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.nombre} - {self.intake.get_short_name()}"
    
    def save(self, *args, **kwargs):
        # Si no se especifica el magíster, usar el del intake
        if not self.magister_id and self.intake_id:
            self.magister = self.intake.magister
            
        # Primero guardamos el grupo
        super().save(*args, **kwargs)
        
        # Actualizamos el estado de proceso de grado de los estudiantes si no está finalizado
        if not self.finalizado:
            self.estudiantes.all().update(proceso_grado='proceso')
    
    def finalizar_proceso(self):
        """Finaliza el proceso de grado para todos los estudiantes del grupo"""
        if not self.finalizado:
            self.finalizado = True
            self.save()
            # Actualizar el estado de los estudiantes
            self.estudiantes.all().update(proceso_grado='finalizado')
            return True
        return False
    
    
class ReunionGrupo(models.Model):
    ESTADO_CHOICES = [
        ('programada', 'Programada'),
        ('reprogramada', 'Reprogramada'),
    ]
    
    grupo = models.ForeignKey(
        GrupoTrabajo,
        on_delete=models.CASCADE,
        related_name='reuniones',
        verbose_name="Grupo de Trabajo"
    )
    fecha = models.DateField(verbose_name="Fecha de Reunión")
    hora = models.TimeField(verbose_name="Hora de Reunión")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='programada',
        verbose_name="Estado"
    )
    link_reunion = models.URLField(
        blank=True, 
        null=True, 
        verbose_name="Link de Reunión",
        help_text="URL para reunión virtual (opcional)"
    )
    comentario = models.TextField(
        blank=True, 
        verbose_name="Comentarios",
        help_text="Notas adicionales sobre la reunión"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    class Meta:
        verbose_name = "Reunión de Grupo"
        verbose_name_plural = "Reuniones de Grupo"
        ordering = ['fecha', 'hora']
    
    def __str__(self):
        return f"Reunión {self.grupo.nombre} - {self.fecha.strftime('%d/%m/%Y')} {self.hora.strftime('%H:%M')}"
    
    # Métodos para facilitar el envío de notificaciones
    @property
    def fecha_hora_reunion(self):
        """Retorna un objeto datetime combinando fecha y hora"""
        from datetime import datetime, timedelta
        import pytz
        # Asumiendo que estamos usando la zona horaria de Chile
        chile_tz = pytz.timezone('America/Santiago')
        dt = datetime.combine(self.fecha, self.hora)
        return chile_tz.localize(dt)
    
    @property
    def debe_notificar_24h(self):
        """Verifica si se debe enviar la notificación de 24h"""
        from datetime import datetime, timedelta
        import pytz
        now = pytz.timezone('America/Santiago').localize(datetime.now())
        diff = self.fecha_hora_reunion - now
        # Entre 23.5 y 24.5 horas antes de la reunión
        return timedelta(hours=23, minutes=30) <= diff <= timedelta(hours=24, minutes=30)
    
    @property
    def debe_notificar_1h(self):
        """Verifica si se debe enviar la notificación de 1h"""
        from datetime import datetime, timedelta
        import pytz
        now = pytz.timezone('America/Santiago').localize(datetime.now())
        diff = self.fecha_hora_reunion - now
        # Entre 50 minutos y 1 hora y 10 minutos antes de la reunión
        return timedelta(minutes=50) <= diff <= timedelta(hours=1, minutes=10)