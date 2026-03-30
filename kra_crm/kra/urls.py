from django.urls import path
from . import views

urlpatterns = [
    #-----Category-------
    path('add-category/', views.add_category, name='add_category'),
    path('categories/', views.category_list, name='category_list'),
    path('category/update/<int:pk>/', views.update_category, name='update_category'),
    path('category/delete/<int:pk>/', views.delete_category, name='delete_category'),
    #---- Task-----------
    path('add-task/', views.add_kra_task, name='add_kra_task'),
    path('tasks/', views.task_list, name='kra_task_list'),
    path('task/update/<int:pk>/', views.update_kra_task, name='update_kra_task'),
    path('task/delete/<int:pk>/', views.delete_kra_task, name='delete_kra_task'),
    
    
]