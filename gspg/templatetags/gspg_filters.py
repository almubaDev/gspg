from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtiene un item de un diccionario por su clave"""
    return dictionary.get(key, {})

@register.filter
def asistencia_color(porcentaje):
    """Determina el color según el porcentaje de asistencia"""
    if porcentaje >= 85:
        return "success"
    elif porcentaje >= 70:
        return "info"
    elif porcentaje >= 50:
        return "warning"
    else:
        return "danger"