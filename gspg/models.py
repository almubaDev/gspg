from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

# === MAGÍSTER ===
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


# === INTAKE ===
class Intake(models.Model):
    MONTH_CHOICES = [(i, name) for i, name in enumerate(
        ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'], 1)]
    
    SECTION_CHOICES = [(1, '1'), (2, '2')]

    month = models.IntegerField(choices=MONTH_CHOICES, verbose_name="Mes de inicio")
    year = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)], verbose_name="Año")
    section = models.IntegerField(choices=SECTION_CHOICES, verbose_name="Sección")
    magister = models.ForeignKey(Magister, on_delete=models.CASCADE, related_name='intakes', verbose_name="Magíster")

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


# === PERSONA ===
class Persona(models.Model):
    rut = models.CharField(
        max_length=13,
        unique=True,
        validators=[RegexValidator(regex=r'^\d{1,13}$', message="El RUT debe contener solo números, sin puntos ni guión.")],
        verbose_name="RUT"
    )
    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre Completo")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    correo_institucional = models.EmailField(verbose_name="Correo Institucional")
    correo_personal = models.EmailField(blank=True, verbose_name="Correo Personal")

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ['nombre_completo']

    def __str__(self):
        return f"{self.nombre_completo} - {self.rut}"


# === ESTUDIANTE ===
class Estudiante(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='estudiantes')
    intake = models.ForeignKey(Intake, on_delete=models.CASCADE, related_name='estudiantes', verbose_name="Intake")
    estado = models.CharField(
        max_length=15,
        choices=[('activo', 'Activo'), ('inhabilitado', 'Inhabilitado'), ('retirado', 'Retirado')],
        default='activo',
        verbose_name="Estado"
    )
    proceso_grado = models.CharField(
        max_length=15,
        choices=[('pendiente', 'Pendiente'), ('proceso', 'En proceso'), ('finalizado', 'Finalizado')],
        default='pendiente',
        verbose_name="Proceso de Grado",
        blank=True,
        null=True
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['persona__nombre_completo']

    def __str__(self):
        return f"{self.persona.nombre_completo} ({self.persona.rut}) - {self.intake}"


# === PROFESOR ===
class Profesor(models.Model):
    rut = models.CharField(
        max_length=13,
        unique=True,
        validators=[RegexValidator(regex=r'^\d{1,13}$', message="El RUT debe contener solo números, sin puntos ni guión.")],
        verbose_name="RUT"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    correo_institucional = models.EmailField(blank=True, null=True, verbose_name="Correo Institucional")
    correo_personal = models.EmailField(blank=True, null=True, verbose_name="Correo Personal")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    magisteres = models.ManyToManyField(Magister, related_name='profesores', verbose_name="Magísteres")

    class Meta:
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.rut}"


# === GRUPO DE TRABAJO ===
class GrupoTrabajo(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Grupo")
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, related_name='grupos_trabajo', verbose_name="Profesor Guía")
    intake = models.ForeignKey(Intake, on_delete=models.CASCADE, related_name='grupos_trabajo', verbose_name="Intake")
    estudiantes = models.ManyToManyField(Estudiante, related_name='grupos_trabajo', verbose_name="Estudiantes")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Finalización")
    magister = models.ForeignKey(Magister, on_delete=models.CASCADE, related_name='grupos_trabajo', verbose_name="Magíster")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    finalizado = models.BooleanField(default=False, verbose_name="Proceso Finalizado")

    class Meta:
        verbose_name = "Grupo de Trabajo"
        verbose_name_plural = "Grupos de Trabajo"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.intake}"


# === REUNIÓN DE GRUPO ===
class ReunionGrupo(models.Model):
    grupo = models.ForeignKey('GrupoTrabajo', on_delete=models.CASCADE, related_name='reuniones', verbose_name="Grupo de Trabajo")
    fecha = models.DateField()
    hora = models.TimeField()
    link = models.URLField(blank=True, null=True)
    comentarios = models.TextField(blank=True, null=True)

    archivo_adjunto = models.FileField(upload_to='reuniones/adjuntos/', blank=True, null=True)

    def __str__(self):
        return f"Reunión del {self.fecha} a las {self.hora}"

class AsistenciaReunion(models.Model):
    reunion = models.ForeignKey(ReunionGrupo, on_delete=models.CASCADE)
    estudiante = models.ForeignKey('Estudiante', on_delete=models.CASCADE)
    asistio = models.BooleanField(default=False)
    comentario = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('reunion', 'estudiante')

    def __str__(self):
        return f"{self.estudiante} - {self.reunion} - {'Asistió' if self.asistio else 'No asistió'}"
    
    

class ActaReunion(models.Model):
    reunion = models.ForeignKey('ReunionGrupo', on_delete=models.CASCADE, related_name='actas')
    archivo = models.FileField(upload_to='actas/')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey('Profesor', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"Acta - {self.reunion.grupo.nombre} - {self.fecha_subida.strftime('%d/%m/%Y %H:%M')}"
