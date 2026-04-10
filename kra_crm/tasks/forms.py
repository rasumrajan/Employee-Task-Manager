from django import forms
from django.utils import timezone
from .models import TaskAssignment
from kra.models import KRATask
from employees.models import Employee


# ================= ASSIGN TASK FORM =================
class TaskAssignForm(forms.ModelForm):

    class Meta:
        model = TaskAssignment
        fields = ['employee', 'task', 'deadline', 'priority']

        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-control'
            }),

            'task': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_task'
            }),

            'deadline': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),

            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

        labels = {
            'employee': 'Assign To',
            'task': 'Task Template',
            'deadline': 'Deadline',
            'priority': 'Priority',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Optimized queryset
        self.fields['task'].queryset = KRATask.objects.select_related('category')
        self.fields['employee'].queryset = Employee.objects.select_related('user')

        # UX labels
        self.fields['task'].empty_label = "Select Task"
        self.fields['employee'].empty_label = "Select Employee"

    # ================= VALIDATION =================
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')

        if deadline and deadline < timezone.now():
            raise forms.ValidationError("Deadline cannot be in the past")

        return deadline


# ================= UPDATE TASK FORM =================
class TaskUpdateForm(forms.ModelForm):

    class Meta:
        model = TaskAssignment
        fields = ['status', 'progress', 'remarks']

        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),

            'progress': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100
            }),

            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add remarks (optional)'
            }),
        }

        labels = {
            'status': 'Task Status',
            'progress': 'Progress (%)',
            'remarks': 'Remarks',
        }

    #  EXTRA VALIDATION (PRO LEVEL)
    def clean_progress(self):
        progress = self.cleaned_data.get('progress')

        if progress < 0 or progress > 100:
            raise forms.ValidationError("Progress must be between 0 and 100")

        return progress