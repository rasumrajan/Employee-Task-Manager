from django.contrib import admin
from .models import KRACategory, KRATask


@admin.register(KRACategory)
class KRACategoryAdmin(admin.ModelAdmin):

    list_display = [
        "name",
        "department",
        "status",
        "created_at",
    ]

    list_filter = [
        "department",
        "status",
        "created_at",
    ]

    search_fields = [
        "name",
        "department__name",
    ]

    ordering = [
        "-created_at"
    ]


@admin.register(KRATask)
class KRATaskAdmin(admin.ModelAdmin):

    list_display = [
        "title",
        "category",
        "frequency",
        "expected_duration",
        "is_active",
    ]

    list_filter = [
        "category",
        "frequency",
        "is_active",
    ]

    search_fields = [
        "title",
        "category__name",
    ]

    ordering = [
        "-created_at"
    ]