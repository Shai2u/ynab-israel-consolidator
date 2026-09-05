from django.urls import path
from . import views

urlpatterns = [
    path('', views.account_list, name='account_list'),
    path('<int:pk>/', views.account_detail, name='account_detail'),
    path('<int:pk>/edit/', views.account_edit, name='account_edit'),
    path('<int:pk>/upload/', views.account_upload, name='account_upload'),
    path('<int:pk>/convert/<path:filename>/', views.account_convert, name='account_convert'),
    path('<int:pk>/review/<path:filename>/', views.account_toggle_review, name='account_toggle_review'),
]
