from django.db import models
from django.contrib.auth.models import User
from department.models import Department


class Employee(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    designation = models.CharField(max_length=100)

    phone = models.CharField(max_length=20, blank=True, null=True)

    join_date = models.DateField()

    def __str__(self):
        return self.user.username