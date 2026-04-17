from django.db import models
from department.models import Department


# ================= KRA CATEGORY =================
class KRACategory(models.Model):

    name = models.CharField(max_length=200)

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="kra_categories"
    )

    description = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=10,
        choices=[('active', 'Active'), ('inactive', 'Inactive')],
        default='active'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'department')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.department.name})"


# ================= KRA TASK TEMPLATE =================
class KRATask(models.Model):

    FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    category = models.ForeignKey(
        KRACategory,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    title = models.CharField(max_length=255)

    description = models.TextField()

    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES
    )

    expected_duration = models.DurationField()

    max_score = models.PositiveIntegerField(default=100)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.category.name})"

    #  Helper Methods
    def expected_hours(self):
        return round(self.expected_minutes / 60, 2)
    
    def duration_display(self):
        total_seconds = self.expected_duration.total_seconds()
        hours = total_seconds // 3600
        days = hours // 24

        if days > 0:
            return f"{int(days)} days"
        elif hours > 0:
            return f"{int(hours)} hrs"
        else:
            minutes = total_seconds // 60
            return f"{int(minutes)} mins"