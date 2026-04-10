from django.db import models
from django.utils import timezone
from datetime import timedelta

from employees.models import Employee
from kra.models import KRATask
from django.contrib.auth.models import User


class TaskAssignment(models.Model):

    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('paused', 'Paused'),
        ('done', 'Done (Waiting Approval)'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    task = models.ForeignKey(
        KRATask,
        on_delete=models.CASCADE
    )

    assigned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    rejection_reason = models.TextField(null=True, blank=True)
    is_resubmitted = models.BooleanField(default=False)
    assigned_date = models.DateTimeField(auto_now_add=True)

    deadline = models.DateTimeField()

    #  DEFAULT SHOULD BE 'assigned'
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='assigned'
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    progress = models.IntegerField(default=0)
    remarks = models.TextField(blank=True, null=True)

    start_time = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_tasks'
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    # ================= SAVE LOGIC =================
    def save(self, *args, **kwargs):

        #  STATUS BASED PROGRESS CONTROL
        if self.status == 'assigned':
            self.progress = 0

        elif self.status == 'accepted':
            self.progress = 5

        elif self.status == 'in_progress':
            if not self.start_time:
                self.start_time = timezone.now()

            if self.progress < 10:
                self.progress = 10

        elif self.status == 'paused':
            pass  # keep same progress

        elif self.status == 'done':
            self.progress = 90

        elif self.status == 'completed':
            self.progress = 100

            if not self.completed_at:
                self.completed_at = timezone.now()

            if not self.approved_at:
                self.approved_at = timezone.now()

        super().save(*args, **kwargs)

    # ================= TIME CALCULATION =================
    
    @property
    def total_duration(self):
        logs = self.time_logs.all()
        total = timedelta()

        for log in logs:
            if log.end_time:
                total += (log.end_time - log.start_time)

        return total


# ================= FORMATTED TIME (NEW) =================
    @property
    def formatted_duration(self):
        duration = self.total_duration

        if not duration:
            return "-"

        total_seconds = int(duration.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    # ================= LATE CHECK =================
    def is_late(self):
        if self.completed_at and self.deadline:
            return self.completed_at > self.deadline
        return False

    # ================= DELAY =================
    def delay(self):
        if self.completed_at and self.deadline:
            diff = self.completed_at - self.deadline

            if diff.total_seconds() > 0:
                hours = diff.total_seconds() // 3600
                return f"{int(hours)} hrs delay"

        return "On Time"

    # ================= PERFORMANCE =================
    def performance_score(self):
        if self.status != 'completed':
            return 0

        return 70 if self.is_late() else 100

    # ================= OVERDUE (FIXED) =================
    @property
    def is_overdue(self):
        return (
            self.deadline and
            self.status not in ['completed'] and
            self.deadline < timezone.now()
        )

    def __str__(self):
        return f"{self.employee.user.username} - {self.task.title}"


# ================= TIME LOG =================
class TaskTimeLog(models.Model):

    employee_task = models.ForeignKey(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name="time_logs"
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    is_rework = models.BooleanField(default=False)

    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None

    def __str__(self):
        return f"{self.employee_task} | {self.start_time}"