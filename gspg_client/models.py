from django.db import models

class Universidad(models.Model):
    nombre_normalizado = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='logos_universidades/', null=True, blank=True)
    color_primario = models.CharField(max_length=7, default='#1e40af')
    color_secundario = models.CharField(max_length=7, default='#3b82f6')

    def __str__(self):
        return self.nombre_normalizado