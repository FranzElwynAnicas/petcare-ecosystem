from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.home, name="home"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/change_password/", views.change_password, name="change_password"),
    path("pets/", views.pet_list, name="pet_list"),
    path("pets/<int:pet_id>/", views.pet_detail, name="pet_detail"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("chatbot/", views.chatbot, name="chatbot"),

    # Authentication URLs
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="index"), name="logout"),

    # Adoption URLs
    path("adopt/<int:pet_id>/", views.adopt_pet, name="adopt_pet"),
    path("adoption/success/<int:application_id>/", views.adoption_success, name="adoption_success"),
    path("my-applications/", views.my_applications, name="my_applications"),
    
    # Veterinary URLs
    path("schedule-vet-appointment/", views.schedule_vet_appointment, name="schedule_vet_appointment"),
    path("schedule-appointment/", views.schedule_appointment_page, name="schedule_appointment_page"),
    path("my-appointments/", views.my_appointments, name="my_appointments"),
    
    # Appointment Management URLs
    path("my-appointments/cancel/<int:appointment_id>/", views.cancel_appointment, name="cancel_appointment"),
    path("my-appointments/reschedule/<int:appointment_id>/", views.reschedule_appointment, name="reschedule_appointment"),
    path("my-appointments/<int:appointment_id>/", views.appointment_detail, name="appointment_detail"),

    # Test URL (you can remove this after testing)
    path("test-vet-connection/", views.test_vet_connection, name="test_vet_connection"),
]