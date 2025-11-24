# core/vet_api.py
import requests
from datetime import datetime, timedelta
from .models import VetAppointment


class VetAPI:
    def __init__(self):
        self.base_url = "http://localhost:6001"
        self.timeout = 10

    def test_connection(self):
        """Test if vet system is reachable"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=self.timeout)
            print(f"✅ Vet system connection test: {response.status_code}")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"❌ Vet system connection failed: {e}")
            return False

    def create_appointment(self, appointment_data, user):
        """Create a new vet appointment and store locally"""
        print("🚀 Starting appointment creation...")
        print(f"📦 Appointment data: {appointment_data}")
        
        try:
            # Add the preferred date
            next_date = datetime.now() + timedelta(days=3)
            next_date = next_date.replace(hour=10, minute=0, second=0, microsecond=0)

            full_data = {
                'pet_name': appointment_data['pet_name'],
                'owner_name': appointment_data['owner_name'],
                'owner_email': appointment_data['owner_email'],
                'owner_phone': appointment_data['owner_phone'],
                'reason': appointment_data.get('reason', 'Post-adoption health checkup'),
                'preferred_date': next_date.isoformat(),
                'species': appointment_data.get('species', 'dog'),
                'breed': appointment_data.get('breed', 'Unknown'),
                'pet_age': appointment_data.get('pet_age', 'Unknown'),
                'urgency': appointment_data.get('urgency', 'routine'),
                'duration_minutes': 30,
                'notes': f'Special notes: {appointment_data.get("special_notes", "None")}. Previous vet: {appointment_data.get("previous_vet", "None")}',
            }

            print(f"📤 Sending to vet system: {self.base_url}/api/create-appointment/")
            print(f"📝 Request data: {full_data}")

            response = requests.post(
                f"{self.base_url}/api/create-appointment/",
                json=full_data,
                timeout=self.timeout
            )
            
            print(f"📥 Vet API Response Status: {response.status_code}")
            print(f"📥 Vet API Response Content: {response.text}")
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    print(f"✅ Appointment created successfully: {result}")
                    
                    # Extract vet name from response
                    vet_name = "Unknown"
                    appointment_details = result.get('appointment_details', {})
                    
                    # Try different possible keys for vet name
                    if 'vet' in appointment_details:
                        vet_name = appointment_details['vet']
                    elif 'vet_name' in appointment_details:
                        vet_name = appointment_details['vet_name']
                    elif 'vet' in result:
                        vet_name = result['vet']
                    
                    # Remove "Dr." prefix if it's already included to avoid "Dr. Dr. Franz"
                    if vet_name.startswith('Dr. '):
                        vet_name = vet_name[4:]
                    
                    print(f"👨‍⚕️ Extracted vet name: {vet_name}")
                    
                    # Store appointment locally
                    local_appointment = VetAppointment.objects.create(
                        user=user,
                        vet_appointment_id=result.get('appointment_id'),
                        pet_name=appointment_data['pet_name'],
                        species=appointment_data.get('species', 'dog'),
                        breed=appointment_data.get('breed', 'Unknown'),
                        vet_name=vet_name,
                        appointment_date=next_date,
                        reason=appointment_data.get('reason', 'Post-adoption health checkup'),
                        status='scheduled',
                        duration_minutes=30,
                        notes=full_data['notes']
                    )
                    
                    print(f"💾 Stored locally with ID: {local_appointment.id}")
                    print(f"💾 Vet name stored: {local_appointment.vet_name}")
                    
                    return {
                        'success': True,
                        'appointment_id': result.get('appointment_id'),
                        'local_appointment_id': local_appointment.id,
                        'message': result.get('message', 'Appointment created successfully'),
                        'details': result.get('appointment_details', {})
                    }
                except Exception as e:
                    print(f"❌ Failed to parse JSON response or store locally: {e}")
                    return {
                        'success': False,
                        'error': f"Invalid response format from vet system: {e}"
                    }
            else:
                # Try to get error details from response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_data.get('detail', f"Vet system returned status: {response.status_code}"))
                except:
                    error_msg = f"Vet system returned status: {response.status_code}"
                
                print(f"❌ Vet system error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Cannot connect to vet system at {self.base_url}. Make sure it's running on port 6001."
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except requests.exceptions.Timeout as e:
            error_msg = "Vet system timeout - taking too long to respond"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def cancel_appointment(self, vet_appointment_id):
        """Cancel an appointment in the vet system"""
        try:
            print(f"🚫 Cancelling appointment in vet system: {vet_appointment_id}")
            
            response = requests.post(
                f"{self.base_url}/api/appointments/{vet_appointment_id}/cancel/",
                timeout=self.timeout
            )
            
            print(f"📥 Vet cancellation response: {response.status_code}")
            print(f"📥 Vet cancellation content: {response.text}")
            
            if response.status_code == 200:
                print(f"✅ Successfully cancelled appointment {vet_appointment_id} in vet system")
                return {
                    'success': True,
                    'message': 'Appointment cancelled in vet system'
                }
            else:
                error_msg = f"Vet system returned status: {response.status_code}"
                print(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def get_user_appointments(self, user):
        """Get all appointments for a user from local database"""
        try:
            appointments = VetAppointment.objects.filter(user=user).order_by('-appointment_date')
            print(f"📋 Found {appointments.count()} local appointments for {user.email}")
            
            # Convert to the format expected by the template
            appointment_list = []
            for apt in appointments:
                appointment_list.append({
                    'id': apt.id,
                    'vet_appointment_id': apt.vet_appointment_id,
                    'pet_name': apt.pet_name,
                    'vet_name': apt.vet_name,
                    'date': apt.appointment_date.isoformat(),
                    'reason': apt.reason,
                    'status': apt.status,
                    'duration': apt.duration_minutes,
                    'species': apt.species
                })
            
            return appointment_list
            
        except Exception as e:
            print(f"❌ Error getting user appointments from local DB: {e}")
            return []


# Singleton instance
vet_api = VetAPI()