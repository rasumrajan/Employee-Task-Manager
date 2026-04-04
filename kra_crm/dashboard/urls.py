from django.urls import path
from . import views

urlpatterns = [
     path('', views.dashboard, name='dashboard'),
     path('department/<int:dept_id>/', views.department_employees, name='department_employees'),
]
