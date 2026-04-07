from django.contrib import admin
from .models import TaskAssignment, TaskTimeLog


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):

    list_display = [
        "task",
        "employee",
        "status",
        "priority",
        "progress",
        "deadline",
        "is_overdue",
        "assigned_by",
    ]

    list_filter = [
        "status",
        "priority",
        "assigned_by",
        "deadline",
    ]

    search_fields = [
        "task__title",
        "employee__user__username",
    ]

    readonly_fields = [
        "assigned_date",
        "completed_at",
        "approved_at",
    ]

    def is_overdue(self, obj):
        return obj.is_overdue

    is_overdue.boolean = True
    is_overdue.short_description = "Overdue"

    def time_spent(self, obj):
        return obj.total_time_spent()

    time_spent.short_description = "Time Spent"


@admin.register(TaskTimeLog)
class TaskTimeLogAdmin(admin.ModelAdmin):

    list_display = [
        "employee_task",
        "start_time",
        "end_time",
        "duration_display"
    ]

    list_filter = [
        "start_time",
        "end_time",
    ]

    def duration_display(self, obj):
        duration = obj.duration()
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return "-"

    duration_display.short_description = "Duration"