from django.urls import path
from . import views
#from .views import employee_dashboard

urlpatterns = [
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('add/', views.add_employee, name='add_employee'),
    path('list/', views.employee_list, name='employee_list'),
    
   # path('employee-dashboard/', employee_dashboard, name='employee_dashboard'),
    path('update/<int:pk>/', views.update_employee, name='update_employee'),
    path('delete/<int:pk>/', views.delete_employee, name='delete_employee'),
]