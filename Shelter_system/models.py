import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

class PetModel:
    def __init__(self, db):
        self.db = db
    
    def get_all_pets(self):
        conn = self.db.get_connection()
        pets = conn.execute('SELECT * FROM pets ORDER BY created_at DESC').fetchall()
        conn.close()
        return [dict(pet) for pet in pets]
    
    def get_pet_by_id(self, pet_id):
        conn = self.db.get_connection()
        pet = conn.execute('SELECT * FROM pets WHERE id = ?', (pet_id,)).fetchone()
        conn.close()
        return dict(pet) if pet else None
    
    def add_pet(self, pet_data):
        conn = self.db.get_connection()
        cursor = conn.execute('''
            INSERT INTO pets (name, species, breed, age, gender, status, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            pet_data['name'], pet_data['species'], pet_data.get('breed', ''),
            pet_data['age'], pet_data['gender'], pet_data.get('status', 'available'),
            pet_data.get('description', '')
        ))
        pet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return pet_id
    
    def update_pet(self, pet_id, pet_data):
        conn = self.db.get_connection()
        conn.execute('''
            UPDATE pets SET 
                name=?, species=?, breed=?, age=?, gender=?, status=?, description=?
            WHERE id=?
        ''', (
            pet_data['name'], pet_data['species'], pet_data.get('breed', ''),
            pet_data['age'], pet_data['gender'], pet_data.get('status', 'available'),
            pet_data.get('description', ''), pet_id
        ))
        conn.commit()
        conn.close()
    
    def delete_pet(self, pet_id):
        conn = self.db.get_connection()
        conn.execute('DELETE FROM pets WHERE id = ?', (pet_id,))
        conn.commit()
        conn.close()