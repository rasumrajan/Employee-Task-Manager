from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import KRACategoryForm, KRATaskForm


def add_category(request):
    form = KRACategoryForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'kra/add_category.html', {'form': form})


def add_kra_task(request):
    form = KRATaskForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'kra/add_task.html', {'form': form})