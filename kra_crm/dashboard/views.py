from django.shortcuts import get_object_or_404, render
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


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import F
from employees.models import Employee, Department
from tasks.models import EmployeeTask
from datetime import timedelta
from django.utils import timezone


# ================= PERFORMANCE FUNCTION =================
def calculate_performance(tasks):
    total = tasks.count()

    completed = tasks.filter(status__iexact='completed').count()

    late = tasks.filter(
        status__iexact='completed',
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

        employees = Employee.objects.select_related('user', 'department')
        all_tasks = EmployeeTask.objects.select_related('employee__department')

        data = []

        # -------- TABLE DATA --------
        for emp in employees:
            tasks = all_tasks.filter(employee=emp)

            performance, total, completed, late = calculate_performance(tasks)

            data.append({
                'employee': emp,
                'total': total,
                'completed': completed,
                'late': late,
                'performance': performance
            })

        # ================= KPI CALCULATION =================
        total_tasks = all_tasks.count()

        completed_tasks = all_tasks.filter(status__iexact='completed').count()
        pending_tasks = all_tasks.filter(status__iexact='pending').count()

        late_tasks = all_tasks.filter(
            status__iexact='completed',
            completed_at__gt=F('deadline')
        ).count()

        if total_tasks > 0:
            overall_performance = int(((completed_tasks - late_tasks) / total_tasks) * 100)
        else:
            overall_performance = 0

        # ================= WEEKLY COMPARISON =================
        today = timezone.now().date()

        chart_labels = []
        employee_chart_data = []

        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            chart_labels.append(day.strftime("%d %b"))

        for emp in employees:

            emp_tasks = all_tasks.filter(employee=emp)
            emp_data = []

            for i in range(6, -1, -1):
                day = today - timedelta(days=i)

                day_tasks = emp_tasks.filter(
                    completed_at__date=day,
                    status__iexact='completed'
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

        # ================= DEPARTMENT GRAPH =================
        dept_chart = []

        departments = Department.objects.all()

        for dept in departments:
            dept_tasks = all_tasks.filter(employee__department=dept)

            completed = dept_tasks.filter(status__iexact='completed').count()
            pending = dept_tasks.filter(status__iexact='pending').count()

            late = dept_tasks.filter(
                status__iexact='completed',
                completed_at__gt=F('deadline')
            ).count()

            dept_chart.append({
                "id": dept.id,
                "name": dept.name,
                "completed": completed,
                "pending": pending,
                "late": late
            })

        return render(request, 'dashboard/admin_dashboard.html', {
            'data': data,
            'chart_labels': chart_labels,
            'employee_chart_data': employee_chart_data,

            # KPI
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'late_tasks': late_tasks,
            'performance': overall_performance,

            # Department Graph
            'dept_chart': dept_chart,
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

        performance, total, completed, late = calculate_performance(tasks)

        today = timezone.now().date()

        labels = []
        daily_performance = []

        for i in range(6, -1, -1):
            day = today - timedelta(days=i)

            day_tasks = tasks.filter(
                completed_at__date=day,
                status__iexact='completed'
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
        
#=======Department View Employee============
@login_required
def department_employees(request, dept_id):

    department = get_object_or_404(Department, id=dept_id)

    employees = Employee.objects.filter(department=department).select_related('user')

    data = []

    for emp in employees:
        tasks = EmployeeTask.objects.filter(employee=emp)

        total = tasks.count()
        completed = tasks.filter(status__iexact='completed').count()

        late = tasks.filter(
            status__iexact='completed',
            completed_at__gt=F('deadline')
        ).count()

        performance = int(((completed - late) / total) * 100) if total > 0 else 0

        data.append({
            'employee': emp,
            'total': total,
            'completed': completed,
            'late': late,
            'performance': performance
        })

    return render(request, 'dashboard/department_employees.html', {
        'department': department,
        'data': data
    })