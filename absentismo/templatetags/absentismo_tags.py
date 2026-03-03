from django import template
register = template.Library()

@register.filter
def attr(obj, nombre):
    return getattr(obj, nombre, False)

@register.filter
def get_item(dictionary, key):
    """
    Permite acceder a un dict con clave dinámica en las plantillas Django.
    Uso: {{ my_dict|get_item:variable_key }}
    Devuelve False si la clave no existe, lo que es seguro para {% if %}.
    """
    return dictionary.get(key, False)