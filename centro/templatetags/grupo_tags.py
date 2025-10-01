from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter(name='not_in_group')
def not_in_group(user, group_name):
    return not user.groups.filter(name=group_name).exists()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})