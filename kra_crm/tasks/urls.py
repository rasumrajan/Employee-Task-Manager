from django.urls import path
from . import views

urlpatterns = [

    path('all/', views.all_tasks, name='all_tasks'),
    path('my/', views.task_list, name='task_list'),
    path('assign/', views.assign_task, name='assign_task'),
    path('get-task-duration/<int:task_id>/', views.get_task_duration, name='get_task_duration'),
    path('accept/<int:task_id>/', views.accept_task, name='accept_task'),
    path('start/<int:task_id>/', views.start_task, name='start_task'),
    path('pause/<int:task_id>/', views.pause_task, name='pause_task'),
    path('done/<int:task_id>/', views.mark_done, name='mark_done'),
    path('approve/<int:task_id>/', views.approve_task, name='approve_task'),
]