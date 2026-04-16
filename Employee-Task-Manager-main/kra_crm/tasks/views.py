from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.contrib import messages
from django.contrib.auth.models import User
from employees.models import Employee
from kra.models import KRATask
from .models import Notification, TaskAssignment, TaskComment, TaskTimeLog
from .forms import TaskAssignForm, TaskUpdateForm
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# ================= HELPER =================
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


# ================= ASSIGN =================
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

        #  REAL-TIME NOTIFICATION
        channel_layer = get_channel_layer()

        employee_user = task.employee.user  #  CONFIRMED CORRECT

        async_to_sync(channel_layer.group_send)(
            f"user_{employee_user.id}",
            {
                "type": "send_notification",
                "message": f"New Task Assigned: {task.task.title}",
                "task_id": task.id,
                "username": request.user.username,
                "message_type": "task"   #  IMPORTANT
            }
        )

        return redirect('all_tasks')

    return render(request, 'tasks/assign_task.html', {'form': form})


# ================= ADMIN TASK LIST =================
@login_required
def all_tasks(request):

    if not request.user.is_superuser:
        return redirect('dashboard')

    tasks = TaskAssignment.objects.select_related(
        'employee__user', 'task'
    ).all().order_by('-assigned_date')

    search = request.GET.get('search', '')
    status = request.GET.get('status')
    employee_id = request.GET.get('employee')

    if search:
        tasks = tasks.filter(
            Q(employee__user__username__icontains=search) |
            Q(task__title__icontains=search)
        )

    if status:

        if status == "late":
            tasks = tasks.filter(
                status__in=['done', 'completed'],
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

    if employee_id:
        tasks = tasks.filter(employee_id=employee_id)

    paginator = Paginator(tasks.distinct(), 10)
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)

    for t in tasks:
        t.total_minutes = calculate_total_minutes(t)

    return render(request, 'tasks/all_tasks.html', {
        'tasks': tasks,
        'employees': Employee.objects.all(),
        'search': search,
        'status': status,
        'employee_id': employee_id,
    })


# ================= EMPLOYEE TASK LIST =================
@login_required
def task_list(request):

    tasks = TaskAssignment.objects.filter(
        employee__user=request.user
    ).order_by('-assigned_date')

    for t in tasks:
        t.total_minutes = calculate_total_minutes(t)

    return render(request, 'tasks/task_list.html', {'tasks': tasks})


# ================= UPDATE =================
@login_required
def update_task(request, pk):

    task = get_object_or_404(TaskAssignment, pk=pk)

    if task.employee.user != request.user and not request.user.is_superuser:
        return redirect('dashboard')

    if task.status == 'completed':
        return redirect('dashboard')

    form = TaskUpdateForm(request.POST or None, instance=task)

    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'tasks/update_task.html', {'form': form, 'task': task})


# ================= ACCEPT =================
@login_required
def accept_task(request, task_id):

    task = get_user_task(request, task_id)
    if not task:
        return redirect('dashboard')

    if task.status == 'assigned':
        task.status = 'accepted'
        task.save()

    return redirect('dashboard')


# ================= START =================
@login_required
def start_task(request, task_id):

    task = get_user_task(request, task_id)
    if not task:
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

        TaskTimeLog.objects.create(
            employee_task=task,
            start_time=timezone.now(),
            is_rework=task.is_resubmitted
        )

    return redirect('dashboard')


# ================= PAUSE =================
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


