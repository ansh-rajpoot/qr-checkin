from django.urls import path
from . import views

urlpatterns = [
    path('', views.scanner_page, name='scanner_page'),
    path('api/check-in/', views.check_in_api, name='check_in_api'),
]
