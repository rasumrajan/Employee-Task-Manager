from django import forms
from django.contrib.auth.models import User
from .models import Employee, UserProfile
from django.contrib.auth.forms import PasswordChangeForm


class EmployeeForm(forms.ModelForm):

    #  User fields
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Leave blank to keep current password"
    )

    #  Employee fields
    class Meta:
        model = Employee
        fields = [
            'emp_id',
            'department',
            'designation',
            'phone',
            'join_date',
            'role',
            'status',
            'profile_image'
        ]

        widgets = {
            'emp_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'join_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    #  Load existing data in edit mode
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username

    #  Validate Employee ID (handle update case)
    def clean_emp_id(self):
        emp_id = self.cleaned_data.get('emp_id')

        qs = Employee.objects.filter(emp_id=emp_id)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Employee ID already exists")

        return emp_id
    
    def clean_username(self):
        username = self.cleaned_data.get('username')

        qs = User.objects.filter(username=username)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise forms.ValidationError("Username already exists")

        return username

    #  Save user + employee together
    def save(self, commit=True):
        employee = super().save(commit=False)

        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        # Create or update user
        if not employee.pk:
            user = User.objects.create_user(username=username, password=password)
            employee.user = user
        else:
            user = employee.user
            user.username = username

            if password:
                user.set_password(password)

            user.save()

        if commit:
            employee.save()

        return employee
    
class EmployeePasswordChangeForm(PasswordChangeForm):

    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Current Password"
    )

    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="New Password"
    )

    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm Password"
    )
    
class EmployeeProfileImageForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['profile_image']

        widgets = {
            'profile_image': forms.FileInput(attrs={'class': 'form-control'})
        }
        
class AdminProfileImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_image']