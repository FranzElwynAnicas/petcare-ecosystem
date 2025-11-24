from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


from .models import Pet, Vet, Appointment, MedicalRecord, Vaccine
from .forms import PetForm, VetForm, AppointmentForm, MedicalRecordForm, VaccineForm, SearchForm
from .serializers import PetSerializer, AppointmentSerializer

# Dashboard and Main Views
def dashboard(request):
    """Main dashboard for veterinary staff"""
    today = timezone.now().date()
    
    # Today's appointments
    todays_appointments = Appointment.objects.filter(
        date__date=today,
        status__in=['scheduled', 'confirmed', 'in_progress']
    ).select_related('pet', 'vet').order_by('date')
    
    # Upcoming appointments (next 7 days)
    upcoming_appointments = Appointment.objects.filter(
        date__date__range=[today, today + timedelta(days=7)],
        status__in=['scheduled', 'confirmed']
    ).select_related('pet', 'vet').order_by('date')
    
    # Recent medical records
    recent_records = MedicalRecord.objects.all().select_related('pet', 'vet').order_by('-visit_date')[:5]
    
    # Due vaccines (next 30 days)
    due_vaccines = Vaccine.objects.filter(
        next_due_date__lte=today + timedelta(days=30)
    ).select_related('pet')
    
    # Quick stats
    total_pets = Pet.objects.count()
    active_vets = Vet.objects.filter(is_active=True).count()
    monthly_appointments = Appointment.objects.filter(
        date__month=today.month,
        date__year=today.year
    ).count()
    
    context = {
        'todays_appointments': todays_appointments,
        'upcoming_appointments': upcoming_appointments,
        'recent_records': recent_records,
        'due_vaccines': due_vaccines,
        'total_pets': total_pets,
        'active_vets': active_vets,
        'monthly_appointments': monthly_appointments,
        'today': today,
    }
    return render(request, 'veterinary/dashboard.html', context)

def vet_dashboard(request, vet_id=None):
    """Vet-specific dashboard showing their schedule and patients"""
    if vet_id:
        vet = get_object_or_404(Vet, pk=vet_id)
    else:
        # For now, show first active vet. Later, connect to user authentication
        vet = Vet.objects.filter(is_active=True).first()
        if not vet:
            messages.warning(request, "No active veterinarians found.")
            return redirect('dashboard')
    
    today = timezone.now().date()
    
    # Vet's today appointments
    todays_appointments = vet.todays_appointments.select_related('pet')
    
    # Vet's upcoming appointments
    upcoming_appointments = vet.upcoming_appointments.select_related('pet')[:10]
    
    # Recent medical records by this vet
    recent_records = MedicalRecord.objects.filter(vet=vet).select_related('pet').order_by('-visit_date')[:5]
    
    # Vet's monthly stats
    monthly_completed = Appointment.objects.filter(
        vet=vet,
        status='completed',
        date__month=today.month,
        date__year=today.year
    ).count()
    
    context = {
        'vet': vet,
        'todays_appointments': todays_appointments,
        'upcoming_appointments': upcoming_appointments,
        'recent_records': recent_records,
        'monthly_completed': monthly_completed,
        'today': today,
    }
    return render(request, 'veterinary/vet_dashboard.html', context)

# Appointment Views
def appointment_list(request):
    """List all appointments with filtering"""
    appointments = Appointment.objects.all().select_related('pet', 'vet').order_by('-date')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    # Filter by date
    date_filter = request.GET.get('date')
    if date_filter:
        appointments = appointments.filter(date__date=date_filter)
    
    # Filter by vet
    vet_filter = request.GET.get('vet')
    if vet_filter:
        appointments = appointments.filter(vet_id=vet_filter)
    
    # Calculate stats
    total_appointments = appointments.count()
    scheduled_count = appointments.filter(status='scheduled').count()
    confirmed_count = appointments.filter(status='confirmed').count()
    completed_count = appointments.filter(status='completed').count()
    cancelled_count = appointments.filter(status='cancelled').count()
    no_show_count = appointments.filter(status='no_show').count()
    
    context = {
        'appointments': appointments,
        'status_choices': Appointment.STATUS_CHOICES,
        'vets': Vet.objects.filter(is_active=True),
        'total_appointments': total_appointments,
        'scheduled_count': scheduled_count,
        'confirmed_count': confirmed_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'no_show_count': no_show_count,
    }
    return render(request, 'veterinary/appointment_list.html', context)

