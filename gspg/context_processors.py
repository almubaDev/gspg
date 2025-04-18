def user_magister(request):
    """
    Añade información del magíster del usuario al contexto de todas las plantillas.
    """
    context = {}
    if request.user.is_authenticated and hasattr(request.user, 'magister') and request.user.magister:
        context['user_magister'] = request.user.magister
    return context