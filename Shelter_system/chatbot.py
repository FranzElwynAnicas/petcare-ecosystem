import sqlite3
import re
from datetime import datetime

class ShelterChatbot:
    def __init__(self, db_path='instance/shelter.db'):
        self.db_path = db_path
    
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def process_message(self, message):
        message = message.lower().strip()
        
        # Statistics queries
        if any(word in message for word in ['how many', 'statistics', 'stats', 'total']):
            return self.get_pet_statistics()
        
        # Available pets
        elif any(word in message for word in ['available', 'show pets', 'list pets']):
            return self.get_available_pets()
        
        # Search by name
        elif 'find' in message or 'search' in message:
            return self.search_pet_by_name(message)
        
        # Species specific
        elif 'dog' in message:
            return self.get_pets_by_species('dog')
        elif 'cat' in message:
            return self.get_pets_by_species('cat')
        
        # Behavioral traits
        elif any(word in message for word in ['kids', 'children', 'family']):
            return self.get_pets_good_with_kids()
        
        # Recent activity
        elif any(word in message for word in ['activity', 'recent', 'log']):
            return self.get_recent_activity()
        
        # Help
        elif any(word in message for word in ['help', 'what can you do']):
            return self.get_help_message()
        
        else:
            return "I can help you with pet information! Try asking about available pets, statistics, or search for a specific pet."
    
    def get_pet_statistics(self):
        conn = self.get_db_connection()
        
        total = conn.execute('SELECT COUNT(*) FROM pets').fetchone()[0]
        available = conn.execute('SELECT COUNT(*) FROM pets WHERE status = "available"').fetchone()[0]
        dogs = conn.execute('SELECT COUNT(*) FROM pets WHERE species = "dog"').fetchone()[0]
        cats = conn.execute('SELECT COUNT(*) FROM pets WHERE species = "cat"').fetchone()[0]
        
        conn.close()
        
        return f"""🏠 Shelter Statistics:
• Total Pets: {total}
• Available for Adoption: {available}
• Dogs: {dogs}
• Cats: {cats}

Use "Show available pets" to see who's ready for a new home!"""
    
    def get_available_pets(self):
        conn = self.get_db_connection()
        
        pets = conn.execute('''
            SELECT * FROM pets 
            WHERE status = "available" 
            ORDER BY created_at DESC 
            LIMIT 10
        ''').fetchall()
        conn.close()
        
        if not pets:
            return "No pets are currently available for adoption. Check back soon!"
        
        response = "🐾 Available Pets:\n\n"
        for pet in pets:
            response += f"• {pet['name']} - {pet['species'].title()} ({pet['breed'] or 'Mixed'}), {pet['age']} years old\n"
            response += f"  Status: {pet['status'].title()}\n\n"
        
        return response
    
    def search_pet_by_name(self, message):
        name_match = re.search(r'find\s+(\w+)', message) or re.search(r'search\s+for\s+(\w+)', message)
        if name_match:
            pet_name = name_match.group(1)
            
            conn = self.get_db_connection()
            pets = conn.execute(
                'SELECT * FROM pets WHERE name LIKE ?', 
                (f'%{pet_name}%',)
            ).fetchall()
            conn.close()
            
            if not pets:
                return f"No pets found with name containing '{pet_name}'."
            
            response = f"🔍 Found {len(pets)} pet(s):\n\n"
            for pet in pets:
                response += f"• {pet['name']} - {pet['species'].title()} ({pet['breed'] or 'Mixed'})\n"
                response += f"  Age: {pet['age']} years, Status: {pet['status'].title()}\n\n"
            
            return response
        
        return "Who are you looking for? Try 'Find Max' or 'Search for Buddy'"
    
    def get_pets_by_species(self, species):
        conn = self.get_db_connection()
        
        pets = conn.execute('''
            SELECT * FROM pets 
            WHERE species = ? AND status = "available" 
            ORDER BY name
        ''', (species,)).fetchall()
        conn.close()
        
        if not pets:
            return f"No available {species}s at the moment."
        
        species_emoji = "🐕" if species == 'dog' else "🐈"
        response = f"{species_emoji} Available {species.title()}s:\n\n"
        for pet in pets:
            response += f"• {pet['name']} - {pet['breed'] or 'Mixed'}, {pet['age']} years old\n"
        
        return response
    
    def get_pets_good_with_kids(self):
        conn = self.get_db_connection()
        
        pets = conn.execute('''
            SELECT * FROM pets 
            WHERE good_with_kids = 1 AND status = "available" 
            ORDER BY species, name
        ''').fetchall()
        conn.close()
        
        if not pets:
            return "No pets specifically noted as good with kids are currently available."
        
        response = "👶 Pets Good with Kids:\n\n"
        for pet in pets:
            species_emoji = "🐕" if pet['species'] == 'dog' else "🐈"
            response += f"• {species_emoji} {pet['name']} - {pet['breed'] or 'Mixed'}, {pet['age']} years\n"
        
        return response
    
    def get_recent_activity(self):
        conn = self.get_db_connection()
        
        logs = conn.execute('''
            SELECT al.*, p.name as pet_name 
            FROM activity_logs al 
            LEFT JOIN pets p ON al.pet_id = p.id 
            ORDER BY al.timestamp DESC 
            LIMIT 5
        ''').fetchall()
        conn.close()
        
        if not logs:
            return "No recent activity to show."
        
        response = "📝 Recent Activity:\n\n"
        for log in logs:
            timestamp = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%m/%d')
            action = log['action'].replace('_', ' ').title()
            pet_info = f" ({log['pet_name']})" if log['pet_name'] else ""
            response += f"• {timestamp}: {action}{pet_info}\n"
            if log['description']:
                response += f"  {log['description']}\n"
        
        return response
    
    def get_help_message(self):
        return """🤖 Shelter Assistant Help:

📊 **Statistics & Overview**
• "How many pets?" - Get shelter statistics
• "Statistics" - View total pets, available, etc.

🐾 **Find Pets**
• "Show available pets" - List all available animals
• "Dogs" or "Cats" - Show available by species
• "Find [name]" - Search for specific pet
• "Pets good with kids" - Family-friendly pets

📝 **Shelter Operations**
• "Recent activity" - View recent shelter logs
• "Help" - Show this help message

Try asking me anything about our shelter pets!"""