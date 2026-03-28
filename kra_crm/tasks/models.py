from datetime import timedelta
from django.utils import timezone
from django.db import models
from employees.models import Employee
from kra.models import KRATask
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class EmployeeTask(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("carry_forward", "Carry Forward"),
        ("not_done", "Not Done"),
        ("department_delay", "Department Delay"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="tasks")
    task = models.ForeignKey(KRATask, on_delete=models.CASCADE)

    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_tasks")

    assigned_date = models.DateField(auto_now_add=True)
    deadline = models.DateTimeField(db_index=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending", db_index=True)

    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    score = models.IntegerField(default=0)

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_date']

    def save(self, *args, **kwargs):

        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()

        if self.status != 'completed':
            self.completed_at = None

        if self.status == 'completed':
            if self.completed_at and self.completed_at <= self.deadline:
                self.score = 100
            else:
                self.score = 50
        else:
            self.score = 0

        super().save(*args, **kwargs)

    def is_late(self):
        if self.completed_at:
            return self.completed_at > self.deadline
        return timezone.now() > self.deadline

    def total_time_spent(self):
        logs = self.time_logs.only('start_time', 'end_time')
        total_duration = timedelta()

        for log in logs:
            if log.end_time:
                total_duration += log.end_time - log.start_time
            else:
                total_duration += timezone.now() - log.start_time

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