from django.contrib import admin

from kra.models import KRACategory, KRATask

# Register your models here.
@admin.register(KRACategory)
class KRACategoryAdmin(admin.ModelAdmin):

    list_display = ["name", "department", "created_at"]


@admin.register(KRATask)
class KRATaskAdmin(admin.ModelAdmin):
  list_display = ["title", "category", "frequency", "expected_minutes"]