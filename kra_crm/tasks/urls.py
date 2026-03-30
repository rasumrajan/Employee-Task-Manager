from django.urls import path
from . import views

urlpatterns = [
    # Task management
    path('assign/', views.assign_task, name='assign_task'),
    path('list/', views.task_list, name='task_list'),
    path('update/<int:pk>/', views.update_task, name='update_task'),

    # Work flow
    path('start/<int:task_id>/', views.start_task, name='start_task'),
    path('pause/<int:task_id>/', views.pause_task, name='pause_task'),

    # Approval flow (NEW SYSTEM)
    path('done/<int:task_id>/', views.mark_done, name='mark_done'),
    path('approve/<int:task_id>/', views.approve_task, name='approve_task'),
]