# ================= DONE (WITH NOTE) =================
@login_required
def mark_done(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if task.employee.user != request.user:
        return redirect('dashboard')

    if request.method == "POST":
        note = request.POST.get('note')

        task.status = 'done'
        task.completed_at = timezone.now()
        task.save()

        # SAVE COMMENT
        TaskComment.objects.create(
            task=task,
            user=request.user,
            message=note,
            is_admin=False
        )

    return redirect('dashboard')
# ================= APPROVE =================
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


# ================= REJECT =================
@login_required
def reject_task(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if request.method == "POST":
        reason = request.POST.get('reason')

        task.status = 'rejected'
        task.rejection_reason = reason
        task.save()

        #  SAVE ADMIN COMMENT
        TaskComment.objects.create(
            task=task,
            user=request.user,
            message=reason,
            is_admin=True
        )

    return redirect('dashboard')

# ================= RESUBMIT =================
@login_required
def resubmit_task(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    if request.method == "POST":
        note = request.POST.get('note')

        task.status = 'done'
        task.is_resubmitted = True
        task.rejection_reason = None
        task.completed_at = timezone.now()
        task.save()

        #  SAVE COMMENT
        TaskComment.objects.create(
            task=task,
            user=request.user,
            message=note,
            is_admin=False
        )

    return redirect('dashboard')

#===============Employee Score===========
def get_employee_score(employee):
    tasks = TaskAssignment.objects.filter(
        employee=employee,
        status__in=['done', 'completed']
    )

    total_tasks = tasks.count()

    if total_tasks < 5:
        return 0

    total_score = sum(t.performance_score() for t in tasks)
    return round(total_score / total_tasks, 2)

def get_top_3_performers():
    employees = Employee.objects.all()

    ranking = []

    for emp in employees:
        score = get_employee_score(emp)

        if score > 0:
            ranking.append({
                "employee": emp,
                "score": score
            })

    # Sort descending
    ranking = sorted(ranking, key=lambda x: x["score"], reverse=True)

    return ranking[:3]


#def admin_dashboard(request):

 #   employees = Employee.objects.all()

  #  top_employee = None
   # top_score = 0

    #for emp in employees:
     #   score = get_employee_score(emp)

      #  if score > top_score:
       #     top_score = score
        #    top_employee = emp

    #context = {
     #   "top_employee": top_employee,
      #  "top_score": top_score,
    #}

    #return render(request, "dashboard.html", context)


# ================= AJAX =================
@login_required
def get_task_duration(request, task_id):
    try:
        task = KRATask.objects.get(id=task_id)
        return JsonResponse({'duration': str(task.expected_duration)})
    except KRATask.DoesNotExist:
        return JsonResponse({'error': 'Task not found'})


# ================= TIME CALC =================
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
    

@login_required
def add_comment(request, task_id):

    task = get_object_or_404(TaskAssignment, id=task_id)

    #  SAFE USER EXTRACTION
    employee_user = getattr(task.employee, "user", task.employee)

    #  SECURITY CHECK
    if not request.user.is_superuser and employee_user != request.user:
        return redirect('dashboard')

    if request.method == "POST":

        message = request.POST.get('message')

        if message:

            # ================= SAVE COMMENT =================
            TaskComment.objects.create(
                task=task,
                user=request.user,
                message=message,
                is_admin=request.user.is_superuser
            )

            channel_layer = get_channel_layer()

            # ================= EMPLOYEE → ADMIN =================
            if not request.user.is_superuser:

                admins = User.objects.filter(is_superuser=True)

                for admin in admins:

                    #  DB Notification
                    Notification.objects.create(
                        user=admin,
                        task=task,
                        message=f"{request.user.username} sent a message on '{task.task.title}'"
                    )

                    #  REAL-TIME → ADMIN
                    async_to_sync(channel_layer.group_send)(
                        f"user_{admin.id}",   #  FIXED (correct target)
                        {
                            "type": "send_notification",
                            "message": message,
                            "task_id": task.id,
                            "username": request.user.username,
                            "message_type": "chat"   #  IMPORTANT
                        }
                    )

            # ================= ADMIN → EMPLOYEE =================
            else:

                # 🗂 DB Notification
                Notification.objects.create(
                    user=employee_user,
                    task=task,
                    message=f"Admin replied on '{task.task.title}'"
                )

                #  REAL-TIME → EMPLOYEE
                async_to_sync(channel_layer.group_send)(
                    f"user_{employee_user.id}",   #  CORRECT
                    {
                        "type": "send_notification",
                        "message": message,
                        "task_id": task.id,
                        "username": request.user.username,
                        "is_admin": True,
                        "message_type": "chat"   #  IMPORTANT
                    }
                )

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# ================= NOTIFICATIONS =================
@login_required
def get_notifications(request):

    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    )

    data = []

    for n in notifications:
        data.append({
            'id': n.id,
            'message': n.message,
            'task_id': n.task.id
        })

        n.is_read = True
        n.save()

    return JsonResponse({'notifications': data})