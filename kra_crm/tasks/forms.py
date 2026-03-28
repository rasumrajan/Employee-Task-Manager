from django import forms
from .models import EmployeeTask


class EmployeeTaskForm(forms.ModelForm):
    class Meta:
        model = EmployeeTask
        fields = ['employee', 'task', 'deadline', 'status', 'progress']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }