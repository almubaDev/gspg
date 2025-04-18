import os
from celery import Celery

# Configura la variable de entorno para la configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Usa la configuración de Django para Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carga las tareas automáticamente
app.autodiscover_tasks()

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    'check-reunion-notifications': {
        'task': 'whatsapp_bot.tasks.check_and_send_reunion_notifications',
        'schedule': 300.0,  # cada 5 minutos
    },
}