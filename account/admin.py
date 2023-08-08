from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(User)
admin.site.register(card_data)
admin.site.register(document_shared)
admin.site.register(email_configuration)