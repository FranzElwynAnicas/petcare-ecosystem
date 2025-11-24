# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import CustomUserCreationForm, EditProfileForm, CustomPasswordChangeForm, ContactForm, AdoptionApplicationForm
from .models import ContactMessage, AdoptionApplication, UserProfile, VetAppointment
from .shelter_api import shelter_api
from .vet_api import vet_api

# Context processor to make appointments available globally
def appointments_context(request):
    """Context processor to add appointments to all templates"""
    if request.user.is_authenticated:
        appointments = vet_api.get_user_appointments(request.user)
        return {
            'user_appointments': appointments[:3],
            'user_appointments_count': len(appointments)
        }
    return {
        'user_appointments': [],
        'user_appointments_count': 0
    }

# Handles user registration process
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Save additional profile data to UserProfile model
            user_profile = user.userprofile
            user_profile.role = form.cleaned_data.get('role')
            user_profile.gender = form.cleaned_data.get('gender')
            user_profile.job = form.cleaned_data.get('job')
            user_profile.phone = form.cleaned_data.get('phone')
            user_profile.address = form.cleaned_data.get('address')
            user_profile.barangay = form.cleaned_data.get('barangay')
            user_profile.city = form.cleaned_data.get('city')
            user_profile.province = form.cleaned_data.get('province')
            user_profile.zip_code = form.cleaned_data.get('zip_code')
            user_profile.save()
            # Automatically log in the user after registration
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

# Displays user profile information
@login_required
def profile(request):
    return render(request, 'core/profile.html')

# Handles profile editing functionality
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user.userprofile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = EditProfileForm(instance=request.user.userprofile, user=request.user)
    return render(request, 'core/edit_profile.html', {'form': form})

# Handles password change functionality
@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update session to keep user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'core/change_password.html', {'form': form})

# Dashboard view for logged-in users
@login_required
def home(request):
    """Dashboard view for logged-in users with appointments"""
    appointments = vet_api.get_user_appointments(request.user)

    context = {
        'user_appointments': appointments[:5],
        'user_appointments_count': len(appointments)
    }
    return render(request, "core/home.html", context)

# Public landing page
def index(request):
    return render(request, 'core/index.html')

# About page with company information
def about(request):
    return render(request, "core/about.html")

