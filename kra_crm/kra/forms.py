from django import forms
from .models import KRACategory, KRATask


#  CATEGORY FORM
class KRACategoryForm(forms.ModelForm):

    class Meta:
        model = KRACategory
        fields = ['name', 'department', 'description']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),

            'department': forms.Select(attrs={
                'class': 'form-control'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description'
            }),
        }


#  TASK FORM
class KRATaskForm(forms.ModelForm):

    class Meta:
        model = KRATask
        fields = [
            'category',
            'title',
            'description',
            'frequency',
            'expected_minutes',
            'max_score'
        ]

        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),

            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter task description'
            }),

            'frequency': forms.Select(attrs={
                'class': 'form-control'
            }),

            'expected_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Expected time in minutes'
            }),

            'max_score': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
        }