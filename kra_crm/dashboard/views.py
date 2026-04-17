import json
from urllib import request
from django.db.models.functions import Lower, Trim
from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.utils import timezone
from datetime import date, timedelta
from employees.forms import AdminProfileImageForm, EmployeeProfileImageForm
from employees.models import Employee, Department, UserProfile
from tasks.models import TaskAssignment
from tasks.views import calculate_times, get_top_3_performers
from employees.forms import EmployeePasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q

#=========for reset password============================
@login_required
def change_password(request):

    if request.method == 'POST':
        form = EmployeePasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()

            #  important (keeps user logged in)
            update_session_auth_hash(request, user)

            return redirect('dashboard')

    else:
        form = EmployeePasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


#=========update profile image===========================
#  DYNAMIC FORM
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['profile_image']


@login_required
def update_profile_image(request):

    user = request.user

    # ================= EMPLOYEE =================
    if hasattr(user, 'employee'):
        employee = user.employee

        if request.method == 'POST':
            form = EmployeeProfileImageForm(
                request.POST,
                request.FILES,
                instance=employee
            )

            if form.is_valid():
                form.save()
                return redirect('dashboard')

        else:
            form = EmployeeProfileImageForm(instance=employee)

    # ================= ADMIN =================
    else:

        profile, created = UserProfile.objects.get_or_create(user=user)

        if request.method == 'POST':
            form = AdminProfileImageForm(
                request.POST,
                request.FILES,
                instance=profile
            )

            if form.is_valid():
                form.save()
                return redirect('dashboard')

        else:
            form = AdminProfileImageForm(instance=profile)

    return render(request, 'accounts/update_profile.html', {'form': form})

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
login_required
def dashboard(request):

    # ================= ADMIN =================
    if request.user.is_superuser:

        employees = Employee.objects.select_related('user', 'department')
        all_tasks = TaskAssignment.objects.select_related('employee__department')

        data = []

        # ================= EMPLOYEE PERFORMANCE =================
        for emp in employees:

            emp_tasks = all_tasks.filter(employee=emp)

            tasks_done = emp_tasks.filter(status__in=['done', 'completed'])
            total_tasks_done = tasks_done.count()
            total_all_tasks = emp_tasks.count()  #  FIX (for UI)

            #  FIXED PERFORMANCE (NO DIVISION ERROR + NO BLOCKING)
            if total_tasks_done > 0:
                scores = [t.performance_score() for t in tasks_done]
                performance = int(sum(scores) / len(scores))
            else:
                performance = 0

            completed = emp_tasks.filter(status__iexact='completed').count()

            late = emp_tasks.filter(
                status__iexact='completed',
                completed_at__gt=F('deadline')
            ).count()

            data.append({
                'employee': emp,
                'total': total_all_tasks,  #  FIXED
                'completed': completed,
                'late': late,
                'performance': performance
            })

        # ================= RANKING =================
        data.sort(key=lambda x: x['performance'], reverse=True)

        for i, item in enumerate(data):
            item['medal'] = ["🥇", "🥈", "🥉"][i] if i < 3 else str(i + 1)

        top_performer = data[0] if data else None
        top_performers = data[:3]

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

        # ================= TASKS FOR APPROVAL =================
        tasks = all_tasks.annotate(
            clean_status=Lower(Trim('status'))
        ).filter(
            clean_status='done'
        ).order_by('-assigned_date')

        all_tasks_history = all_tasks.order_by('-assigned_date')

        return render(request, 'dashboard/admin_dashboard.html', {
            'data': data,
            'top_performer': top_performer,
            'top_performers': top_performers,

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

            'departments': Department.objects.all(),

            'tasks': tasks,
            'all_tasks': all_tasks_history,
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

        data = []

        for emp in employees:

            emp_tasks = tasks.filter(employee=emp)
            tasks_done = emp_tasks.filter(status__in=['done', 'completed'])
            total_tasks_done = tasks_done.count()

            if total_tasks_done > 0:
                scores = [t.performance_score() for t in tasks_done]
                performance = int(sum(scores) / len(scores))
            else:
                performance = 0

            data.append({
                'employee': emp,
                'performance': performance
            })

        data.sort(key=lambda x: x['performance'], reverse=True)

        return render(request, 'employees/manager_dashboard.html', {
            'department': department,
            'data': data,
        })

    # ================= EMPLOYEE =================
    else:

        tasks = TaskAssignment.objects.filter(employee=employee)

        tasks_done = tasks.filter(status__in=['done', 'completed'])
        total_tasks_done = tasks_done.count()

        if total_tasks_done > 0:
            scores = [t.performance_score() for t in tasks_done]
            performance = int(sum(scores) / len(scores))
        else:
            performance = 0

        return render(request, 'dashboard/employee_dashboard.html', {
            'performance': performance,
            'task_data': tasks,
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
    
def task_chat_history(request):

    tasks = TaskAssignment.objects.select_related(
    'employee__user',
    'employee__department',
    'task'
    ).prefetch_related('comments__user').order_by('-assigned_date')

    #  FILTERS
    department_id = request.GET.get('department')
    employee_id = request.GET.get('employee')
    status = request.GET.get('status')
    search = request.GET.get('search')

    if department_id:
        tasks = tasks.filter(employee__department_id=department_id)

    if employee_id:
        tasks = tasks.filter(employee_id=employee_id)

    if status:
        tasks = tasks.filter(status__iexact=status)

    if search:
        tasks = tasks.filter(
            Q(employee__user__username__icontains=search) |
            Q(task__title__icontains=search)
        )

    return render(request, 'dashboard/task_chat_history.html', {
        'tasks': tasks,
        'departments': Department.objects.all(),
        'employees': Employee.objects.all(),

        # keep selected values
        'department_id': department_id,
        'employee_id': employee_id,
        'status': status,
        'search': search,
    })
    
def admin_dashboard(request):

    top_performers = get_top_3_performers()

    context = {
        "top_performers": top_performers
    }

    return render(request, "admin_dashboard.html", context)
