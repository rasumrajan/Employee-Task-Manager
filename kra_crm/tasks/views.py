from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import EmployeeTask
from .forms import EmployeeTaskForm
from django.utils import timezone


@login_required
def mark_done(request, task_id):
    task = get_object_or_404(EmployeeTask, id=task_id)

    if task.employee.user != request.user:
        return redirect('dashboard')

    task.status = 'done'
    task.save()

    return redirect('dashboard')


@login_required
def approve_task(request, task_id):
    task = get_object_or_404(EmployeeTask, id=task_id)

    if not request.user.is_superuser:
        return redirect('dashboard')

    task.status = 'completed'
    task.approved_by = request.user
    task.approved_at = timezone.now()
    task.save()

    return redirect('dashboard')

def assign_task(request):
    form = EmployeeTaskForm(request.POST or None)

    if form.is_valid():
        task = form.save(commit=False)
        task.assigned_by = request.user
        task.save()
        return redirect('task_list')

    return render(request, 'tasks/assign_task.html', {'form': form})

@login_required
def task_list(request):

    tasks = EmployeeTask.objects.filter(employee__user=request.user)

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks
    })
    
@login_required
def update_task(request, pk):

    task = get_object_or_404(EmployeeTask, pk=pk)

    # Optional: only owner or admin can edit
    if task.employee.user != request.user and not request.user.is_superuser:
        return redirect('task_list')

    form = EmployeeTaskForm(request.POST or None, instance=task)

    if form.is_valid():
        form.save()
        return redirect('task_list')

    return render(request, 'tasks/update_task.html', {
        'form': form
    })
    
@login_required
def start_task(request, task_id):
    task = get_object_or_404(EmployeeTask, id=task_id)

    if task.employee.user != request.user:
        return redirect('task_list')

    task.status = 'in_progress'
    task.save()

    return redirect('task_list')


@login_required
def pause_task(request, task_id):
    task = get_object_or_404(EmployeeTask, id=task_id)

    if task.employee.user != request.user:
        return redirect('task_list')

    task.status = 'paused'
    task.save()

    return redirect('task_list')


@login_required
def mark_done(request, task_id):
    task = get_object_or_404(EmployeeTask, id=task_id)

    if task.employee.user != request.user:
        return redirect('task_list')

    task.status = 'done'
    task.save()

    return redirect('task_list')


@login_required
def approve_task(request, task_id):
    task = get_object_or_404(EmployeeTask, id=task_id)

    if not request.user.is_superuser:
        return redirect('task_list')

    task.status = 'completed'
    task.approved_by = request.user
    task.approved_at = timezone.now()
    task.save()

    return redirect('task_list')