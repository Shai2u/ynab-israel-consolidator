"""
URL configuration for recon_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
from accounts import views as account_views
from identity import views as identity_views
from consolidation import views as consolidation_views
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/', account_views.account_list, name='account_list'),
    path('identity/', identity_views.identity_edit, name='identity_edit'),
    path('consolidation/', consolidation_views.consolidation_run, name='consolidation_run'),
    path('consolidation/export/', consolidation_views.consolidation_export, name='consolidation_export'),
]
