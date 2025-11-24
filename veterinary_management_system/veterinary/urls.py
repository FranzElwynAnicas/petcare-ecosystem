from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.dashboard, name='dashboard'),
    path('search/', views.search, name='search'),
    
    # Appointments
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/new/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/edit/', views.appointment_update, name='appointment_update'),
    path('appointments/<int:pk>/complete/', views.complete_appointment, name='complete_appointment'),
    path('appointments/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    
    # Vet-specific pages
    path('vet-dashboard/', views.vet_dashboard, name='vet_dashboard'),
    path('vet-dashboard/<int:vet_id>/', views.vet_dashboard, name='vet_dashboard_with_id'),
    path('vet-schedule/<int:vet_id>/', views.vet_schedule, name='vet_schedule'),
    path('vet-schedule-ajax/<int:vet_id>/', views.get_vet_schedule, name='get_vet_schedule'),
    
    # Pets
    path('pets/', views.pet_list, name='pet_list'),
    path('pets/new/', views.pet_create, name='pet_create'),
    path('pets/<int:pk>/', views.pet_detail, name='pet_detail'),
    path('pets/<int:pk>/edit/', views.pet_update, name='pet_update'),
    
    # Medical Records
    path('pets/<int:pet_pk>/medical-record/new/', views.medical_record_create, name='medical_record_create'),
    path('medical-records/<int:pk>/', views.medical_record_detail, name='medical_record_detail'),
    
    # Vaccines
    path('pets/<int:pet_pk>/vaccine/new/', views.add_vaccine_record, name='add_vaccine_record'),
    
    # Vets
    path('vets/', views.vet_list, name='vet_list'),
    path('vets/<int:pk>/', views.vet_detail, name='vet_detail'),
    
    # Legacy API endpoints (for external integration)
    path('api/health/<int:pet_id>/', views.get_health_record, name='get_health_record'),
    path('api/schedule-appointment/', views.schedule_appointment, name='schedule_appointment'),

    path('api/create-appointment/', views.api_create_appointment, name='api_create_appointment'),
]