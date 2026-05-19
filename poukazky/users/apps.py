from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "poukazky.users"
    label = "poukazky_users"
    verbose_name = "Users"
