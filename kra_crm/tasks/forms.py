from django import forms
from .models import TaskAssignment
from kra.models import KRATask


class TaskAssignForm(forms.ModelForm):

    class Meta:
        model = TaskAssignment
        fields = ['employee', 'task', 'deadline', 'priority']

        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #  IMPORTANT FIX
        self.fields['task'].queryset = KRATask.objects.all()

        # Optional UX improvement
        self.fields['task'].empty_label = "Select Task"


# 🔹 Employee Update Form
class TaskUpdateForm(forms.ModelForm):

    class Meta:
        model = TaskAssignment
        fields = ['status', 'progress', 'remarks']