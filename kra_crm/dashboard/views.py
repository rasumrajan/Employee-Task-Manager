from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db.models import F
from employees.models import Employee, Department
from tasks.models import TaskAssignment
from datetime import date, timedelta
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


# ================= DASHBOARD =================
@login_required
def dashboard(request):

    # ================= ADMIN =================
    if request.user.is_superuser:

        employees = Employee.objects.select_related('user', 'department')
        all_tasks = TaskAssignment.objects.select_related('employee__department')

        data = []

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

        # ================= KPI =================
        total_tasks = all_tasks.count()

        completed_tasks = all_tasks.filter(status__iexact='completed').count()
        pending_tasks = all_tasks.filter(status__iexact='pending').count()

        late_tasks = all_tasks.filter(
            status__iexact='completed',
            completed_at__gt=F('deadline')
        ).count()

        overall_performance = int(((completed_tasks - late_tasks) / total_tasks) * 100) if total_tasks > 0 else 0

        # ================= WEEKLY =================
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
                late_day = day_tasks.filter(completed_at__gt=F('deadline')).count()

                performance_day = int(((total_day - late_day) / total_day) * 100) if total_day > 0 else 0

                emp_data.append(performance_day)

            employee_chart_data.append({
                'name': emp.user.username,
                'data': emp_data
            })

        # ================= DEPARTMENT GRAPH =================
        dept_chart = []

        for dept in Department.objects.all():
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

            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'late_tasks': late_tasks,
            'performance': overall_performance,

            'dept_chart': dept_chart,
        })


    # ================= EMPLOYEE =================
    else:

        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return render(request, 'dashboard/employee_dashboard.html', {
                'task_data': [],
                'total': 0,
                'completed': 0,
                'late': 0,
                'performance': 0,
                'labels': [],
                'daily_performance': []
            })

        # ✅ IMPORTANT FIX (ONLY EMPLOYEE TASKS)
        tasks = TaskAssignment.objects.filter(employee=employee)

        performance, total, completed, late = calculate_performance(tasks)

        # ================= TASK DETAILS =================
        task_data = []

        for task in tasks:

            status = task.status
            assigned_on = task.assigned_at if task.assigned_at else None
            deadline = task.deadline

            # Pending Days
            if assigned_on and status.lower() != 'completed':
                pending_days = (date.today() - assigned_on.date()).days
            else:
                pending_days = 0

            # On Time
            if task.completed_at and deadline:
                on_time = task.completed_at <= deadline
            else:
                on_time = False

            # Performance
            if status.lower() == 'completed':
                task_performance = 100 if on_time else 50
            else:
                task_performance = 0

            task_data.append({
                "task": task,
                "status": status,
                "assigned_on": assigned_on,
                "deadline": deadline,
                "pending_days": pending_days,
                "on_time": "Yes" if on_time else "No",
                "performance": task_performance,
                "score": task_performance
            })

        # ================= WEEKLY =================
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
            late_day = day_tasks.filter(completed_at__gt=F('deadline')).count()

            performance_day = int(((total_day - late_day) / total_day) * 100) if total_day > 0 else 0

            labels.append(day.strftime("%d %b"))
            daily_performance.append(performance_day)

        return render(request, 'dashboard/employee_dashboard.html', {
            'task_data': task_data,
            'total': total,
            'completed': completed,
            'late': late,
            'performance': performance,
            'labels': labels,
            'daily_performance': daily_performance,
        })


# ================= DEPARTMENT VIEW =================
@login_required
def department_employees(request, dept_id):

    department = get_object_or_404(Department, id=dept_id)

    employees = Employee.objects.filter(department=department).select_related('user')

    data = []

    for emp in employees:
        tasks = TaskAssignment.objects.filter(employee=emp)

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