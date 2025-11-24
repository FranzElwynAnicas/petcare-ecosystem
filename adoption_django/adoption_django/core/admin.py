# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from .models import UserProfile, ContactMessage, Pet, AdoptionRequest, AdoptionApplication
from django.contrib.auth.models import User
from .shelter_api import shelter_api

# Add this function to admin.py instead of importing from views
def get_shelter_api_stats():
    """Get shelter stats directly without circular imports"""
    import requests
    try:
        response = requests.get("http://localhost:5001/api/adoption/pets", timeout=5)
        if response.status_code == 200:
            pets = response.json()
            pets_count = len(pets) if pets else 0
            dogs_count = len([p for p in pets if p.get('species') == 'dog']) if pets else 0
            cats_count = len([p for p in pets if p.get('species') == 'cat']) if pets else 0
            return pets_count, dogs_count, cats_count
    except:
        pass
    return 0, 0, 0

# Your existing admin classes remain the same...
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'subject', 'created_at', 'is_read', 'mark_as_read_action']
    list_filter = ['subject', 'is_read', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'message']
    readonly_fields = ['created_at']
    list_per_page = 20
    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read_action(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green; font-weight: bold;">✓ Read</span>')
        else:
            return format_html('<span style="color: #f59e0b; font-weight: bold;">● Unread</span>')
    mark_as_read_action.short_description = 'Status'

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} message(s) marked as read.")
    mark_as_read.short_description = "Mark selected messages as read"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} message(s) marked as unread.")
    mark_as_unread.short_description = "Mark selected messages as unread"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'city', 'phone', 'created_date']
    list_filter = ['role', 'city']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

    def created_date(self, obj):
        return obj.user.date_joined.strftime("%Y-%m-%d")
    created_date.short_description = 'Joined'

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['name', 'age', 'pet_type', 'breed', 'created_at']
    list_filter = ['pet_type']
    search_fields = ['name', 'breed']

    def created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d") if obj.created_at else "N/A"
    created_at.short_description = 'Created'

@admin.register(AdoptionRequest)
class AdoptionRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'pet', 'status', 'created_at', 'short_message']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'pet__name']

    def short_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    short_message.short_description = 'Message'

