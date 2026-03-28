from django.db import models
from department.models import Department


class KRACategory(models.Model):

    name = models.CharField(max_length=200)

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="kra_categories"
    )

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
      
# KRA Task Template

class KRATask(models.Model):

    category = models.ForeignKey(
        KRACategory,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    title = models.CharField(max_length=255)

    description = models.TextField()

    frequency = models.CharField(
        max_length=20,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly")
        ]
    )

    expected_minutes = models.IntegerField()

    max_score = models.IntegerField(default=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title