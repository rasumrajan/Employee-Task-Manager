from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import EmployeeTask, TaskTimeLog
from .forms import EmployeeTaskForm
from employees.models import Employee


# ==============================
# ASSIGN TASK (BOSS)
# ==============================

@login_required
def assign_task(request):
    if request.method == 'POST':
        form = EmployeeTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            return redirect('task_list')
    else:
        form = EmployeeTaskForm()

    return render(request, 'tasks/assign_task.html', {'form': form})


# ==============================
# TASK LIST (EMPLOYEE)
# ==============================

@login_required
def task_list(request):
    tasks = EmployeeTask.objects.filter(employee__user=request.user)
    return render(request, 'tasks/task_list.html', {'tasks': tasks})


# ==============================
# UPDATE TASK
# ==============================

@login_required
def update_task(request, pk):
    task = get_object_or_404(EmployeeTask, pk=pk)

    if task.employee.user != request.user:
        return redirect('task_list')

    if request.method == 'POST':
        form = EmployeeTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
        form = EmployeeTaskForm(instance=task)

    return render(request, 'tasks/update_task.html', {'form': form})


# ==============================
# START TASK
# ==============================

@login_required
def start_task(request, task_id):

    employee = Employee.objects.filter(user=request.user).first()

    if not employee:
        return redirect('dashboard')

    task = get_object_or_404(EmployeeTask, id=task_id, employee=employee)

    active_log = TaskTimeLog.objects.filter(
        employee_task=task,
        end_time__isnull=True
    ).first()

    if not active_log:
        TaskTimeLog.objects.create(
            employee_task=task,
            start_time=timezone.now()
        )

    task.status = "in_progress"
    task.save()

    return redirect('task_list')


# ==============================
# PAUSE TASK
# ==============================

@login_required
def pause_task(request, task_id):

    employee = Employee.objects.filter(user=request.user).first()

    if not employee:
        return redirect('dashboard')

    task = get_object_or_404(EmployeeTask, id=task_id, employee=employee)

    log = TaskTimeLog.objects.filter(
        employee_task=task,
        end_time__isnull=True
    ).last()

    if log:
        log.end_time = timezone.now()
        log.save()

    task.status = "paused"
    task.save()

    return redirect('task_list')


# ==============================
# COMPLETE TASK
# ==============================

@login_required
def complete_task(request, task_id):

    employee = Employee.objects.filter(user=request.user).first()

    if not employee:
        return redirect('dashboard')

    task = get_object_or_404(EmployeeTask, id=task_id, employee=employee)

    log = TaskTimeLog.objects.filter(
        employee_task=task,
        end_time__isnull=True
    ).last()

    if log:
        log.end_time = timezone.now()
        log.save()

    task.status = "completed"
    task.progress = 100
    task.save()

    return redirect('task_list')