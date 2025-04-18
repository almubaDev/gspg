def user_magister_context(request):
    """
    Añade tanto el magister activo como la lista de magisteres al contexto.
    """
    context = {}
    if request.user.is_authenticated:
        context['user_magister'] = getattr(request.user, 'active_magister', None)
        context['user_magisteres'] = getattr(request.user, 'magisteres', []).all()
    return context
