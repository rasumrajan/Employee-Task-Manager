from django import forms
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
                'id': 'id_task'   # 🔥 IMPORTANT for JS
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

        #  Ensure dropdown loads properly
        self.fields['task'].queryset = KRATask.objects.select_related('category').all()

        self.fields['employee'].queryset = Employee.objects.select_related('user').all()

        #  UX improvements
        self.fields['task'].empty_label = "Select Task"
        self.fields['employee'].empty_label = "Select Employee"

    #  OPTIONAL VALIDATION (SAFE)
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')

        if deadline:
            from django.utils import timezone

            if deadline < timezone.now():
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
        
