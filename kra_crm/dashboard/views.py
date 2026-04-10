import json
from urllib import request

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.utils import timezone
from datetime import date, timedelta

from employees.models import Employee, Department
from tasks.models import TaskAssignment
from tasks.views import calculate_times


# ================= PERFORMANCE FUNCTION =================
def calculate_times(task):
    total = 0
    rework = 0

    logs = task.time_logs.all()

    for log in logs:
        if log.end_time:
            duration = (log.end_time - log.start_time).total_seconds()

            total += duration

            if getattr(log, 'is_rework', False):
                rework += duration

    return {
        "total_hours": round(total / 3600, 2),
        "rework_hours": round(rework / 3600, 2),
        "actual_hours": round((total - rework) / 3600, 2)
    }

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

        # ================= EMPLOYEE PERFORMANCE =================
        for emp in employees:
            emp_tasks = all_tasks.filter(employee=emp)

            total = emp_tasks.count()
            completed = emp_tasks.filter(status__iexact='completed').count()

            late = emp_tasks.filter(
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

        # ================= RANKING =================
        data.sort(key=lambda x: x['performance'], reverse=True)

        for i, item in enumerate(data):
            if i == 0:
                item['medal'] = "🥇"
            elif i == 1:
                item['medal'] = "🥈"
            elif i == 2:
                item['medal'] = "🥉"
            else:
                item['medal'] = str(i + 1)

        top_performer = data[0] if data else None

        # ================= KPI =================
        total_tasks = all_tasks.count()

        completed_tasks = all_tasks.filter(status__iexact='completed').count()

        pending_tasks = all_tasks.filter(
            status__in=['assigned', 'accepted', 'in_progress', 'paused']
        ).count()

        late_tasks = all_tasks.filter(
            status__iexact='completed',
            completed_at__gt=F('deadline')
        ).count()

        performance = int(((completed_tasks - late_tasks) / total_tasks) * 100) if total_tasks > 0 else 0

        # ================= CHART DATA =================
        employee_labels = [d['employee'].user.username for d in data]
        employee_performance = [d['performance'] for d in data]

        dept_labels = []
        dept_completed = []
        dept_pending = []
        dept_late = []

        for dept in Department.objects.all():
            dept_tasks = all_tasks.filter(employee__department=dept)

            dept_labels.append(dept.name)

            dept_completed.append(
                dept_tasks.filter(status__iexact='completed').count()
            )

            dept_pending.append(
                dept_tasks.filter(
                    status__in=['assigned', 'accepted', 'in_progress', 'paused']
                ).count()
            )

            dept_late.append(
                dept_tasks.filter(
                    status__iexact='completed',
                    completed_at__gt=F('deadline')
                ).count()
            )

        # ================= FIX: TASKS FOR APPROVAL =================
        tasks = all_tasks.filter(status__iexact='done').order_by('-assigned_date')
        for t in tasks:
            times = calculate_times(t)
            t.total_hours = times["total_hours"]
            t.rework_hours = times["rework_hours"]
            t.actual_hours = times["actual_hours"]

        # ================= RETURN =================
        return render(request, 'dashboard/admin_dashboard.html', {
            'data': data,
            'top_performer': top_performer,

            # KPI
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'late_tasks': late_tasks,
            'performance': performance,

            # Charts
            'employee_labels': json.dumps(employee_labels),
            'employee_performance': json.dumps(employee_performance),

            'dept_labels': json.dumps(dept_labels),
            'dept_completed': json.dumps(dept_completed),
            'dept_pending': json.dumps(dept_pending),
            'dept_late': json.dumps(dept_late),

            # Departments
            'departments': Department.objects.all(),

            #  IMPORTANT FIXES
            'tasks': tasks,
            'now': timezone.now(),
        })

    # ================= ROLE BASE =================
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return redirect('login')

    # ================= MANAGER =================
    if employee.role == "manager":

        department = employee.department

        employees = Employee.objects.filter(department=department).select_related('user')
        tasks = TaskAssignment.objects.filter(employee__department=department)

        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status__iexact='completed').count()

        pending_tasks = tasks.filter(
            status__in=['assigned', 'accepted', 'in_progress', 'paused']
        ).count()

        late_tasks = tasks.filter(
            status__iexact='completed',
            completed_at__gt=F('deadline')
        ).count()

        performance = int(((completed_tasks - late_tasks) / total_tasks) * 100) if total_tasks > 0 else 0

        data = []

        for emp in employees:
            emp_tasks = tasks.filter(employee=emp)

            total = emp_tasks.count()
            completed = emp_tasks.filter(status__iexact='completed').count()

            late = emp_tasks.filter(
                status__iexact='completed',
                completed_at__gt=F('deadline')
            ).count()

            emp_performance = int(((completed - late) / total) * 100) if total > 0 else 0

            data.append({
                'employee': emp,
                'total': total,
                'completed': completed,
                'late': late,
                'performance': emp_performance
            })

        data.sort(key=lambda x: x['performance'], reverse=True)

        for i, item in enumerate(data):
            if i == 0:
                item['medal'] = "🥇"
            elif i == 1:
                item['medal'] = "🥈"
            elif i == 2:
                item['medal'] = "🥉"
            else:
                item['medal'] = str(i + 1)

        return render(request, 'employees/manager_dashboard.html', {
            'department': department,
            'data': data,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'late_tasks': late_tasks,
            'performance': performance,
        })

    # ================= EMPLOYEE =================
    else:

        tasks = TaskAssignment.objects.filter(employee=employee)
        for t in tasks:
            times = calculate_times(t)
            t.total_hours = times["total_hours"]
            t.rework_hours = times["rework_hours"]
            t.actual_hours = times["actual_hours"]

        total = tasks.count()
        completed = tasks.filter(status__iexact='completed').count()

        late = tasks.filter(
            status__iexact='completed',
            completed_at__gt=F('deadline')
        ).count()

        performance = int(((completed - late) / total) * 100) if total > 0 else 0

        today = timezone.now().date()

        today_tasks = tasks.filter(assigned_date__date=today)
        today_completed = tasks.filter(
            status__iexact='completed',
            completed_at__date=today
        )

        today_total = today_tasks.count()
        today_done = today_completed.count()

        today_late = today_completed.filter(
            completed_at__gt=F('deadline')
        ).count()

        today_performance = int(((today_done - today_late) / today_done) * 100) if today_done > 0 else 0

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
            'total': total,
            'completed': completed,
            'late': late,
            'performance': performance,
            'task_data': tasks,
            'labels': json.dumps(labels),
            'daily_performance': json.dumps(daily_performance),

            'today_total': today_total,
            'today_done': today_done,
            'today_late': today_late,
            'today_performance': today_performance,
        })
