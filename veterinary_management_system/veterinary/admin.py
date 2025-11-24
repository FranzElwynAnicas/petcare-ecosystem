from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Vet, Pet, MedicalRecord, Vaccine, Appointment

@admin.register(Vet)
class VetAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'specialization', 'phone', 'is_active')
    list_filter = ('specialization', 'is_active')
    search_fields = ('name', 'email', 'specialization')
    list_editable = ('is_active',)

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'breed', 'owner_name', 'age')
    list_filter = ('species', 'sex')
    search_fields = ('name', 'owner_name', 'microchip_id')
    readonly_fields = ('age', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('external_pet_id', 'name', 'species', 'breed', 'sex', 'date_of_birth', 'color', 'weight')
        }),
        ('Owner Information', {
            'fields': ('owner_name', 'owner_email', 'owner_phone', 'owner_address', 'emergency_contact')
        }),
        ('Medical Information', {
            'fields': ('allergies', 'chronic_conditions', 'microchip_id'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('pet', 'vet', 'visit_date', 'diagnosis')
    list_filter = ('visit_date', 'vet')
    search_fields = ('pet__name', 'diagnosis')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('pet', 'vet', 'visit_date')
        }),
        ('Vital Signs', {
            'fields': ('weight', 'temperature', 'heart_rate', 'respiratory_rate'),
            'classes': ('collapse',)
        }),
        ('Medical Information', {
            'fields': ('diagnosis', 'symptoms', 'treatment', 'medications', 'notes')
        }),
        ('Follow-up', {
            'fields': ('follow_up_required', 'follow_up_date'),
            'classes': ('collapse',)
        })
    )

@admin.register(Vaccine)
class VaccineAdmin(admin.ModelAdmin):
    list_display = ('pet', 'vaccine_type', 'vaccination_date', 'next_due_date', 'administered_by')
    list_filter = ('vaccine_type', 'vaccination_date')
    search_fields = ('pet__name', 'vaccine_type')
    
    def is_overdue(self, obj):
        if obj.next_due_date:
            from django.utils import timezone
            return obj.next_due_date < timezone.now().date()
        return False
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('pet', 'vet', 'date', 'reason', 'status')
    list_filter = ('status', 'date', 'vet')
    search_fields = ('pet__name', 'reason', 'vet__name')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('pet', 'vet', 'date', 'duration_minutes', 'reason', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes', 'google_calendar_event_id'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )