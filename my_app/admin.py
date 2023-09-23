# файл создан руками
from django.contrib import admin

from . import models


admin.site.register(models.ChemistryEquipment)
admin.site.register(models.RequestService)
admin.site.register(models.Requests)
admin.site.register(models.Users)