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

    user = request.user

    # Boss view
    if user.is_superuser:

        employees = Employee.objects.all()
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

        return render(request, 'dashboard/dashboard.html', {
            'data': data,
            'is_boss': True
        })

    # Employee view
    else:

        tasks = EmployeeTask.objects.filter(employee__user=user)

        performance, total, completed, late = calculate_performance(tasks)

        return render(request, 'dashboard/dashboard.html', {
            'tasks': tasks,
            'total': total,
            'completed': completed,
            'late': late,
            'performance': performance,
            'is_boss': False
        })