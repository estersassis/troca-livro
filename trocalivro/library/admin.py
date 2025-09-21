from django.contrib import admin
from library.models import Profile, Book


# Registrando os modelos.
admin.site.register(Profile)
admin.site.register(Book)