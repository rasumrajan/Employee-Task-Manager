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

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="tasks")
    task = models.ForeignKey(KRATask, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE)

    rejection_reason = models.TextField(null=True, blank=True)
    is_resubmitted = models.BooleanField(default=False)

    assigned_date = models.DateTimeField(auto_now_add=True)

    #  NEW FIELDS
    completion_note = models.TextField(blank=True, null=True)
    is_candidate = models.BooleanField(default=False)

    deadline = models.DateTimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

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
            pass

        elif self.status == 'done':
            self.progress = 90

            # IMPORTANT FIX
            if not self.completed_at:
                self.completed_at = timezone.now()

        elif self.status == 'completed':
            self.progress = 100

            # DO NOT set completed_at here
            # only set approved_at
            if not self.approved_at:
                self.approved_at = timezone.now()

        super().save(*args, **kwargs)

    # ================= TIME =================
    @property
    def total_duration(self):
        logs = self.time_logs.all()
        total = timedelta()

        for log in logs:
            if log.end_time:
                total += (log.end_time - log.start_time)

        return total

    @property
    def expected_hours(self):
        if self.task and self.task.expected_duration:
            return round(self.task.expected_duration.total_seconds() / 3600, 2)
        return 0

    @property
    def actual_hours(self):
        total = 0
        for log in self.time_logs.all():
            if log.end_time:
                total += (log.end_time - log.start_time).total_seconds()
        return round(total / 3600, 2)

    @property
    def rework_hours(self):
        total = 0
        for log in self.time_logs.all():
            if log.end_time and log.is_rework:
                total += (log.end_time - log.start_time).total_seconds()
        return round(total / 3600, 2)

    @property
    def efficiency(self):
        expected = self.expected_hours
        actual = self.actual_hours

        if expected > 0 and actual > 0:
            return round(min((expected / actual) * 100, 150), 1)
        return 0

    @property
    def efficiency_score(self):
        eff = self.efficiency
        if eff >= 100:
            return "Excellent"
        elif eff >= 80:
            return "Good"
        elif eff >= 50:
            return "Average"
        return "Poor"

    # ================= TIME FORMAT =================
    @property
    def formatted_duration(self):
        duration = self.total_duration
        if not duration:
            return "-"

        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    # ================= LATE =================
    def is_late(self):
        if self.is_candidate:
            return False  #  NO penalty for candidates

        if self.completed_at and self.deadline:
            return self.completed_at > self.deadline

        return False

    def delay(self):
        if self.is_late():
            diff = self.completed_at - self.deadline
            hours = diff.total_seconds() // 3600
            return f"{int(hours)} hrs delay"
        return "On Time"

    # ================= PERFORMANCE =================
    def performance_score(self):

    # Ignore incomplete tasks
        if self.status not in ['done', 'completed']:
            return 0

        # Candidate = always good
        if self.is_candidate:
            return 100

        # ================= EFFICIENCY =================
        efficiency = self.efficiency

        #  FIX: If no time logs → give neutral score (not 0)
        if efficiency == 0:
            efficiency = 80   # neutral baseline

        # ================= TIME DISCIPLINE =================
        if self.is_late():
            time_score = -20
        else:
            time_score = 30

        # ================= REWORK =================
        actual = self.actual_hours
        rework = self.rework_hours

        if actual > 0:
            rework_ratio = rework / actual
            rework_penalty = min(rework_ratio * 50, 30)
        else:
            rework_penalty = 0

        # ================= FINAL SCORE =================
        score = (efficiency * 0.6) + time_score - rework_penalty

        #  FIX: Prevent negative score
        score = max(score, 0)

        return round(score, 2)
    
    #================get employee score===========
    def get_employee_score(employee):

        tasks = TaskAssignment.objects.filter(
            employee=employee,
            status__in=['done', 'completed']
        )

        total_tasks = tasks.count()

        if total_tasks < 5:
            return 0  # important filter

        total_score = sum(t.performance_score() for t in tasks)

        avg_score = total_score / total_tasks

        return round(avg_score, 2)

    # ================= OVERDUE =================
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
    
class TaskComment(models.Model):
    task = models.ForeignKey(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}: {self.message[:20]}"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(TaskAssignment, on_delete=models.CASCADE)

    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message}"