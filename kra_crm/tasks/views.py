from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.contrib import messages
from employees.models import Employee
from kra.models import KRATask
from .models import TaskAssignment, TaskTimeLog
from .forms import TaskAssignForm, TaskUpdateForm


# ================= HELPER FUNCTION =================
def get_user_task(request, task_id):
    task = get_object_or_404(TaskAssignment, id=task_id)
    if task.employee.user != request.user:
        return None
    return task


def calculate_total_minutes(task):
    total = 0
    for log in task.time_logs.all():
        if log.end_time:
            total += (log.end_time - log.start_time).total_seconds()
    return round(total / 60, 2)


# ================= ASSIGN TASK =================
@login_required
def assign_task(request):

    if not request.user.is_superuser:
        return redirect('dashboard')

    form = TaskAssignForm(request.POST or None)

    if form.is_valid():
        task = form.save(commit=False)
        task.assigned_by = request.user
        task.status = 'assigned'
        task.save()
        return redirect('all_tasks')

    return render(request, 'tasks/assign_task.html', {'form': form})


# ================= ADMIN: ALL TASKS =================
@login_required
def all_tasks(request):

    if not request.user.is_superuser:
        return redirect('dashboard')

    tasks = TaskAssignment.objects.select_related(
        'employee__user', 'task'
    ).all().order_by('-assigned_date')

    # ================= FILTER INPUT =================
    search = request.GET.get('search', '')
    status = request.GET.get('status')
    employee_id = request.GET.get('employee')

    if search:
        tasks = tasks.filter(
            Q(employee__user__username__icontains=search) |
            Q(task__title__icontains=search)
        )

    # ================= STATUS FILTER =================
    if status:

        if status == "late":
            tasks = tasks.filter(
                status='completed',
                completed_at__gt=F('deadline')
            )

        elif status == "pending":
            tasks = tasks.filter(
                status__in=['assigned', 'accepted', 'in_progress', 'paused']
            )

        elif status == "overdue":
            tasks = tasks.filter(
                deadline__lt=timezone.now(),
                status__in=['assigned', 'accepted', 'in_progress', 'paused']
            )

        elif status == "waiting_approval":
            tasks = tasks.filter(status='done')

        elif status == "approved":
            tasks = tasks.filter(status='completed')

        else:
            tasks = tasks.filter(status=status)

    # ================= EMPLOYEE FILTER =================
    if employee_id:
        tasks = tasks.filter(employee_id=employee_id)

    tasks = tasks.distinct()

    # ================= PAGINATION =================
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)

    # ================= ADD TIME =================
    for t in tasks:
        t.total_minutes = calculate_total_minutes(t)

    return render(request, 'tasks/all_tasks.html', {
        'tasks': tasks,
        'employees': Employee.objects.all(),
        'search': search,
        'status': status,
        'employee_id': employee_id,
    })


# ================= EMPLOYEE: MY TASKS =================
@login_required
def task_list(request):

    tasks = TaskAssignment.objects.filter(
        employee__user=request.user
    ).order_by('-assigned_date')

    for t in tasks:
        t.total_minutes = calculate_total_minutes(t)

    return render(request, 'tasks/task_list.html', {'tasks': tasks})


# ================= UPDATE TASK =================
@login_required
def update_task(request, pk):

    task = get_object_or_404(TaskAssignment, pk=pk)

    if task.employee.user != request.user and not request.user.is_superuser:
        return redirect('dashboard')

    # prevent editing completed tasks
    if task.status == 'completed':
        return redirect('dashboard')

    form = TaskUpdateForm(request.POST or None, instance=task)

    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'tasks/update_task.html', {
        'form': form,
        'task': task
    })


# ================= ACCEPT TASK =================
@login_required
def accept_task(request, task_id):

    task = get_user_task(request, task_id)
    if not task:
        return redirect('dashboard')

    if task.status == 'assigned':
        task.status = 'accepted'
        task.save()

    return redirect('dashboard')


# ================= START TASK =================
@login_required
def start_task(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if task.employee.user != request.user:
        return redirect('dashboard')

    if task.status in ['assigned', 'accepted', 'paused']:

        if task.status == 'assigned':
            task.status = 'accepted'

        task.status = 'in_progress'
        task.save()

        # stop previous running log
        running_log = task.time_logs.filter(end_time__isnull=True).last()
        if running_log:
            running_log.end_time = timezone.now()
            running_log.save()

        #  CHECK IF REWORK
        is_rework = task.is_resubmitted

        TaskTimeLog.objects.create(
            employee_task=task,
            start_time=timezone.now(),
            is_rework=is_rework   
        )

    return redirect('dashboard')

# ================= PAUSE TASK =================
@login_required
def pause_task(request, task_id):

    task = get_user_task(request, task_id)
    if not task:
        return redirect('dashboard')

    if task.status == 'in_progress':
        task.status = 'paused'
        task.save()

        log = task.time_logs.filter(end_time__isnull=True).last()
        if log:
            log.end_time = timezone.now()
            log.save()

    return redirect('dashboard')


# ================= MARK DONE =================
@login_required
def mark_done(request, task_id):

    task = get_user_task(request, task_id)
    if not task:
        return redirect('dashboard')

    task.status = 'done'
    task.completed_at = timezone.now()
    task.save()

    log = task.time_logs.filter(end_time__isnull=True).last()
    if log:
        log.end_time = timezone.now()
        log.save()

    return redirect('dashboard')


# ================= APPROVE TASK =================
@login_required
def approve_task(request, task_id):

    if not request.user.is_superuser:
        return redirect('dashboard')

    task = get_object_or_404(TaskAssignment, id=task_id)

    task.status = 'completed'
    task.approved_by = request.user
    task.approved_at = timezone.now()
    task.save()

    return redirect('all_tasks')


# ================= AJAX: GET TASK DURATION =================
@login_required
def get_task_duration(request, task_id):
    try:
        task = KRATask.objects.get(id=task_id)

        return JsonResponse({
            'duration': str(task.expected_duration)
        })

    except KRATask.DoesNotExist:
        return JsonResponse({'error': 'Task not found'})
    
    
    #==========Rejected=================
@login_required
def reject_task(request, task_id):

    if not request.user.is_superuser:
        return redirect('dashboard')

    task = get_object_or_404(TaskAssignment, id=task_id)

    if request.method == "POST":
        reason = request.POST.get('reason')

        task.status = 'rejected'
        task.rejection_reason = reason
        task.save()

        messages.error(request, "Task Rejected")

    return redirect('dashboard')

#===========Resubmit================

@login_required
def resubmit_task(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if task.employee.user != request.user:
        return redirect('dashboard')

    if task.status == 'rejected':
        task.status = 'done'
        task.is_resubmitted = True
        task.rejection_reason = None
        task.save()

    return redirect('dashboard')

def calculate_times(task):

    total = 0
    rework = 0

    for log in task.time_logs.all():
        if log.end_time:
            duration = (log.end_time - log.start_time).total_seconds()

            total += duration

            if log.is_rework:
                rework += duration

    return {
        "total_hours": round(total / 3600, 2),
        "rework_hours": round(rework / 3600, 2),
        "actual_hours": round((total - rework) / 3600, 2)
    }