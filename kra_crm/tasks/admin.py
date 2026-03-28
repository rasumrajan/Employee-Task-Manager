from django.contrib import admin
from .models import EmployeeTask, TaskTimeLog


@admin.register(EmployeeTask)
class EmployeeTaskAdmin(admin.ModelAdmin):

    list_display = ["employee", "task", "status", "deadline", "time_spent", "progress"]

    def time_spent(self, obj):
        return obj.total_time_spent()

    time_spent.short_description = "Time Spent"


@admin.register(TaskTimeLog)
class TaskTimeLogAdmin(admin.ModelAdmin):

    list_display = ["employee_task", "start_time", "end_time"]