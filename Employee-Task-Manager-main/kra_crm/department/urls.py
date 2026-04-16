from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_department, name='add_department'),
    path('list/', views.department_list, name='department_list'),
    path('update/<int:pk>/', views.update_department, name='update_department'),
    path('delete/<int:pk>/', views.delete_department, name='delete_department'),
]