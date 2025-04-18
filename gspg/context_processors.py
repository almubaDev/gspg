def user_magister(request):
    """
    Añade información del magíster del usuario al contexto de todas las plantillas.
    """
    context = {}
    if request.user.is_authenticated:
        # Usar el magister activo si existe
        if hasattr(request.user, 'active_magister') and request.user.active_magister:
            context['user_magister'] = request.user.active_magister
        # Mostrar el primer magister asociado como alternativa
        elif hasattr(request.user, 'magisteres') and request.user.magisteres.exists():
            context['user_magister'] = request.user.magisteres.first()
    return context


def user_magisteres(request):
    """
    Añade la lista de magisteres del usuario al contexto.
    """
    context = {}
    if request.user.is_authenticated and hasattr(request.user, 'magisteres'):
        context['user_magisteres'] = request.user.magisteres.all()
    return context