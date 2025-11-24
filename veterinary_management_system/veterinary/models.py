from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Vet(BaseModel):
    SPECIALIZATION_CHOICES = [
        ('general', 'General Practice'),
        ('surgery', 'Surgery'),
        ('dentistry', 'Dentistry'),
        ('dermatology', 'Dermatology'),
        ('ophthalmology', 'Ophthalmology'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('oncology', 'Oncology'),
        ('emergency', 'Emergency Care'),
    ]
    
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES, default='general')
    phone = models.CharField(max_length=20, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='vet_profiles/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    working_hours_start = models.TimeField(default='08:00')
    working_hours_end = models.TimeField(default='17:00')
    
    class Meta:
        ordering = ['name']
        verbose_name = "Veterinarian"
        verbose_name_plural = "Veterinarians"

    def __str__(self):
        return f"Dr. {self.name} ({self.get_specialization_display()})"
    
    @property
    def upcoming_appointments(self):
        return self.appointments.filter(
            date__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        ).order_by('date')
    
    @property
    def todays_appointments(self):
        return self.appointments.filter(
            date__date=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        ).order_by('date')

class Pet(BaseModel):
    SEX_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('unknown', 'Unknown'),
    ]
    
    SPECIES_CHOICES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('rabbit', 'Rabbit'),
        ('hamster', 'Hamster'),
        ('guinea_pig', 'Guinea Pig'),
        ('reptile', 'Reptile'),
        ('other', 'Other'),
    ]

    # External system integration
    external_pet_id = models.IntegerField(
        unique=True,
        blank=True,
        null=True,  # Make it nullable
        help_text="ID of pet from external system (e.g., Shelter Database) - Optional"
    )
    
    # Basic information
    name = models.CharField(max_length=255)
    species = models.CharField(max_length=50, choices=SPECIES_CHOICES, default='dog')
    breed = models.CharField(max_length=100, blank=True, null=True)
    sex = models.CharField(max_length=10, choices=SEX_CHOICES)
    date_of_birth = models.DateField(blank=True, null=True)
    color = models.CharField(max_length=100, blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    microchip_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    # Owner information
    owner_name = models.CharField(max_length=255)
    owner_email = models.EmailField(blank=True, null=True)
    owner_phone = models.CharField(max_length=20, blank=True, null=True)
    owner_address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=255, blank=True, null=True)
    
    # Medical information
    allergies = models.TextField(blank=True, null=True)
    chronic_conditions = models.TextField(blank=True, null=True)
    special_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Pet"
        verbose_name_plural = "Pets"

    def __str__(self):
        return f"{self.name} ({self.owner_name})"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def last_appointment(self):
        return self.appointments.filter(status='completed').order_by('-date').first()
    
    @property
    def upcoming_appointment(self):
        return self.appointments.filter(
            status__in=['scheduled', 'confirmed'],
            date__gte=timezone.now()
        ).order_by('date').first()

class MedicalRecord(BaseModel):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='medical_records')
    vet = models.ForeignKey(Vet, on_delete=models.CASCADE)
    visit_date = models.DateField(default=timezone.now)
    
    # Vital signs
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    heart_rate = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(300)])
    respiratory_rate = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(200)])
    
    # Medical information
    diagnosis = models.TextField()
    symptoms = models.TextField(blank=True, null=True)
    treatment = models.TextField(blank=True, null=True)
    medications = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    
    class Meta:
        ordering = ['-visit_date']
        verbose_name = "Medical Record"
        verbose_name_plural = "Medical Records"

    def __str__(self):
        return f"Medical record for {self.pet.name} on {self.visit_date}"
    
    def clean(self):
        if self.follow_up_required and not self.follow_up_date:
            raise ValidationError('Follow-up date is required when follow-up is needed.')

class Vaccine(BaseModel):
    VACCINE_TYPES = [
        ('rabies', 'Rabies'),
        ('distemper', 'Distemper'),
        ('parvo', 'Parvovirus'),
        ('hepatitis', 'Hepatitis'),
        ('leptospirosis', 'Leptospirosis'),
        ('bordetella', 'Bordetella'),
        ('feline_leukaemia', 'Feline Leukaemia'),
        ('feline_viral_rhinotracheitis', 'Feline Viral Rhinotracheitis'),
        ('canine_parainfluenza', 'Canine Parainfluenza'),
        ('lyme', 'Lyme Disease'),
    ]
    
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vaccines')
    vaccine_type = models.CharField(max_length=50, choices=VACCINE_TYPES)
    vaccination_date = models.DateField()
    next_due_date = models.DateField(blank=True, null=True)
    administered_by = models.ForeignKey(Vet, on_delete=models.SET_NULL, null=True, blank=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-vaccination_date']
        verbose_name = "Vaccine Record"
        verbose_name_plural = "Vaccine Records"

    def __str__(self):
        return f"{self.vaccine_type} - {self.pet.name}"
    
    @property
    def is_overdue(self):
        if self.next_due_date:
            return self.next_due_date < timezone.now().date()
        return False
    
    @property
    def is_due_soon(self):
        if self.next_due_date:
            thirty_days_from_now = timezone.now().date() + timezone.timedelta(days=30)
            return self.next_due_date <= thirty_days_from_now
        return False

class Appointment(BaseModel):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    vet = models.ForeignKey(Vet, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30, choices=[(30, '30 minutes'), (60, '60 minutes'), (90, '90 minutes')])
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"

    def __str__(self):
        return f"Appointment for {self.pet.name} with Dr. {self.vet.name} on {self.date}"
    
    def clean(self):
        if self.date:
            # Ensure time is between 8:00 and 20:00 (8am-8pm)
            hour = self.date.hour
            if hour < 8 or hour > 20:
                raise ValidationError('Appointment time must be between 8am and 8pm.')
            
            # Check for overlapping appointments for the same vet
            overlapping = Appointment.objects.filter(
                vet=self.vet,
                date__date=self.date.date(),
                date__time__range=[
                    (self.date - timezone.timedelta(minutes=self.duration_minutes)).time(),
                    (self.date + timezone.timedelta(minutes=self.duration_minutes)).time()
                ],
                status__in=['scheduled', 'confirmed']
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError('This vet already has an appointment at the selected time.')
    
    @property
    def end_time(self):
        return self.date + timezone.timedelta(minutes=self.duration_minutes)
    
    @property
    def is_upcoming(self):
        return self.date > timezone.now() and self.status in ['scheduled', 'confirmed']
    
    @property
    def is_today(self):
        return self.date.date() == timezone.now().date()