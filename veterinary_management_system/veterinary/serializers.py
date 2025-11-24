from rest_framework import serializers
from .models import Vet, Pet, MedicalRecord, Vaccine, Appointment

class VetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vet
        fields = '__all__'

class PetSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = Pet
        fields = '__all__'

class MedicalRecordSerializer(serializers.ModelSerializer):
    vet_name = serializers.CharField(source='vet.name', read_only=True)
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'

class VaccineSerializer(serializers.ModelSerializer):
    vet_name = serializers.CharField(source='administered_by.name', read_only=True)
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    
    class Meta:
        model = Vaccine
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    vet_name = serializers.CharField(source='vet.name', read_only=True)
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    owner_name = serializers.CharField(source='pet.owner_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['google_calendar_event_id']

class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['pet', 'vet', 'date', 'duration_minutes', 'reason', 'notes']
    
    def validate_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Appointment date cannot be in the past")
        return value