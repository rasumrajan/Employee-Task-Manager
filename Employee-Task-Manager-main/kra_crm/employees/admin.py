from django.contrib import admin

from employees.models import Employee

# Register your models here.
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    list_display = ["user", "department", "designation"]