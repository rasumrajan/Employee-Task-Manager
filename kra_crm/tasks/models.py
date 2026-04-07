from django.db import models
from django.utils import timezone
from datetime import timedelta

from employees.models import Employee
from kra.models import KRATask
from django.contrib.auth.models import User


class TaskAssignment(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("paused", "Paused"),
        ("done", "Done (Waiting Approval)"),
        ("completed", "Completed"),
    ]

    PRIORITY_CHOICES = [
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="tasks")
    task = models.ForeignKey(KRATask, on_delete=models.CASCADE)

    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_date = models.DateTimeField(auto_now_add=True)

    deadline = models.DateTimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium")

    progress = models.IntegerField(default=0)
    remarks = models.TextField(blank=True, null=True)

    start_time = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_tasks')
    approved_at = models.DateTimeField(null=True, blank=True)

    # ================= SAVE LOGIC =================
    def save(self, *args, **kwargs):

        if self.status == 'pending':
            self.progress = 0

        elif self.status == 'in_progress':
            if self.progress == 0:
                self.progress = 10

        elif self.status == 'done':
            self.progress = 90

        elif self.status == 'completed':
            self.progress = 100
            if not self.completed_at:
                self.completed_at = timezone.now()

        super().save(*args, **kwargs)

    # ================= CALCULATIONS =================

    def total_duration(self):
        logs = self.time_logs.all()
        total = timedelta()

        for log in logs:
            if log.end_time:
                total += log.end_time - log.start_time

        return total

    def is_late(self):
        if self.completed_at:
            return self.completed_at > self.deadline
        return False

    def delay(self):
        if self.completed_at and self.deadline:
            diff = self.completed_at - self.deadline

            if diff.total_seconds() > 0:
                hours = diff.total_seconds() // 3600
                return f"{int(hours)} hrs delay"

        return "On Time"

    def performance_score(self):
        if self.status != 'completed':
            return 0

        if self.is_late():
            return 70
        return 100

    def __str__(self):
        return f"{self.employee.user.username} - {self.task.title}"


class TaskTimeLog(models.Model):

    employee_task = models.ForeignKey(TaskAssignment, on_delete=models.CASCADE, related_name="time_logs")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None