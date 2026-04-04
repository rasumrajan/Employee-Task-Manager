from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import F
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Employee
from .forms import EmployeeForm
from tasks.models import EmployeeTask



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


# ================= DASHBOARD =================
@login_required
def dashboard(request):

    # ---------- ADMIN ----------
    if request.user.is_superuser:

        employees = Employee.objects.select_related('user').all()
        data = []

        for emp in employees:
            tasks = EmployeeTask.objects.filter(employee=emp)

            performance, total, completed, late = calculate_performance(tasks)

            data.append({
                'employee': emp,
                'total': total,
                'completed': completed,
                'late': late,
                'performance': performance
            })

        return render(request, 'dashboard/admin_dashboard.html', {'data': data})


    # ---------- EMPLOYEE ----------
    else:

        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return render(request, 'dashboard/employee_dashboard.html', {
                'tasks': [],
                'total': 0,
                'completed': 0,
                'late': 0,
                'performance': 0
            })

        tasks = EmployeeTask.objects.filter(employee=employee)

        performance, total, completed, late = calculate_performance(tasks)

        return render(request, 'dashboard/employee_dashboard.html', {
            'tasks': tasks,
            'total': total,
            'completed': completed,
            'late': late,
            'performance': performance
        })


# ================= ADMIN CHECK =================
def is_admin(user):
    return user.is_superuser


# ================= ADD EMPLOYEE =================
@login_required
@user_passes_test(is_admin)
def add_employee(request):

    form = EmployeeForm(request.POST or None)

    if form.is_valid():

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        # Prevent duplicate username
        if User.objects.filter(username=username).exists():
            form.add_error('username', 'Username already exists')

        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password
            )

            # Create employee
            employee = form.save(commit=False)
            employee.user = user
            employee.save()

            return redirect('dashboard')

    return render(request, 'employees/add_employee.html', {
        'form': form
    })
    
@login_required
@user_passes_test(is_admin)
def employee_list(request):

    employees = Employee.objects.select_related('user', 'department').all()

    return render(request, 'employees/employee_list.html', {
        'employees': employees
    })
    
@login_required
@user_passes_test(is_admin)
def update_employee(request, pk):

    employee = Employee.objects.get(pk=pk)

    form = EmployeeForm(request.POST or None, instance=employee)

    if form.is_valid():
        form.save()
        messages.success(request, "Employee update successfully")
        return redirect('employee_list')

    return render(request, 'employees/add_employee.html', {
        'form': form,
        'is_edit': True   # 
    })


@login_required
@user_passes_test(is_admin)
def delete_employee(request, pk):

    employee = Employee.objects.get(pk=pk)

    # Delete linked user also
    employee.user.delete()
    messages.success(request, "Employee Deleted Successfully")
    return redirect('employee_list')

