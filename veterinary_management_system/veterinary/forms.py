from django import forms
from django.utils import timezone
from .models import Pet, Vet, Appointment, MedicalRecord, Vaccine

class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            'external_pet_id', 'name', 'species', 'breed', 'sex',
            'date_of_birth', 'color', 'weight', 'microchip_id',
            'owner_name', 'owner_email', 'owner_phone', 'owner_address',
            'emergency_contact', 'allergies', 'chronic_conditions', 'special_notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'max': timezone.now().date().isoformat()
            }),
            'external_pet_id': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Only if pet exists in external system'
            }),
            'owner_address': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Enter full address...'
            }),
            'allergies': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'List any known allergies...'
            }),
            'chronic_conditions': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'List any chronic conditions...'
            }),
            'special_notes': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'Any special care instructions...'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter pet name'
            }),
            'owner_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter owner full name'
            }),
            'owner_email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'owner@example.com'
            }),
            'owner_phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+1 (555) 123-4567'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact name and phone'
            }),
            'microchip_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Microchip ID if available'
            }),
            'breed': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Labrador Retriever, Persian'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Black, Brown and White'
            }),
        }
    
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # Make external_pet_id not required
    self.fields['external_pet_id'].required = False
    
    for field in self.fields:
        if 'class' not in self.fields[field].widget.attrs:
            self.fields[field].widget.attrs['class'] = 'form-control'

    # Add Bootstrap form-select class to choice fields
    choice_fields = ['species', 'sex']
    for field_name in choice_fields:
        self.fields[field_name].widget.attrs['class'] = 'form-select'

class VetForm(forms.ModelForm):
    class Meta:
        model = Vet
        fields = [
            'name', 'email', 'specialization', 'phone', 'license_number',
            'bio', 'working_hours_start', 'working_hours_end', 'is_active'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control',
                'placeholder': 'Brief professional biography...'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dr. Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'vet@clinic.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State license number'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'
        
        # Style choice fields
        self.fields['specialization'].widget.attrs['class'] = 'form-select'
        self.fields['is_active'].widget.attrs['class'] = 'form-check-input'

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['pet', 'vet', 'date', 'duration_minutes', 'reason', 'status', 'notes']
        widgets = {
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 
                'class': 'form-control',
                'min': timezone.now().strftime('%Y-%m-%dT%H:%M')
            }),
            'reason': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Annual checkup, Vaccination, Emergency visit'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Any additional notes or special instructions...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pet'].queryset = Pet.objects.all().order_by('name')
        self.fields['vet'].queryset = Vet.objects.filter(is_active=True).order_by('name')
        
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'
        
        # Style choice fields
        self.fields['duration_minutes'].widget.attrs['class'] = 'form-select'
        self.fields['status'].widget.attrs['class'] = 'form-select'
        self.fields['pet'].widget.attrs['class'] = 'form-select'
        self.fields['vet'].widget.attrs['class'] = 'form-select'

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            'vet', 'visit_date', 'weight', 'temperature', 
            'heart_rate', 'respiratory_rate', 'diagnosis', 
            'symptoms', 'treatment', 'medications', 'notes',
            'follow_up_required', 'follow_up_date'
        ]
        widgets = {
            'visit_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'max': timezone.now().date().isoformat()
            }),
            'follow_up_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'diagnosis': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Primary diagnosis and findings...'
            }),
            'symptoms': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'Observed symptoms and clinical signs...'
            }),
            'treatment': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Treatment provided and procedures performed...'
            }),
            'medications': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'Medications prescribed with dosage...'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Additional clinical notes and recommendations...'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Weight in kg/lbs'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Temperature in °C/°F'
            }),
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'BPM'
            }),
            'respiratory_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Breaths per minute'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vet'].queryset = Vet.objects.filter(is_active=True).order_by('name')
        
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'
        
        self.fields['vet'].widget.attrs['class'] = 'form-select'
        self.fields['follow_up_required'].widget.attrs['class'] = 'form-check-input'

class VaccineForm(forms.ModelForm):
    class Meta:
        model = Vaccine
        fields = ['vaccine_type', 'vaccination_date', 'next_due_date', 'administered_by', 'batch_number', 'notes']
        widgets = {
            'vaccination_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'max': timezone.now().date().isoformat()
            }),
            'next_due_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'Any notes about the vaccination...'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vaccine batch/lot number'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['administered_by'].queryset = Vet.objects.filter(is_active=True).order_by('name')
        
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'
        
        self.fields['vaccine_type'].widget.attrs['class'] = 'form-select'
        self.fields['administered_by'].widget.attrs['class'] = 'form-select'

class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search pets, owners, appointments, veterinarians...',
            'aria-label': 'Search'
        })
    )
    
    search_type = forms.ChoiceField(
        choices=[
            ('all', 'All Categories'),
            ('pets', 'Pets'),
            ('owners', 'Owners'),
            ('appointments', 'Appointments'),
            ('vets', 'Veterinarians'),
        ],
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )