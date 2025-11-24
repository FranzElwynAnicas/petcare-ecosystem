# core/shelter_api.py
import requests
from django.conf import settings

class ShelterAPI:
    def __init__(self):
        self.base_url = "http://localhost:5001/api/adoption"  # Flask app URL
    
    def get_available_pets(self):
        """Fetch available pets from shelter system"""
        try:
            response = requests.get(f"{self.base_url}/pets")
            if response.status_code == 200:
                return response.json()
            return []
        except requests.exceptions.RequestException:
            return []
    
    def get_pet_details(self, pet_id):
        """Fetch detailed pet information"""
        try:
            response = requests.get(f"{self.base_url}/pets/{pet_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException:
            return None

# Singleton instance
shelter_api = ShelterAPI()