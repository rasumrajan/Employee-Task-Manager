from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from kra.models import KRACategory, KRATask
from kra.admin import is_admin
from .forms import KRACategoryForm, KRATaskForm
from django.shortcuts import render, redirect, get_object_or_404
from .models import KRACategory, KRATask
from .forms import KRACategoryForm, KRATaskForm

@login_required
@user_passes_test(is_admin)
def add_category(request):
    form = KRACategoryForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'kra/add_category.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def add_kra_task(request):
    form = KRATaskForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'kra/add_task.html', {'form': form})
@login_required
@user_passes_test(is_admin)
def category_list(request):
    categories = KRACategory.objects.select_related('department').all()

    return render(request, 'kra/category_list.html', {
        'categories': categories
    })

@login_required
@user_passes_test(is_admin)
def task_list(request):
    tasks = KRATask.objects.select_related('category', 'category__department').all()

    return render(request, 'kra/task_list.html', {
        'tasks': tasks
    })
    



# ================= CATEGORY =================
@login_required
@user_passes_test(is_admin)
def update_category(request, pk):
    category = get_object_or_404(KRACategory, pk=pk)

    form = KRACategoryForm(request.POST or None, instance=category)

    if form.is_valid():
        form.save()
        return redirect('category_list')

    return render(request, 'kra/add_category.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delete_category(request, pk):
    category = get_object_or_404(KRACategory, pk=pk)

    category.delete()
    return redirect('category_list')


# ================= TASK =================
@login_required
@user_passes_test(is_admin)
def update_kra_task(request, pk):
    task = get_object_or_404(KRATask, pk=pk)

    form = KRATaskForm(request.POST or None, instance=task)

    if form.is_valid():
        form.save()
        return redirect('kra_task_list')

    return render(request, 'kra/add_task.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delete_kra_task(request, pk):
    task = get_object_or_404(KRATask, pk=pk)

    task.delete()
    return redirect('kra_task_list')