from datetime import timedelta

from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import F

from .models import Employee
from .forms import EmployeeForm
from tasks.models import TaskAssignment


# ================= ADMIN CHECK =================
def is_admin(user):
    return user.is_superuser


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


# ================= ADD EMPLOYEE =================
@login_required
@user_passes_test(is_admin)
def add_employee(request):

    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                form.save()   

                messages.success(request, "Employee created successfully")
                return redirect('employee_list')

            except Exception as e:
                form.add_error(None, str(e))

    else:
        form = EmployeeForm()

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

    form = EmployeeForm(request.POST or None, instance=employee)

    if form.is_valid():
        employee = form.save()

        password = form.cleaned_data.get('password')
        if password:
            employee.user.set_password(password)
            employee.user.save()

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

    employee.user.delete()

    messages.success(request, "Employee deleted successfully")
    return redirect('employee_list')


# ================= EMPLOYEE DASHBOARD =================
@login_required
def employee_dashboard(request):

    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return render(request, 'employees/dashboard.html', {
            'error': 'Employee profile not found'
        })

    # ================= TASK QUERY =================
    tasks = TaskAssignment.objects.filter(employee=employee)

    # FILTER (optional)
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # ================= BASIC STATS =================
    total_tasks = tasks.count()

    completed_tasks = tasks.filter(status__iexact='completed').count()

    pending_tasks = tasks.filter(
        status__in=['assigned', 'accepted', 'pending']
    ).count()

    in_progress_tasks = tasks.filter(
        status__in=['in_progress', 'paused']
    ).count()

    overdue_tasks = tasks.filter(
        deadline__lt=timezone.now(),
        status__in=['assigned', 'accepted', 'in_progress', 'paused']
    ).count()

    # ================= PERFORMANCE =================
    performance, total, completed, late = calculate_performance(tasks)

    # ================= RECENT TASKS =================
    recent_tasks = tasks.order_by('-assigned_date')[:10]

    # ================= DAILY ANALYTICS =================
    today = timezone.now().date()

    today_tasks = tasks.filter(assigned_date__date=today).count()

    today_completed = tasks.filter(
        status='completed',
        completed_at__date=today
    ).count()

    today_pending = tasks.filter(
        assigned_date__date=today
    ).exclude(status='completed').count()

    # ================= WEEKLY ANALYTICS =================
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    weekly_labels = []
    weekly_completed_data = []

    for day in last_7_days:
        count = tasks.filter(
            status='completed',
            completed_at__date=day
        ).count()

        weekly_labels.append(day.strftime("%d %b"))
        weekly_completed_data.append(count)

    # ================= CHART DATA =================
    chart_labels = ['Completed', 'Pending', 'In Progress', 'Overdue']

    chart_data = [
        completed_tasks,
        pending_tasks,
        in_progress_tasks,
        overdue_tasks
    ]

    return render(request, 'employees/dashboard.html', {

        # BASIC STATS
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'overdue_tasks': overdue_tasks,

        # PERFORMANCE
        'performance': performance,

        # TASKS
        'recent_tasks': recent_tasks,

        # MAIN CHART
        'chart_labels': chart_labels,
        'chart_data': chart_data,

        #  DAILY ANALYTICS
        'today_tasks': today_tasks,
        'today_completed': today_completed,
        'today_pending': today_pending,

        # WEEKLY ANALYTICS
        'weekly_labels': weekly_labels,
        'weekly_completed_data': weekly_completed_data,
    })
    
@login_required
def manager_dashboard(request):

    try:
        manager = request.user.employee
    except Employee.DoesNotExist:
        return redirect('dashboard')

    #  ROLE CHECK
    if manager.role != "manager":
        return redirect('dashboard')

    department = manager.department

    #  FETCH DATA
    employees = Employee.objects.filter(
        department=department
    ).select_related('user')

    tasks = TaskAssignment.objects.filter(
        employee__department=department
    ).select_related('employee__user')

    # ================= KPI =================
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

    # ================= EMPLOYEE PERFORMANCE =================
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

    # ================= 🔥 FINAL RANK + MEDAL =================

    # SORT BY PERFORMANCE
    data.sort(key=lambda x: x['performance'], reverse=True)

    # FORCE MEDAL (NO FAIL CASE)
    for i, item in enumerate(data):

        if i == 0:
            item['medal'] = "🥇"
        elif i == 1:
            item['medal'] = "🥈"
        elif i == 2:
            item['medal'] = "🥉"
        else:
            item['medal'] = str(i + 1)

    # 🏆 TOP PERFORMER
    top_performer = data[0] if data else None

    
    return render(request, 'employees/manager_dashboard.html', {
        'department': department,
        'data': data,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'late_tasks': late_tasks,
        'performance': performance,

        'top_performer': top_performer,
    })