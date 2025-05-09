# Generated by Django 5.2 on 2025-04-19 02:10

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Intake',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.IntegerField(choices=[(1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')], verbose_name='Mes de inicio')),
                ('year', models.IntegerField(validators=[django.core.validators.MinValueValidator(2000), django.core.validators.MaxValueValidator(2100)], verbose_name='Año')),
                ('section', models.IntegerField(choices=[(1, '1'), (2, '2')], verbose_name='Sección')),
            ],
            options={
                'verbose_name': 'Intake',
                'verbose_name_plural': 'Intakes',
                'ordering': ['-year', '-month', 'section'],
            },
        ),
        migrations.CreateModel(
            name='Magister',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nombre')),
                ('faculty', models.CharField(max_length=200, verbose_name='Facultad')),
                ('university', models.CharField(max_length=200, verbose_name='Universidad')),
            ],
            options={
                'verbose_name': 'Programa',
                'verbose_name_plural': 'Programas',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Persona',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rut', models.CharField(max_length=13, unique=True, validators=[django.core.validators.RegexValidator(message='El RUT debe contener solo números, sin puntos ni guión.', regex='^\\d{1,13}$')], verbose_name='RUT')),
                ('nombre_completo', models.CharField(max_length=200, verbose_name='Nombre Completo')),
                ('telefono', models.CharField(max_length=20, verbose_name='Teléfono')),
                ('correo_institucional', models.EmailField(max_length=254, verbose_name='Correo Institucional')),
                ('correo_personal', models.EmailField(blank=True, max_length=254, verbose_name='Correo Personal')),
            ],
            options={
                'verbose_name': 'Persona',
                'verbose_name_plural': 'Personas',
                'ordering': ['nombre_completo'],
            },
        ),
        migrations.CreateModel(
            name='ReunionGrupo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('hora', models.TimeField()),
                ('link', models.URLField(blank=True, null=True)),
                ('comentarios', models.TextField(blank=True, null=True)),
                ('archivo_adjunto', models.FileField(blank=True, null=True, upload_to='reuniones/adjuntos/')),
            ],
        ),
        migrations.CreateModel(
            name='Estudiante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[('activo', 'Activo'), ('inhabilitado', 'Inhabilitado'), ('retirado', 'Retirado')], default='activo', max_length=15, verbose_name='Estado')),
                ('proceso_grado', models.CharField(choices=[('pendiente', 'Pendiente'), ('proceso', 'En proceso'), ('finalizado', 'Finalizado')], default='pendiente', max_length=15, verbose_name='Proceso de Grado')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')),
                ('intake', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='estudiantes', to='gspg.intake', verbose_name='Intake')),
                ('persona', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='estudiantes', to='gspg.persona')),
            ],
            options={
                'verbose_name': 'Estudiante',
                'verbose_name_plural': 'Estudiantes',
                'ordering': ['persona__nombre_completo'],
            },
        ),
        migrations.AddField(
            model_name='intake',
            name='magister',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='intakes', to='gspg.magister', verbose_name='Magíster'),
        ),
        migrations.CreateModel(
            name='Profesor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rut', models.CharField(max_length=13, unique=True, validators=[django.core.validators.RegexValidator(message='El RUT debe contener solo números, sin puntos ni guión.', regex='^\\d{1,13}$')], verbose_name='RUT')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre')),
                ('correo_institucional', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Correo Institucional')),
                ('correo_personal', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Correo Personal')),
                ('telefono', models.CharField(max_length=20, verbose_name='Teléfono')),
                ('magisteres', models.ManyToManyField(related_name='profesores', to='gspg.magister', verbose_name='Magísteres')),
            ],
            options={
                'verbose_name': 'Profesor',
                'verbose_name_plural': 'Profesores',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='GrupoTrabajo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre del Grupo')),
                ('fecha_inicio', models.DateField(verbose_name='Fecha de Inicio')),
                ('fecha_fin', models.DateField(verbose_name='Fecha de Finalización')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('finalizado', models.BooleanField(default=False, verbose_name='Proceso Finalizado')),
                ('estudiantes', models.ManyToManyField(related_name='grupos_trabajo', to='gspg.estudiante', verbose_name='Estudiantes')),
                ('intake', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grupos_trabajo', to='gspg.intake', verbose_name='Intake')),
                ('magister', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grupos_trabajo', to='gspg.magister', verbose_name='Magíster')),
                ('profesor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grupos_trabajo', to='gspg.profesor', verbose_name='Profesor Guía')),
            ],
            options={
                'verbose_name': 'Grupo de Trabajo',
                'verbose_name_plural': 'Grupos de Trabajo',
                'ordering': ['nombre'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='intake',
            unique_together={('month', 'year', 'section', 'magister')},
        ),
        migrations.CreateModel(
            name='AsistenciaReunion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asistio', models.BooleanField(default=False)),
                ('comentario', models.TextField(blank=True, null=True)),
                ('estudiante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gspg.estudiante')),
                ('reunion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gspg.reuniongrupo')),
            ],
            options={
                'unique_together': {('reunion', 'estudiante')},
            },
        ),
    ]
