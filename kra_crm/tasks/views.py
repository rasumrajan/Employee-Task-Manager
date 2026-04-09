from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from kra.models import KRATask
from .models import TaskAssignment, TaskTimeLog
from .forms import TaskAssignForm, TaskUpdateForm


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

    return render(request, 'tasks/all_tasks.html', {'tasks': tasks})


# ================= EMPLOYEE: MY TASKS =================
@login_required
def task_list(request):

    tasks = TaskAssignment.objects.filter(
        employee__user=request.user
    ).order_by('-assigned_date')

    return render(request, 'tasks/task_list.html', {'tasks': tasks})


# ================= UPDATE TASK =================
@login_required
def update_task(request, pk):

    task = get_object_or_404(TaskAssignment, pk=pk)

    if task.employee.user != request.user and not request.user.is_superuser:
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

    task = get_object_or_404(TaskAssignment, id=task_id)

    if task.employee.user != request.user:
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

    if task.status in ['accepted', 'paused']:

        task.status = 'in_progress'
        task.save()

        # 🔥 STOP any running timer first
        running_log = task.time_logs.filter(end_time__isnull=True).last()
        if running_log:
            running_log.end_time = timezone.now()
            running_log.save()

        # 🔥 START new timer
        TaskTimeLog.objects.create(
            employee_task=task,
            start_time=timezone.now()
        )

    return redirect('dashboard')


# ================= PAUSE TASK =================
@login_required
def pause_task(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if task.employee.user != request.user:
        return redirect('dashboard')

    task.status = 'paused'
    task.save()

    # 🔥 STOP timer
    log = task.time_logs.filter(end_time__isnull=True).last()
    if log:
        log.end_time = timezone.now()
        log.save()

    return redirect('dashboard')


# ================= MARK DONE =================
@login_required
def mark_done(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if task.employee.user != request.user:
        return redirect('dashboard')

    task.status = 'done'
    task.save()

    #  STOP timer
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

    return redirect('dashboard')


# ================= GET TASK DURATION (AJAX) =================
def get_task_duration(request, task_id):
    try:
        task = KRATask.objects.get(id=task_id)

        return JsonResponse({
            'duration': str(task.expected_duration)
        })

    except KRATask.DoesNotExist:
        return JsonResponse({'error': 'Task not found'})