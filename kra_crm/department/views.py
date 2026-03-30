from django.shortcuts import render, redirect, get_object_or_404
from .models import Department
from .forms import DepartmentForm


#  ADD DEPARTMENT
def add_department(request):
    form = DepartmentForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('department_list')

    return render(request, 'department/add_department.html', {
        'form': form
    })


#  LIST DEPARTMENTS
def department_list(request):
    departments = Department.objects.all()

    return render(request, 'department/department_list.html', {
        'departments': departments
    })


#  UPDATE DEPARTMENT
def update_department(request, pk):
    department = get_object_or_404(Department, pk=pk)

    form = DepartmentForm(request.POST or None, instance=department)

    if form.is_valid():
        form.save()
        return redirect('department_list')

    return render(request, 'department/add_department.html', {
        'form': form
    })


#  DELETE DEPARTMENT
def delete_department(request, pk):
    department = get_object_or_404(Department, pk=pk)

    department.delete()
    return redirect('department_list')