@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant_name', 'pet_name', 'status', 'applied_date', 'user', 'approval_actions']
    list_filter = ['status', 'applied_date', 'pet_species']
    search_fields = ['applicant_name', 'pet_name', 'user__username', 'applicant_email']
    readonly_fields = ['applied_date', 'updated_date', 'application_summary']
    list_editable = ['status']
    actions = ['approve_applications', 'reject_applications']
    list_per_page = 20

    fieldsets = (
        ('Application Information', {
            'fields': ('user', 'applicant_name', 'applicant_email', 'applicant_phone', 'status')
        }),
        ('Pet Information', {
            'fields': ('shelter_pet_id', 'pet_name', 'pet_species')
        }),
        ('Application Summary', {
            'fields': ('application_summary',)
        }),
        ('Timestamps', {
            'fields': ('applied_date', 'updated_date'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def approval_actions(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<div style="display: flex; gap: 5px;">'
                '<a class="button" style="background: #28a745; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none;" href="{}">✓ Approve</a>'
                '<a class="button" style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none;" href="{}">✗ Reject</a>'
                '</div>',
                f'{obj.id}/approve/',
                f'{obj.id}/reject/'
            )
        status_color = {
            'approved': '#28a745',
            'rejected': '#dc3545',
            'pending': '#ffc107'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            status_color.get(obj.status, '#6c757d'),
            obj.get_status_display().upper()
        )
    approval_actions.short_description = 'Actions'

    def application_summary(self, obj):
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>Applied:</strong> {}<br>'
            '<strong>Pet:</strong> {} ({})<br>'
            '<strong>Contact:</strong> {} | {}<br>'
            '<strong>Shelter Pet ID:</strong> {}<br>'
            '<strong>Django App ID:</strong> {}'
            '</div>',
            obj.applied_date.strftime("%Y-%m-%d %H:%M"),
            obj.pet_name, obj.pet_species.title(),
            obj.applicant_email, obj.applicant_phone or 'No phone',
            obj.shelter_pet_id,
            obj.id
        )
    application_summary.short_description = 'Quick Summary'

    def approve_applications(self, request, queryset):
        for application in queryset:
            self._send_to_shelter_api(application, 'approved')
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} application(s) approved and sent to shelter system!')
    approve_applications.short_description = "Approve selected applications"

    def reject_applications(self, request, queryset):
        for application in queryset:
            self._send_to_shelter_api(application, 'rejected')
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} application(s) rejected and notified shelter system.')
    reject_applications.short_description = "Reject selected applications"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/approve/', self.admin_site.admin_view(self.approve_application),
                name='core_adoptionapplication_approve'),
            path('<path:object_id>/reject/', self.admin_site.admin_view(self.reject_application),
                name='core_adoptionapplication_reject'),
        ]
        return custom_urls + urls

    def approve_application(self, request, object_id):
        application = self.get_object(request, object_id)
        if application:
            # Send to shelter API first
            success = self._send_to_shelter_api(application, 'approved')

            # Update local status
            application.status = 'approved'
            application.save()

            if success:
                self.message_user(request, f'Application for {application.pet_name} has been approved and sent to shelter system!')
            else:
                self.message_user(request, 'Application approved locally but failed to send to shelter system.')
        return redirect('admin:core_adoptionapplication_changelist')

    def reject_application(self, request, object_id):
        application = self.get_object(request, object_id)
        if application:
            # Send to shelter API first
            success = self._send_to_shelter_api(application, 'rejected')

            # Update local status
            application.status = 'rejected'
            application.save()

            if success:
                self.message_user(request, f'Application for {application.pet_name} has been rejected and notified shelter system.')
            else:
                self.message_user(request, 'Application rejected locally but failed to notify shelter system.')
        return redirect('admin:core_adoptionapplication_changelist')

    def _send_to_shelter_api(self, application, action):
        """Send adoption status update to shelter API"""
        import requests
        import json

        try:
            # Prepare data for shelter API
            data = {
                'pet_id': application.shelter_pet_id,
                'status': action,
                'application_id': f'DJANGO-APP-{application.id}',
                'pet_name': application.pet_name,
                'applicant_name': application.applicant_name,
                'applicant_email': application.applicant_email,
                'decision_date': application.updated_date.isoformat() if application.updated_date else None
            }

            # Send to shelter API
            response = requests.post(
                'http://localhost:5001/api/adoption/update-status',
                json=data,
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                print(f"Successfully sent {action} status to shelter API for pet {application.shelter_pet_id}")
                return True
            else:
                print(f"Failed to send {action} status to shelter API. Status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to shelter API: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending to shelter API: {e}")
            return False

# Custom Admin Site
class ShelterAdminSite(admin.AdminSite):
    site_header = "Shelter Management System"
    site_title = "Shelter Management Admin"
    index_title = "Dashboard"
    site_url = "/"

    def index(self, request, extra_context=None):
        from django.contrib.auth.models import User
        from django.utils import timezone
        from datetime import timedelta
        
        # Get comprehensive statistics from LOCAL database
        contact_messages_count = ContactMessage.objects.count()
        unread_messages_count = ContactMessage.objects.filter(is_read=False).count()
        users_count = User.objects.count()
        staff_users_count = User.objects.filter(is_staff=True).count()

        # Get adoption applications from LOCAL AdoptionApplication model
        adoption_requests_count = AdoptionApplication.objects.count()
        pending_requests_count = AdoptionApplication.objects.filter(status="pending").count()

        # Get pets from SHELTER API (external) - use the local function
        pets_count, dogs_count, cats_count = get_shelter_api_stats()

        # Active users (logged in last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        active_users_count = User.objects.filter(last_login__gte=week_ago).count()

        recent_messages = ContactMessage.objects.all().order_by("-created_at")[:5]

        # Add application statistics
        approved_apps_count = AdoptionApplication.objects.filter(status='approved').count()
        rejected_apps_count = AdoptionApplication.objects.filter(status='rejected').count()
        completed_apps_count = AdoptionApplication.objects.filter(status='completed').count()

        extra_context = extra_context or {}
        extra_context.update({
            'contact_messages_count': contact_messages_count,
            'unread_messages_count': unread_messages_count,
            'users_count': users_count,
            'staff_users_count': staff_users_count,
            'adoption_requests_count': adoption_requests_count,
            'pending_requests_count': pending_requests_count,
            'pets_count': pets_count,
            'dogs_count': dogs_count,
            'cats_count': cats_count,
            'active_users_count': active_users_count,
            'recent_messages': recent_messages,
            'approved_apps_count': approved_apps_count,
            'rejected_apps_count': rejected_apps_count,
            'completed_apps_count': completed_apps_count,
        })

        return super().index(request, extra_context)

# Create custom admin site instance
shelter_admin_site = ShelterAdminSite(name="shelter_admin")

# Register models with custom admin site
shelter_admin_site.register(ContactMessage, ContactMessageAdmin)
shelter_admin_site.register(UserProfile, UserProfileAdmin)
shelter_admin_site.register(Pet, PetAdmin)
shelter_admin_site.register(AdoptionRequest, AdoptionRequestAdmin)
shelter_admin_site.register(AdoptionApplication, AdoptionApplicationAdmin)
shelter_admin_site.register(User, admin.ModelAdmin)