# ================= DEPARTMENT VIEW =================
@login_required
def department_employees(request, dept_id):

    department = get_object_or_404(Department, id=dept_id)

    #  All tasks of this department
    dept_tasks = TaskAssignment.objects.filter(
        employee__department=department
    ).select_related('employee__user')

    employees = Employee.objects.filter(
        department=department
    ).select_related('user')

    # ================= KPI =================
    total_tasks = dept_tasks.count()

    completed_tasks = dept_tasks.filter(status__iexact='completed').count()

    pending_tasks = dept_tasks.filter(
        status__in=['assigned', 'accepted', 'in_progress', 'paused']
    ).count()

    late_tasks = dept_tasks.filter(
        status__iexact='completed',
        completed_at__gt=F('deadline')
    ).count()

    performance = int(((completed_tasks - late_tasks) / total_tasks) * 100) if total_tasks > 0 else 0

    # ================= EMPLOYEE DATA =================
    data = []

    for emp in employees:
        tasks = dept_tasks.filter(employee=emp)

        total = tasks.count()
        completed = tasks.filter(status__iexact='completed').count()

        late = tasks.filter(
            status__iexact='completed',
            completed_at__gt=F('deadline')
        ).count()

        emp_performance = int(((completed - late) / total) * 100) if total > 0 else 0

        data.append({
            'employee': emp,
            'total': total,
            'completed': completed,
            'late': late,
            'performance': emp_performance
        })

    return render(request, 'dashboard/department_employees.html', {
        'department': department,
        'data': data,

        # KPI
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'late_tasks': late_tasks,
        'performance': performance,
    })
    