# Contact page with contact form and information
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save the contact message to database
            contact_message = form.save()
            messages.success(request, 'Thank you! Your message has been sent successfully. We will get back to you within 24 hours.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})

# Chatbot page
def chatbot(request):
    return render(request, 'core/chatbot.html')

# Pet listing page
def pet_list(request):
    """Display available pets from shelter system"""
    pets = []
    shelter_system_connected = False

    try:
        pets = shelter_api.get_available_pets()
        shelter_system_connected = len(pets) > 0

        # Apply filters if provided
        species_filter = request.GET.get('species')
        breed_filter = request.GET.get('breed')
        age_filter = request.GET.get('age')
        gender_filter = request.GET.get('gender')
        energy_filter = request.GET.get('energy')

        if species_filter:
            pets = [pet for pet in pets if pet.get('species') == species_filter]
        if breed_filter:
            pets = [pet for pet in pets if breed_filter.lower() in pet.get('breed', '').lower()]
        if age_filter:
            # Simple age filtering - you might want to enhance this
            pets = [pet for pet in pets if str(pet.get('age', '')).lower() == age_filter]
        if gender_filter:
            pets = [pet for pet in pets if pet.get('gender') == gender_filter]
        if energy_filter:
            pets = [pet for pet in pets if pet.get('energy_level') == energy_filter]

        # Count statistics
        dogs_count = len([pet for pet in pets if pet.get('species') == 'dog'])
        cats_count = len([pet for pet in pets if pet.get('species') == 'cat'])
        puppies_count = len([pet for pet in pets if pet.get('age', 0) <= 2]) # Young pets

    except Exception as e:
        print(f"Error loading pets: {e}")
        pets = []
        dogs_count = 0
        cats_count = 0
        puppies_count = 0

    context = {
        'pets': pets,
        'shelter_system_connected': shelter_system_connected,
        'dogs_count': dogs_count,
        'cats_count': cats_count,
        'puppies_count': puppies_count
    }
    return render(request, 'core/pet_list.html', context)

# Pet detail page
def pet_detail(request, pet_id):
    """Display detailed information about a specific pet"""
    pet = None
    try:
        pet = shelter_api.get_pet_details(pet_id)
    except Exception as e:
        print(f"Error loading pet details: {e}")
        messages.error(request, "Sorry, we couldn't load the pet details at this time.")
    context = {
        'pet': pet,
        'pet_id': pet_id
    }
    return render(request, 'core/pet_detail.html', context)

# Adoption application page
@login_required
def adopt_pet(request, pet_id):
    """Handle pet adoption application"""
    pet = None
    try:
        pet = shelter_api.get_pet_details(pet_id)
    except Exception as e:
        print(f"Error loading pet for adoption: {e}")
        messages.error(request, "Sorry, we couldn't load the pet information.")
        return redirect('pet_list')

    if request.method == 'POST':
        form = AdoptionApplicationForm(request.POST)
        if form.is_valid():
            # Save adoption application
            application = form.save(commit=False)
            application.user = request.user
            application.shelter_pet_id = pet_id
            application.pet_name = pet.get('name', 'Unknown')
            application.pet_species = pet.get('species', 'dog')
            application.save()

            # Try to schedule vet appointment automatically
            appointment_result = None
            try:
                adoption_data = {
                    'pet_name': pet.get('name'),
                    'owner_name': form.cleaned_data['applicant_name'],
                    'owner_email': form.cleaned_data['applicant_email'],
                    'owner_phone': form.cleaned_data['applicant_phone'],
                    'species': pet.get('species'),
                    'breed': pet.get('breed', 'Mixed'),
                    'reason': 'Post-adoption health checkup'
                }
                appointment_result = vet_api.create_appointment(adoption_data, request.user)
            except Exception as e:
                print(f"Error scheduling vet appointment: {e}")
                appointment_result = {'success': False, 'error': str(e)}

            messages.success(request, 'Adoption application submitted successfully!')
            return redirect('adoption_success', application_id=application.id)
    else:
        # Pre-fill form with user data
        initial_data = {
            'applicant_name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'applicant_email': request.user.email,
            'applicant_phone': request.user.userprofile.phone if hasattr(request.user, 'userprofile') else '',
            'applicant_address': request.user.userprofile.address if hasattr(request.user, 'userprofile') else ''
        }
        form = AdoptionApplicationForm(initial=initial_data)

    context = {
        'form': form,
        'pet': pet,
        'pet_id': pet_id
    }
    return render(request, 'core/adopt_pet.html', context)

# Adoption success page
@login_required
def adoption_success(request, application_id):
    """Display adoption application success page"""
    try:
        application = AdoptionApplication.objects.get(id=application_id, user=request.user)
        # Try to get appointment result (this would typically come from the adoption process)
        appointment_result = None
        context = {
            'application': application,
            'appointment_result': appointment_result
        }
        return render(request, 'core/adoption_success.html', context)
    except AdoptionApplication.DoesNotExist:
        messages.error(request, "Application not found.")
        return redirect('my_applications')

# User's adoption applications
@login_required
def my_applications(request):
    """Display user's adoption applications"""
    applications = AdoptionApplication.objects.filter(user=request.user).order_by('-applied_date')
    context = {
        'applications': applications
    }
    return render(request, 'core/my_applications.html', context)

# Vet appointment scheduling
@login_required
def schedule_vet_appointment(request):
    """Handle vet appointment scheduling"""
    if request.method == 'POST':
        try:
            # Get form data
            appointment_data = {
                'pet_name': request.POST.get('pet_name'),
                'owner_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'owner_email': request.user.email,
                'owner_phone': request.user.userprofile.phone or 'Not provided',
                'reason': request.POST.get('reason'),
                'species': request.POST.get('species'),
                'breed': request.POST.get('breed', 'Unknown'),
                'pet_age': request.POST.get('pet_age', 'Unknown'),
                'urgency': request.POST.get('urgency', 'routine'),
                'special_notes': request.POST.get('special_notes', ''),
                'previous_vet': request.POST.get('previous_vet', ''),
            }

            # Use the vet API - pass the user object
            result = vet_api.create_appointment(appointment_data, request.user)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(result)
            else:
                if result['success']:
                    messages.success(request, result['message'])
                else:
                    messages.error(request, result.get('error', 'Failed to schedule appointment'))
                return redirect('my_appointments')
        except Exception as e:
            error_msg = f"Error scheduling appointment: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            else:
                messages.error(request, error_msg)
            return redirect('schedule_appointment_page')
    return redirect('schedule_appointment_page')

@login_required
def schedule_appointment_page(request):
    """Display the vet appointment scheduling page"""
    return render(request, 'core/schedule_appointment.html')

@login_required
def my_appointments(request):
    """Display user's vet appointments"""
    appointments = vet_api.get_user_appointments(request.user)

    # Calculate stats
    appointments_count = len(appointments)
    upcoming_count = len([appt for appt in appointments if appt.get('status') in ['scheduled', 'confirmed']])
    completed_count = len([appt for appt in appointments if appt.get('status') == 'completed'])
    scheduled_count = len([appt for appt in appointments if appt.get('status') == 'scheduled'])

    context = {
        'appointments': appointments,
        'appointments_count': appointments_count,
        'upcoming_count': upcoming_count,
        'completed_count': completed_count,
        'scheduled_count': scheduled_count
    }
    return render(request, 'core/my_appointments.html', context)

# UPDATED: Cancel appointment view with vet system integration
@login_required
def cancel_appointment(request, appointment_id):
    """Cancel a vet appointment in both systems"""
    try:
        # Get the local appointment
        appointment = VetAppointment.objects.get(id=appointment_id, user=request.user)
        
        # If we have a vet system appointment ID, cancel it there too
        if appointment.vet_appointment_id:
            print(f"🔄 Cancelling appointment in vet system: {appointment.vet_appointment_id}")
            vet_result = vet_api.cancel_appointment(appointment.vet_appointment_id)
            
            if not vet_result['success']:
                print(f"⚠️ Failed to cancel in vet system: {vet_result.get('error')}")
                # Continue with local cancellation even if vet system fails
                messages.warning(request, f"Appointment cancelled locally but failed to cancel in vet system: {vet_result.get('error')}")
            else:
                messages.info(request, "Appointment cancelled in both systems successfully.")
        else:
            messages.info(request, "Appointment cancelled locally.")
        
        # Update local appointment status
        appointment.status = 'cancelled'
        appointment.save()
        
        messages.success(request, f"Appointment for {appointment.pet_name} has been cancelled successfully.")
        
    except VetAppointment.DoesNotExist:
        messages.error(request, "Appointment not found.")
    except Exception as e:
        messages.error(request, f"Error cancelling appointment: {str(e)}")
    
    return redirect('my_appointments')

@login_required
def reschedule_appointment(request, appointment_id):
    """Reschedule a vet appointment"""
    if request.method == 'POST':
        try:
            appointment = VetAppointment.objects.get(id=appointment_id, user=request.user)
            new_date_str = request.POST.get('new_date')
            
            if new_date_str:
                from datetime import datetime
                new_date = datetime.fromisoformat(new_date_str.replace('Z', '+00:00'))
                appointment.appointment_date = new_date
                appointment.status = 'scheduled'
                appointment.save()
                
                messages.success(request, f"Appointment for {appointment.pet_name} has been rescheduled.")
            else:
                messages.error(request, "Please provide a new date and time.")
                
        except VetAppointment.DoesNotExist:
            messages.error(request, "Appointment not found.")
        except Exception as e:
            messages.error(request, f"Error rescheduling appointment: {str(e)}")
    
    return redirect('my_appointments')

@login_required
def appointment_detail(request, appointment_id):
    """View detailed information about a specific appointment"""
    try:
        appointment = VetAppointment.objects.get(id=appointment_id, user=request.user)
        context = {
            'appointment': appointment
        }
        return render(request, 'core/appointment_detail.html', context)
    except VetAppointment.DoesNotExist:
        messages.error(request, "Appointment not found.")
        return redirect('my_appointments')

# Temporary test view for vet system connection
@login_required
def test_vet_connection(request):
    """Temporary view to test vet system connection"""
    print("🧪 Testing vet system connection...")
    
    # Test connection
    connection_ok = vet_api.test_connection()
    print(f"Connection test result: {connection_ok}")
    
    # Test appointment creation
    test_data = {
        'pet_name': 'Test Pet',
        'owner_name': f"{request.user.first_name} {request.user.last_name}",
        'owner_email': request.user.email,
        'owner_phone': '123-456-7890',
        'reason': 'Test appointment',
        'species': 'dog',
        'breed': 'Mixed'
    }
    
    result = vet_api.create_appointment(test_data, request.user)
    print(f"Appointment creation result: {result}")
    
    return JsonResponse({
        'connection_ok': connection_ok,
        'appointment_result': result
    })