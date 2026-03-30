from django.urls import path
from . import views

urlpatterns = [
    path('add-category/', views.add_category, name='add_category'),
    path('add-task/', views.add_kra_task, name='add_kra_task'),
]