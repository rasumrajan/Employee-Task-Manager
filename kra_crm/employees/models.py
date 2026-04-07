from django.db import models
from django.contrib.auth.models import User
from department.models import Department


class Employee(models.Model):

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    #  User Link
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    #  Basic Info
    emp_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    designation = models.CharField(max_length=100)

    phone = models.CharField(max_length=20, blank=True, null=True)

    join_date = models.DateField()

    #  New Professional Fields
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    profile_image = models.ImageField(upload_to='employees/', blank=True, null=True)

    #  Helper Methods
    def __str__(self):
        return f"{self.user.username} ({self.emp_id})"

    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()