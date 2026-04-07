from datetime import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import F
from django.contrib import messages

from .models import Employee
from .forms import EmployeeForm
from tasks.models import TaskAssignment


# ================= PERFORMANCE FUNCTION =================
def calculate_performance(tasks):

    total = tasks.count()

    completed = tasks.filter(status='completed').count()

    late = tasks.filter(
        status='completed',
        completed_at__gt=F('deadline')
    ).count()

    if total == 0:
        return 0, total, completed, late

    on_time = completed - late
    performance = int((on_time / total) * 100)

    return performance, total, completed, late


# ================= ADMIN CHECK =================
def is_admin(user):
    return user.is_superuser


# ================= ADD EMPLOYEE =================
@login_required
@user_passes_test(is_admin)
def add_employee(request):

    form = EmployeeForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Employee created successfully")
        return redirect('employee_list')

    return render(request, 'employees/add_employee.html', {
        'form': form
    })


# ================= EMPLOYEE LIST =================
@login_required
@user_passes_test(is_admin)
def employee_list(request):

    employees = Employee.objects.select_related('user', 'department').all()

    return render(request, 'employees/employee_list.html', {
        'employees': employees
    })


# ================= UPDATE EMPLOYEE =================
@login_required
@user_passes_test(is_admin)
def update_employee(request, pk):

    employee = get_object_or_404(Employee, pk=pk)

    form = EmployeeForm(request.POST or None, request.FILES or None, instance=employee)

    if form.is_valid():
        form.save()
        messages.success(request, "Employee updated successfully")
        return redirect('employee_list')

    return render(request, 'employees/add_employee.html', {
        'form': form,
        'is_edit': True
    })


# ================= DELETE EMPLOYEE =================
@login_required
@user_passes_test(is_admin)
def delete_employee(request, pk):

    employee = get_object_or_404(Employee, pk=pk)

    # Delete linked user also
    employee.user.delete()

    messages.success(request, "Employee deleted successfully")
    return redirect('employee_list')

#=====================Employee Dash===================
@login_required
def employee_dashboard(request):

    employee = request.user.employee
    tasks = TaskAssignment.objects.filter(employee=employee)

    # 🔹 Filters
    status_filter = request.GET.get('status')

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # 🔹 Stats
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    pending_tasks = tasks.filter(status='pending').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    overdue_tasks = tasks.filter(deadline__lt=timezone.now(), status__in=['pending', 'in_progress']).count()

    # 🔹 Performance
    performance, total, completed, late = calculate_performance(tasks)

    # 🔹 Recent Tasks
    recent_tasks = tasks.order_by('-assigned_date')[:10]

    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'overdue_tasks': overdue_tasks,
        'performance': performance,
        'recent_tasks': recent_tasks,
    }

    return render(request, 'employees/dashboard.html', context)