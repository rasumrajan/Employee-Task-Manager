"""
URL configuration for kra_crm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

# Set the site header to an empty string to remove the text
admin.site.site_header = "OM SAI KRA" 
# Set other titles to empty strings if needed
admin.site.site_title = "OM SAI"
admin.site.index_title = "KRA"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('kra/', include('kra.urls')),
    path('tasks/', include('tasks.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('department/',include('department.urls')),
    
]
