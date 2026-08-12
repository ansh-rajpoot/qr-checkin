from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_participant, name='register'),
    path('<uuid:qr_token>/', views.participant_qr_detail, name='qr_detail'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('login/', views.staff_login, name='login'),
    path('logout/', views.staff_logout, name='logout'),
]
