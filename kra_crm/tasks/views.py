from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import TaskAssignment
from .forms import TaskAssignForm, TaskUpdateForm


# 🔹 ASSIGN TASK (Admin Only)
@login_required
def assign_task(request):

    if not request.user.is_superuser:
        return redirect('dashboard')

    form = TaskAssignForm(request.POST or None)

    if form.is_valid():
        task = form.save(commit=False)
        task.assigned_by = request.user
        task.save()
        return redirect('all_tasks')

    return render(request, 'tasks/assign_task.html', {
        'form': form
    })


# 🔹 ADMIN: VIEW ALL TASKS
@login_required
def all_tasks(request):

    if not request.user.is_superuser:
        return redirect('task_list')

    tasks = TaskAssignment.objects.select_related(
        'employee__user',
        'task'
    ).all().order_by('-assigned_date')

    return render(request, 'tasks/all_tasks.html', {
        'tasks': tasks
    })


# 🔹 EMPLOYEE: MY TASKS
@login_required
def task_list(request):

    tasks = TaskAssignment.objects.filter(
        employee__user=request.user
    ).order_by('-assigned_date')

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks
    })


# 🔹 UPDATE TASK (Employee or Admin)
@login_required
def update_task(request, pk):

    task = get_object_or_404(TaskAssignment, pk=pk)

    if task.employee.user != request.user and not request.user.is_superuser:
        return redirect('task_list')

    form = TaskUpdateForm(request.POST or None, instance=task)

    if form.is_valid():
        form.save()
        return redirect('task_list')

    return render(request, 'tasks/update_task.html', {
        'form': form,
        'task': task
    })


# 🔹 START TASK
@login_required
def start_task(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if task.employee.user != request.user:
        return redirect('task_list')

    task.status = 'in_progress'
    task.save()

    return redirect('task_list')


# 🔹 PAUSE TASK
@login_required
def pause_task(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if task.employee.user != request.user:
        return redirect('task_list')

    task.status = 'paused'
    task.save()

    return redirect('task_list')


# 🔹 MARK AS DONE (Employee)
@login_required
def mark_done(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if task.employee.user != request.user:
        return redirect('task_list')

    task.status = 'done'
    task.save()

    return redirect('task_list')


# 🔹 APPROVE TASK (Admin Only)
@login_required
def approve_task(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if not request.user.is_superuser:
        return redirect('task_list')

    task.status = 'completed'
    task.approved_by = request.user
    task.approved_at = timezone.now()
    task.save()

    return redirect('all_tasks')