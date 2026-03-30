from django.shortcuts import render, redirect
from .forms import EmployeeForm
from django.contrib.auth.models import User

# Create your views here.
def add_employee(request):

    form = EmployeeForm(request.POST or None)

    if form.is_valid():

        # Create user
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )

        # Create employee
        employee = form.save(commit=False)
        employee.user = user
        employee.save()

        return redirect('dashboard')
