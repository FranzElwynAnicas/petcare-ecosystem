"""
Populate shelter system with user data
"""
import sys
import os
import sqlite3
import hashlib
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('instance/shelter.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_user_exists(username, email):
    """Check if a user already exists"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT id FROM users WHERE username = ? OR email = ?', 
        (username, email)
    ).fetchone()
    conn.close()
    return user is not None

# User data to populate
USERS = [
    {
        'username': 'Franz',
        'email': 'franzanicas@gmail.com',
        'full_name': 'Franz Anicas',
        'role': 'staff',
        'password': 'admin123'
    },
    {
        'username': 'Kamil',
        'email': 'kamilogoy@gmail.com',
        'full_name': 'Kamil Ogoy',
        'role': 'staff',
        'password': 'admin123'
    },
    {
        'username': 'Bella',
        'email': 'bellawhitehead@gmail.com',
        'full_name': 'Bella Whitehead',
        'role': 'staff',
        'password': 'admin123'
    },
    {
        'username': 'Sora',
        'email': 'soraserizawa@gmail.com',
        'full_name': 'Sora Serizawa',
        'role': 'staff',
        'password': 'admin123'
    }
]

def populate_users():
    """Populate database with user data"""
    print("\n=== Populating Shelter with User Data ===")
    
    conn = get_db_connection()
    
    try:
        users_created = 0
        users_skipped = 0
        
        for user_data in USERS:
            # Check if user already exists
            if check_user_exists(user_data['username'], user_data['email']):
                print(f"⚠ User {user_data['username']} already exists, skipping...")
                users_skipped += 1
                continue
            
            # Create user
            conn.execute('''
                INSERT INTO users (username, password_hash, email, full_name, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_data['username'],
                hash_password(user_data['password']),
                user_data['email'],
                user_data['full_name'],
                user_data['role'],
                1  # is_active
            ))
            
            print(f"✓ Created user: {user_data['full_name']} ({user_data['username']})")
            users_created += 1
        
        conn.commit()
        
        print(f"\n{'='*50}")
        print(f"🎉 User population completed!")
        print(f"  Users created: {users_created}")
        print(f"  Users skipped: {users_skipped}")
        print(f"  Total users in system: {conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
        print(f"\n📋 Login credentials (all use 'admin123'):")
        for user_data in USERS:
            print(f"  - {user_data['username']} / admin123")
        print(f"{'='*50}\n")
        
    except Exception as e:
        print(f"❌ Error populating users: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    populate_users()