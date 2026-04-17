from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .models import KRACategory, KRATask
from .forms import KRACategoryForm, KRATaskForm


# ================= ADMIN CHECK =================
def is_admin(user):
    return user.is_superuser


# ================= CATEGORY =================

@login_required
@user_passes_test(is_admin)
def add_category(request):
    form = KRACategoryForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Category created successfully")
        return redirect('kra_categories')

    return render(request, 'kra/add_category.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def category_list(request):
    categories = KRACategory.objects.select_related('department').all()

    return render(request, 'kra/category_list.html', {
        'categories': categories
    })


@login_required
@user_passes_test(is_admin)
def update_category(request, pk):
    category = get_object_or_404(KRACategory, pk=pk)

    form = KRACategoryForm(request.POST or None, instance=category)

    if form.is_valid():
        form.save()
        messages.success(request, "Category updated successfully")
        return redirect('kra_categories')

    return render(request, 'kra/add_category.html', {
        'form': form,
        'is_edit': True
    })


@login_required
@user_passes_test(is_admin)
def delete_category(request, pk):
    category = get_object_or_404(KRACategory, pk=pk)

    category.delete()
    messages.success(request, "Category deleted successfully")

    return redirect('kra_categories')


# ================= KRA TASK =================

# ================= TASK LIST =================
@login_required
@user_passes_test(is_admin)
def kra_task_list(request):

    tasks = KRATask.objects.select_related('category', 'category__department').all()

    return render(request, 'kra/task_list.html', {
        'tasks': tasks
    })


# ================= ADD TASK =================
@login_required
@user_passes_test(is_admin)
def add_kra_task(request):

    form = KRATaskForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Task created successfully")
        return redirect('kra_tasks')

    return render(request, 'kra/add_task.html', {
        'form': form
    })


# ================= UPDATE TASK =================
@login_required
@user_passes_test(is_admin)
def update_kra_task(request, pk):

    task = get_object_or_404(KRATask, pk=pk)

    form = KRATaskForm(request.POST or None, instance=task)

    if form.is_valid():
        form.save()
        messages.success(request, "Task updated successfully")
        return redirect('kra_tasks')

    return render(request, 'kra/add_task.html', {
        'form': form,
        'is_edit': True
    })


# ================= DELETE TASK =================
@login_required
@user_passes_test(is_admin)
def delete_kra_task(request, pk):

    task = get_object_or_404(KRATask, pk=pk)

    task.delete()
    messages.success(request, "Task deleted successfully")

    return redirect('kra_tasks')