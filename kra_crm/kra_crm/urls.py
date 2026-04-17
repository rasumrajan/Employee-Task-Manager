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
from django.conf.urls.static import static
from kra_crm import settings
from django.shortcuts import redirect
from django.views.static import serve
from django.urls import re_path
# Set the site header to an empty string to remove the text
admin.site.site_header = "OM SAI KRA" 
# Set other titles to empty strings if needed
admin.site.site_title = "OM SAI"
admin.site.index_title = "KRA"

urlpatterns = [
    
    path('', lambda request: redirect('login')),
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('employees/', include('employees.urls')),
    path('kra/', include('kra.urls')),
    path('tasks/', include('tasks.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('department/',include('department.urls')),
    
] 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
