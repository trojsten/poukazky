from django import template

from poukazky import VERSION

register = template.Library()


@register.simple_tag
def app_version():
    return VERSION
