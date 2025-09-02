from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtro personalizado para acceder a valores de diccionario en templates
    Uso: {{ mi_diccionario|get_item:mi_llave }}
    """
    return dictionary.get(key, 0)

@register.filter
def get_item_rounded(dictionary, key):
    """
    Filtro para obtener valor y redondear a 4 decimales
    Uso: {{ probabilidades|get_item_rounded:ngrama }}
    """
    value = dictionary.get(key, 0)
    return round(value, 4) if isinstance(value, float) else value