def appointment_detail(request, pk):
    """View appointment details"""
    appointment = get_object_or_404(Appointment, pk=pk)
    context = {'appointment': appointment}
    return render(request, 'veterinary/appointment_detail.html', context)

def appointment_create(request):
    """Create a new appointment"""
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            messages.success(request, f'Appointment scheduled for {appointment.pet.name} with Dr. {appointment.vet.name}')
            return redirect('appointment_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentForm()
    
    context = {'form': form, 'title': 'Schedule New Appointment'}
    return render(request, 'veterinary/appointment_form.html', context)

def appointment_update(request, pk):
    """Update an existing appointment"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment updated successfully')
            return redirect('appointment_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentForm(instance=appointment)
    
    context = {'form': form, 'appointment': appointment, 'title': 'Edit Appointment'}
    return render(request, 'veterinary/appointment_form.html', context)

def complete_appointment(request, pk):
    """Mark an appointment as completed and create medical record"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.pet = appointment.pet
            medical_record.vet = appointment.vet
            medical_record.save()
            
            # Update appointment status
            appointment.status = 'completed'
            appointment.save()
            
            messages.success(request, f'Appointment completed and medical record created for {appointment.pet.name}')
            return redirect('vet_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill form with appointment data
        initial_data = {
            'vet': appointment.vet,
            'visit_date': timezone.now().date(),
            'diagnosis': f'Follow-up for: {appointment.reason}',
        }
        form = MedicalRecordForm(initial=initial_data)
    
    context = {
        'appointment': appointment,
        'form': form,
    }
    return render(request, 'veterinary/complete_appointment.html', context)

def cancel_appointment(request, pk):
    """Cancel an appointment"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, f'Appointment cancelled for {appointment.pet.name}')
        return redirect('appointment_list')
    
    context = {'appointment': appointment}
    return render(request, 'veterinary/cancel_appointment.html', context)

# Pet Views
def pet_list(request):
    """List all pets with search"""
    pets = Pet.objects.all().order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        pets = pets.filter(
            Q(name__icontains=search_query) |
            Q(owner_name__icontains=search_query) |
            Q(microchip_id__icontains=search_query) |
            Q(breed__icontains=search_query)
        )
    
    # Calculate stats
    total_pets = pets.count()
    dog_count = pets.filter(species='dog').count()
    cat_count = pets.filter(species='cat').count()
    other_count = total_pets - dog_count - cat_count
    
    context = {
        'pets': pets,
        'total_pets': total_pets,
        'dog_count': dog_count,
        'cat_count': cat_count,
        'other_count': other_count,
    }
    return render(request, 'veterinary/pet_list.html', context)

def pet_detail(request, pk):
    """View pet details and medical history"""
    pet = get_object_or_404(Pet, pk=pk)
    medical_records = MedicalRecord.objects.filter(pet=pet).select_related('vet').order_by('-visit_date')
    vaccines = Vaccine.objects.filter(pet=pet).select_related('administered_by').order_by('-vaccination_date')
    appointments = Appointment.objects.filter(pet=pet).select_related('vet').order_by('-date')
    
    context = {
        'pet': pet,
        'medical_records': medical_records,
        'vaccines': vaccines,
        'appointments': appointments,
    }
    return render(request, 'veterinary/pet_detail.html', context)

def pet_create(request):
    """Add a new pet to the system"""
    if request.method == 'POST':
        form = PetForm(request.POST)
        if form.is_valid():
            pet = form.save()
            messages.success(request, f'Successfully added {pet.name} to the system')
            return redirect('pet_detail', pk=pet.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PetForm()
    
    context = {'form': form, 'title': 'Add New Pet'}
    return render(request, 'veterinary/pet_form.html', context)

def pet_update(request, pk):
    """Update pet information"""
    pet = get_object_or_404(Pet, pk=pk)
    
    if request.method == 'POST':
        form = PetForm(request.POST, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, f'Successfully updated {pet.name}\'s information')
            return redirect('pet_detail', pk=pet.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PetForm(instance=pet)
    
    context = {'form': form, 'pet': pet, 'title': f'Edit {pet.name}'}
    return render(request, 'veterinary/pet_form.html', context)

# Medical Record Views
def medical_record_create(request, pet_pk):
    """Create a medical record for a pet"""
    pet = get_object_or_404(Pet, pk=pet_pk)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.pet = pet
            medical_record.save()
            messages.success(request, f'Medical record added for {pet.name}')
            return redirect('pet_detail', pk=pet.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MedicalRecordForm(initial={'pet': pet})
    
    context = {'form': form, 'pet': pet, 'title': f'Add Medical Record for {pet.name}'}
    return render(request, 'veterinary/medical_record_form.html', context)

def medical_record_detail(request, pk):
    """View medical record details"""
    medical_record = get_object_or_404(MedicalRecord, pk=pk)
    context = {'medical_record': medical_record}
    return render(request, 'veterinary/medical_record_detail.html', context)

# Vaccine Views
def add_vaccine_record(request, pet_pk):
    """Add vaccine record for a pet"""
    pet = get_object_or_404(Pet, pk=pet_pk)
    
    if request.method == 'POST':
        form = VaccineForm(request.POST)
        if form.is_valid():
            vaccine = form.save(commit=False)
            vaccine.pet = pet
            vaccine.save()
            messages.success(request, f'Vaccine record added for {pet.name}')
            return redirect('pet_detail', pk=pet.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VaccineForm()
    
    context = {'form': form, 'pet': pet, 'title': f'Add Vaccine Record for {pet.name}'}
    return render(request, 'veterinary/vaccine_form.html', context)

# Vet Views
def vet_list(request):
    """List all veterinarians"""
    vets = Vet.objects.filter(is_active=True).order_by('name')
    context = {'vets': vets}
    return render(request, 'veterinary/vet_list.html', context)

def vet_detail(request, pk):
    """View vet details and schedule"""
    vet = get_object_or_404(Vet, pk=pk)
    upcoming_appointments = vet.upcoming_appointments.select_related('pet')[:10]
    context = {
        'vet': vet,
        'upcoming_appointments': upcoming_appointments,
    }
    return render(request, 'veterinary/vet_detail.html', context)

def vet_schedule(request, vet_id):
    """Detailed schedule view for a specific vet"""
    vet = get_object_or_404(Vet, pk=vet_id)
    
    # Get date filter
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Get appointments for selected date
    daily_appointments = Appointment.objects.filter(
        vet=vet,
        date__date=selected_date
    ).select_related('pet').order_by('date')
    
    context = {
        'vet': vet,
        'selected_date': selected_date,
        'daily_appointments': daily_appointments,
    }
    return render(request, 'veterinary/vet_schedule.html', context)

# Search Functionality
def search(request):
    """Search across pets, owners, and appointments"""
    form = SearchForm(request.GET or None)
    results = {}
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        search_type = form.cleaned_data.get('search_type')
        
        if query:
            if search_type in ['all', 'pets']:
                results['pets'] = Pet.objects.filter(
                    Q(name__icontains=query) |
                    Q(owner_name__icontains=query) |
                    Q(microchip_id__icontains=query) |
                    Q(breed__icontains=query)
                )[:10]
            
            if search_type in ['all', 'owners']:
                # Get unique owners from pets
                owner_pets = Pet.objects.filter(
                    Q(owner_name__icontains=query) |
                    Q(owner_email__icontains=query) |
                    Q(owner_phone__icontains=query)
                ).distinct('owner_name')[:10]
                results['owners'] = owner_pets
            
            if search_type in ['all', 'appointments']:
                results['appointments'] = Appointment.objects.filter(
                    Q(pet__name__icontains=query) |
                    Q(reason__icontains=query) |
                    Q(vet__name__icontains=query) |
                    Q(notes__icontains=query)
                ).select_related('pet', 'vet')[:10]
            
            if search_type in ['all', 'vets']:
                results['vets'] = Vet.objects.filter(
                    Q(name__icontains=query) |
                    Q(specialization__icontains=query) |
                    Q(email__icontains=query)
                )[:10]
    
    context = {'form': form, 'results': results}
    return render(request, 'veterinary/search.html', context)

# API endpoints for external integration
@api_view(['GET'])
def get_health_record(request, pet_id):
    """API endpoint to get health record for a specific pet"""
    try:
        # Try to find pet by external_pet_id first, then by primary key
        try:
            pet = Pet.objects.get(external_pet_id=pet_id)
        except Pet.DoesNotExist:
            pet = Pet.objects.get(pk=pet_id)
            
        serializer = PetSerializer(pet)
        return Response(serializer.data)
    except Pet.DoesNotExist:
        return Response(
            {'detail': 'No record found for this pet.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def schedule_appointment(request):
    """API endpoint to schedule appointment (for external systems)"""
    from .utils.google_calendar import create_calendar_event
    
    serializer = AppointmentSerializer(data=request.data)
    if serializer.is_valid():
        try:
            appointment = serializer.save()
            
            # Create Google Calendar event
            event_id = create_calendar_event(appointment)
            if event_id:
                appointment.google_calendar_event_id = event_id
                appointment.save()

            output_serializer = AppointmentSerializer(appointment)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#API
@api_view(['POST'])
def api_create_appointment(request):
    """
    API endpoint for adoption app to create appointments
    Expects JSON data with appointment details
    """
    try:
        # Get JSON data from request
        data = request.data
        
        # Required fields
        required_fields = ['pet_name', 'owner_name', 'owner_email', 'owner_phone', 'reason', 'preferred_date']
        
        # Validate required fields
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'Missing required field: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Find or create pet
        pet, pet_created = Pet.objects.get_or_create(
            name=data['pet_name'],
            owner_name=data['owner_name'],
            owner_email=data['owner_email'],
            defaults={
                'owner_phone': data.get('owner_phone', ''),
                'species': data.get('species', 'dog'),
                'breed': data.get('breed', 'Unknown'),
                'sex': data.get('sex', 'unknown'),
            }
        )
        
        # Get first available vet (or assign based on logic)
        vet = Vet.objects.filter(is_active=True).first()
        if not vet:
            return Response(
                {'error': 'No active veterinarians available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse appointment date
        try:
            from datetime import datetime
            appointment_date = datetime.fromisoformat(data['preferred_date'].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create appointment
        appointment = Appointment.objects.create(
            pet=pet,
            vet=vet,
            date=appointment_date,
            duration_minutes=data.get('duration_minutes', 30),
            reason=data['reason'],
            status='scheduled',
            notes=data.get('notes', f'Created from adoption app. Pet details: {data.get("pet_details", "")}')
        )
        
        # Prepare response data
        response_data = {
            'success': True,
            'appointment_id': appointment.id,
            'message': f'Appointment scheduled for {pet.name} with Dr. {vet.name}',
            'appointment_details': {
                'date': appointment.date.isoformat(),
                'pet': pet.name,
                'vet': f'Dr. {vet.name}',
                'reason': appointment.reason,
                'status': appointment.status
            },
            'pet_created': pet_created
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to create appointment: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Utility Views
def get_vet_schedule(request, vet_id):
    """Get vet's schedule for AJAX requests"""
    vet = get_object_or_404(Vet, pk=vet_id)
    date_str = request.GET.get('date')
    
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    appointments = Appointment.objects.filter(
        vet=vet,
        date__date=selected_date
    ).select_related('pet').order_by('date')
    
    data = {
        'vet': vet.name,
        'date': selected_date.isoformat(),
        'appointments': [
            {
                'id': apt.id,
                'pet_name': apt.pet.name,
                'time': apt.date.strftime('%H:%M'),
                'duration': apt.duration_minutes,
                'reason': apt.reason,
                'status': apt.status,
            }
            for apt in appointments
        ]
    }
    
    return JsonResponse(data)