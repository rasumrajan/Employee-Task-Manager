from django import forms
from datetime import timedelta
from .models import KRACategory, KRATask


# ================= CATEGORY FORM =================
class KRACategoryForm(forms.ModelForm):

    class Meta:
        model = KRACategory
        fields = ['name', 'department', 'description', 'status']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


# ================= TASK FORM =================
class KRATaskForm(forms.ModelForm):

    days = forms.IntegerField(required=False, min_value=0)
    hours = forms.IntegerField(required=False, min_value=0)
    minutes = forms.IntegerField(required=False, min_value=0)

    class Meta:
        model = KRATask
        fields = [
            'category',
            'title',
            'description',
            'frequency',
            'max_score'
        ]

    def clean(self):
        cleaned_data = super().clean()

        days = cleaned_data.get('days') or 0
        hours = cleaned_data.get('hours') or 0
        minutes = cleaned_data.get('minutes') or 0

        if days == 0 and hours == 0 and minutes == 0:
            raise forms.ValidationError("Enter duration")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.expected_duration = timedelta(
            days=self.cleaned_data.get('days') or 0,
            hours=self.cleaned_data.get('hours') or 0,
            minutes=self.cleaned_data.get('minutes') or 0
        )

        if commit:
            instance.save()

        return instance