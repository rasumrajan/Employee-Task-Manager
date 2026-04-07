from django.urls import path
from . import views

urlpatterns = [
    #-----Category-------
    path('add-category/', views.add_category, name='add_kra_category'),
    path('categories/', views.category_list, name='kra_categories'),
    path('category/update/<int:pk>/', views.update_category, name='update_kra_category'),
    path('category/delete/<int:pk>/', views.delete_category, name='delete_kra_category'),
    #---- Task-----------
    path('tasks/', views.kra_task_list, name='kra_tasks'),
    path('add-task/', views.add_kra_task, name='add_kra_task'),
    path('task/update/<int:pk>/', views.update_kra_task, name='update_kra_task'),
    path('task/delete/<int:pk>/', views.delete_kra_task, name='delete_kra_task'),
]

