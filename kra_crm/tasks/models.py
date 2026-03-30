from datetime import timedelta
from django.utils import timezone
from django.db import models
from employees.models import Employee
from kra.models import KRATask
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class EmployeeTask(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("paused", "Paused"),
        ("done", "Done (Waiting Approval)"),
        ("completed", "Completed"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="tasks")
    task = models.ForeignKey(KRATask, on_delete=models.CASCADE)

    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_tasks")

    assigned_date = models.DateField(auto_now_add=True)
    deadline = models.DateTimeField()

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")

    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    score = models.IntegerField(default=0)

    completed_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    approved_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):

        # Progress logic
        if self.status == 'pending':
            self.progress = 0

        elif self.status == 'in_progress':
            if self.progress == 0:
                self.progress = 10

        elif self.status == 'done':
            self.progress = 90

        elif self.status == 'completed':
            self.progress = 100

        # Completion logic
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()

        if self.status != 'completed':
            self.completed_at = None

        super().save(*args, **kwargs)

    def clean(self):
        if self.status == 'completed' and self.progress < 100:
            raise ValidationError("Completed task must have 100% progress")

    def is_late(self):
        if self.completed_at:
            return self.completed_at > self.deadline
        return timezone.now() > self.deadline

    def total_time_spent(self):
        logs = self.time_logs.all()
        total_duration = timedelta()

        for log in logs:
            if log.end_time:
                total_duration += log.end_time - log.start_time

        total_seconds = int(total_duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        return f"{hours}h {minutes}m"

    def __str__(self):
        return f"{self.employee.user.username} - {self.task.title}"


class TaskTimeLog(models.Model):

    employee_task = models.ForeignKey(EmployeeTask, on_delete=models.CASCADE, related_name="time_logs")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None