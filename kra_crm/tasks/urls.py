from django.urls import path
from . import views

urlpatterns = [
    path('assign/', views.assign_task, name='assign_task'),
    path('list/', views.task_list, name='task_list'),
    path('update/<int:pk>/', views.update_task, name='update_task'),

    path('start/<int:task_id>/', views.start_task, name='start_task'),
    path('pause/<int:task_id>/', views.pause_task, name='pause_task'),
    path('complete/<int:task_id>/', views.complete_task, name='complete_task'),
]