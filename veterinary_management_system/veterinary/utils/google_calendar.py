from datetime import timedelta
from django.conf import settings
import os

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False

def get_calendar_service():
    """
    Load stored user credentials and return a Google Calendar service instance.
    """
    if not GOOGLE_CALENDAR_AVAILABLE:
        print("Google Calendar packages not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return None

    # scopes required for calendar access
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    # Use Django's BASE_DIR to locate token.json
    token_path = os.path.join(settings.BASE_DIR, 'token.json')

    if not os.path.exists(token_path):
        print(f"token.json not found at {token_path}. Please run OAuth flow first to generate credentials.")
        return None

    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        print(f"Error initializing Google Calendar service: {e}")
        return None

def create_calendar_event(appointment):
    """
    Creates a Google Calendar event for a vet appointment.

    Args:
        appointment: Appointment model instance

    Returns:
        str: Event ID string or None on failure
    """
    service = get_calendar_service()
    if not service:
        return None

    try:
        # Assume 30-minute appointment by default
        start = appointment.date.isoformat()
        end_dt = appointment.date + timedelta(minutes=30)
        end = end_dt.isoformat()

        event = {
            'summary': f"Vet Appointment - Pet #{appointment.pet_id}",
            'description': (
                f"Reason: {appointment.reason}\n"
                f"Vet: {appointment.vet.name}\n"
                f"Specialization: {appointment.vet.specialization or 'General'}"
            ),
            'start': {
                'dateTime': start,
                'timeZone': 'America/Chicago', # update if needed
            },
            'end': {
                'dateTime': end,
                'timeZone': 'America/Chicago',
            },
        }
        
        created_event = service.events().insert(
            calendarId='primary', 
            body=event
        ).execute()
        return created_event.get('id')
    except Exception as e:
        print(f"Error creating calendar event: {e}")
        return None

def update_calendar_event(event_id, appointment):
    """ 
    Updates an existing Google Calendar event.

    Args:
        event_id: Google Calendar event ID
        appointment: Updated Appointment model instance

    Returns:
        bool: True if successful, False otherwise
    """ 
    service = get_calendar_service()
    if not service:
        return False

    try:
        # Get existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # Update event details
        end_dt = appointment.date + timedelta(minutes=30)

        event['summary'] = f"Vet Appointment - Pet #{appointment.pet_id}"
        event['description'] = (
            f"Reason: {appointment.reason}\n"
            f"Vet: {appointment.vet.name}\n"
            f"Specialization: {appointment.vet.specialization or 'General'}"
        )
        event['start']['dateTime'] = appointment.date.isoformat()
        event['end']['dateTime'] = end_dt.isoformat()

        service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()
        return True
    except Exception as e:
        print(f"Error updating calendar event: {e}")
        return False

def delete_calendar_event(event_id):
    """  
    Deletes a Google Calendar event.

    Args:
        event_id: Google Calendar event ID

    Returns:
        bool: True if successful, False otherwise
    """  
    service = get_calendar_service()
    if not service:
        return False

    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting calendar event: {e}")
        return False