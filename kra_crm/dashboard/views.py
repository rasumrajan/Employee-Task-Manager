from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import F
from employees.models import Employee
from tasks.models import EmployeeTask


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


@login_required
def dashboard(request):

    # ADMIN DASHBOARD
    if request.user.is_superuser:

        employees = Employee.objects.all()
        data = []

        for emp in employees:
            tasks = EmployeeTask.objects.filter(employee=emp)

            total = tasks.count()
            completed = tasks.filter(status='completed').count()
            late = sum(1 for t in tasks if t.is_late())

            performance = int((completed / total) * 100) if total > 0 else 0

            data.append({
                'employee': emp,
                'total': total,
                'completed': completed,
                'late': late,
                'performance': performance
            })

        return render(request, 'dashboard/admin_dashboard.html', {'data': data})

    # EMPLOYEE DASHBOARD
    else:

        employee = Employee.objects.get(user=request.user)
        tasks = EmployeeTask.objects.filter(employee=employee)

        total = tasks.count()
        completed = tasks.filter(status='completed').count()
        late = sum(1 for t in tasks if t.is_late())

        performance = int((completed / total) * 100) if total > 0 else 0

        return render(request, 'dashboard/employee_dashboard.html', {
            'tasks': tasks,
            'total': total,
            'completed': completed,
            'late': late,
            'performance': performance
        })