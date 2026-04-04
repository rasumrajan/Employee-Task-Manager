from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import F
from employees.models import Employee
from tasks.models import EmployeeTask
from datetime import timedelta
from django.utils import timezone


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


@login_required
def dashboard(request):

    # ================= ADMIN =================
    if request.user.is_superuser:

        employees = Employee.objects.select_related('user').all()
        data = []

        # -------- Table Data --------
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

        # ================= WEEKLY COMPARISON =================
        today = timezone.now().date()

        chart_labels = []
        employee_chart_data = []

        # Labels (last 7 days)
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            chart_labels.append(day.strftime("%d %b"))

        # Each employee line
        for emp in employees:

            emp_tasks = EmployeeTask.objects.filter(employee=emp)
            emp_data = []

            for i in range(6, -1, -1):
                day = today - timedelta(days=i)

                day_tasks = emp_tasks.filter(
                    completed_at__date=day,
                    status='completed'
                )

                total_day = day_tasks.count()
                late_day = day_tasks.filter(
                    completed_at__gt=F('deadline')
                ).count()

                if total_day == 0:
                    performance_day = 0
                else:
                    performance_day = int(((total_day - late_day) / total_day) * 100)

                emp_data.append(performance_day)

            employee_chart_data.append({
                'name': emp.user.username,
                'data': emp_data
            })

        return render(request, 'dashboard/admin_dashboard.html', {
            'data': data,
            'chart_labels': chart_labels,
            'employee_chart_data': employee_chart_data
        })


    # ================= EMPLOYEE =================
    else:

        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return render(request, 'dashboard/employee_dashboard.html', {
                'tasks': [],
                'total': 0,
                'completed': 0,
                'late': 0,
                'performance': 0,
                'labels': [],
                'daily_performance': []
            })

        tasks = EmployeeTask.objects.filter(employee=employee)

        # -------- Performance --------
        performance, total, completed, late = calculate_performance(tasks)

        # ================= WEEKLY DATA =================
        today = timezone.now().date()

        labels = []
        daily_performance = []

        for i in range(6, -1, -1):
            day = today - timedelta(days=i)

            day_tasks = tasks.filter(
                completed_at__date=day,
                status='completed'
            )

            total_day = day_tasks.count()
            late_day = day_tasks.filter(
                completed_at__gt=F('deadline')
            ).count()

            if total_day == 0:
                performance_day = 0
            else:
                performance_day = int(((total_day - late_day) / total_day) * 100)

            labels.append(day.strftime("%d %b"))
            daily_performance.append(performance_day)

        return render(request, 'dashboard/employee_dashboard.html', {
            'tasks': tasks,
            'total': total,
            'completed': completed,
            'late': late,
            'performance': performance,
            'labels': labels,
            'daily_performance': daily_performance,
        })