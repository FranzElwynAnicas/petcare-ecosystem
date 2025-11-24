from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('adopter', 'Pet Adopter'),
        ('shelter', 'Shelter Staff'),
        ('vet', 'Veterinarian'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='adopter')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    job = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    barangay = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, default='Philippines')

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Automatically create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

class Pet(models.Model):
    PET_TYPES = [
        ("dog", "Dog"),
        ("cat", "Cat"),
    ]

    name = models.CharField(max_length=100)
    age = models.IntegerField()
    pet_type = models.CharField(max_length=10, choices=PET_TYPES)
    breed = models.CharField(max_length=100)
    description = models.TextField()
    image_url = models.CharField(max_length=255, blank=True)
    # Add created_at field
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name

class AdoptionRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE)
    shelter_pet_id = models.IntegerField(null=True, blank=True)  # ID from shelter system
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.pet.name}"

class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('adoption', 'Adoption Inquiry'),
        ('volunteer', 'Volunteer Opportunity'),
        ('donation', 'Donation Question'),
        ('support', 'Technical Support'),
        ('partnership', 'Partnership'),
        ('other', 'Other'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    message = models.TextField()
    newsletter_subscription = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.subject}"
    
    class Meta:
        ordering = ['-created_at']

class AdoptionApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Adoption Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shelter_pet_id = models.IntegerField()  
    pet_name = models.CharField(max_length=100)
    pet_species = models.CharField(max_length=10)
    applicant_name = models.CharField(max_length=200)
    applicant_email = models.EmailField()
    applicant_phone = models.CharField(max_length=20)
    applicant_address = models.TextField()
    family_members = models.TextField(help_text="Number and ages of family members")
    previous_pets = models.TextField(help_text="Experience with previous pets")
    home_type = models.CharField(max_length=100, help_text="Apartment, house, etc.")
    yard_info = models.TextField(help_text="Information about yard/outdoor space")
    work_schedule = models.TextField(help_text="Work hours and schedule")
    pet_alone_time = models.TextField(help_text="How long pet would be alone daily")
    vet_contact = models.TextField(blank=True, help_text="Veterinarian contact information")
    references = models.TextField(help_text="Personal references")
    message = models.TextField(blank=True, help_text="Additional comments")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.applicant_name} - {self.pet_name} ({self.status})"

class VetAppointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vet_appointments')
    vet_appointment_id = models.IntegerField(null=True, blank=True)  # ID from vet system
    pet_name = models.CharField(max_length=100)
    species = models.CharField(max_length=50, default='dog')
    breed = models.CharField(max_length=100, blank=True, null=True)
    vet_name = models.CharField(max_length=255, default='Dr. Unknown')
    appointment_date = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    duration_minutes = models.IntegerField(default=30)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment_date']
        verbose_name = "Vet Appointment"
        verbose_name_plural = "Vet Appointments"

    def __str__(self):
        return f"{self.pet_name} - {self.appointment_date.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.appointment_date > timezone.now() and self.status in ['scheduled', 'confirmed']

    @property
    def is_today(self):
        from django.utils import timezone
        return self.appointment_date.date() == timezone.now().date()