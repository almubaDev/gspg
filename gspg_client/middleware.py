from gspg.models import Magister
from gspg_client.models import Universidad
from gspg.context_processors import normalizar_nombre

class UniversidadConfigMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Configurar colores y logo antes de procesar la vista
        self.configure_universidad(request)
        
        # Procesar la vista
        response = self.get_response(request)
        
        return response
    
    def configure_universidad(self, request):
        """Configura los colores y logo de la universidad en la sesión."""
        # Solo aplicar si hay un tipo de usuario en la sesión
        if not request.session.get('tipo'):
            return
            
        # Recuperar el magister según el tipo de usuario
        magister = None
        if request.session.get('tipo') == 'profesor':
            from gspg.models import Profesor
            profesor_id = request.session.get('id')
            if profesor_id:
                try:
                    profesor = Profesor.objects.get(id=profesor_id)
                    # Intentar obtener el magister del primer grupo del profesor
                    grupo = profesor.grupos_trabajo.select_related('magister').first()
                    if grupo:
                        magister = grupo.magister
                except Profesor.DoesNotExist:
                    pass
                    
        elif request.session.get('tipo') == 'estudiante':
            from gspg.models import Estudiante
            estudiante_id = request.session.get('id')
            if estudiante_id:
                try:
                    estudiante = Estudiante.objects.select_related('intake__magister').get(id=estudiante_id)
                    magister = estudiante.intake.magister
                except Estudiante.DoesNotExist:
                    pass
        
        # Si encontramos un magister, configurar colores y logo
        if magister and magister.university:
            nombre_normalizado = normalizar_nombre(magister.university)
            universidad = Universidad.objects.filter(nombre_normalizado=nombre_normalizado).first()
            
            if universidad:
                request.session['color_primario'] = universidad.color_primario
                request.session['color_secundario'] = universidad.color_secundario
                request.session['logo_url'] = universidad.logo.url if universidad.logo and universidad.logo.name else None
            else:
                # Valores por defecto
                request.session['color_primario'] = '#1e40af'
                request.session['color_secundario'] = '#3b82f6'
                request.session['logo_url'] = None