from django import forms
from django.contrib.auth.models import User
from .models import Employee


class EmployeeForm(forms.ModelForm):

    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Employee
        fields = ['department', 'designation', 'phone', 'join_date']

        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'join_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }