from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import sqlite3
import os
import hashlib
from datetime import datetime
from chatbot import ShelterChatbot
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shelter-system-secret-key-2024'
app.config['DATABASE'] = 'instance/shelter.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize chatbot and CORS
chatbot = ShelterChatbot()
CORS(app)

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(hashed_password, user_password):
    """Verify a stored password against one provided by user"""
    return hashed_password == hashlib.sha256(user_password.encode()).hexdigest()

def init_db():
    """Initialize database with required tables"""
    os.makedirs('instance', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'staff',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Pets table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            description TEXT,
            vaccinated BOOLEAN DEFAULT 0,
            spayed_neutered BOOLEAN DEFAULT 0,
            microchipped BOOLEAN DEFAULT 0,
            special_needs TEXT,
            good_with_kids BOOLEAN DEFAULT 1,
            good_with_pets BOOLEAN DEFAULT 1,
            good_with_dogs BOOLEAN DEFAULT 1,
            good_with_cats BOOLEAN DEFAULT 1,
            energy_level TEXT,
            image_url TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            intake_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Activity logs table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            user_id INTEGER,
            action TEXT NOT NULL,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Pet images table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pet_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            image_url TEXT NOT NULL,
            caption TEXT,
            is_primary BOOLEAN DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets (id)
        )
    ''')
    
    # Create default admin user if not exists
    admin_exists = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        conn.execute('''
            INSERT INTO users (username, password_hash, email, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            'admin', 
            hash_password('admin123'), 
            'admin@shelter.com', 
            'System Administrator', 
            'admin'
        ))
        print("✅ Default admin user created: username='admin', password='admin123'")
    
    conn.commit()
    conn.close()

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current user from session"""
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return dict(user) if user else None
    return None

# ===== ADOPTION API ENDPOINTS =====
@app.route('/api/adoption/test', methods=['GET'])
def api_adoption_test():
    """Test endpoint for adoption system"""
    return jsonify({
        'status': 'success', 
        'message': 'Shelter Adoption API is working!',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/adoption/pets', methods=['GET'])
def api_adoption_pets():
    """API: Get all available pets for adoption system"""
    try:
        conn = get_db_connection()
        
        # Get available pets with shelter information
        pets = conn.execute('''
            SELECT p.*, u.full_name as shelter_name, u.email as shelter_email
            FROM pets p 
            LEFT JOIN users u ON p.created_by = u.id 
            WHERE p.status = "available"
            ORDER BY p.created_at DESC
        ''').fetchall()
        
        # Get primary images for each pet
        pets_with_images = []
        for pet in pets:
            pet_dict = dict(pet)
            
            # Get primary image
            primary_image = conn.execute(
                'SELECT image_url FROM pet_images WHERE pet_id = ? AND is_primary = 1 LIMIT 1',
                (pet_dict['id'],)
            ).fetchone()
            
            if primary_image:
                pet_dict['primary_image'] = primary_image['image_url']
            else:
                # Get any image if no primary
                any_image = conn.execute(
                    'SELECT image_url FROM pet_images WHERE pet_id = ? LIMIT 1',
                    (pet_dict['id'],)
                ).fetchone()
                pet_dict['primary_image'] = any_image['image_url'] if any_image else None
            
            # Convert SQLite integers to Python booleans
            bool_fields = ['vaccinated', 'spayed_neutered', 'microchipped', 
                          'good_with_kids', 'good_with_pets', 'good_with_dogs', 'good_with_cats']
            for field in bool_fields:
                pet_dict[field] = bool(pet_dict[field]) if field in pet_dict else False
            
            pets_with_images.append(pet_dict)
        
        conn.close()
        return jsonify(pets_with_images)
        
    except Exception as e:
        print(f"Error in adoption pets API: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/adoption/pets/<int:pet_id>', methods=['GET'])
def api_adoption_pet_detail(pet_id):
    """API: Get specific pet details for adoption"""
    try:
        conn = get_db_connection()
        
        # Get pet details
        pet = conn.execute('''
            SELECT p.*, u.full_name as shelter_name, u.email as shelter_email
            FROM pets p 
            LEFT JOIN users u ON p.created_by = u.id 
            WHERE p.id = ?
        ''', (pet_id,)).fetchone()
        
        if not pet:
            conn.close()
            return jsonify({'error': 'Pet not found'}), 404
        
        pet_dict = dict(pet)
        
        # Get all images
        images = conn.execute(
            'SELECT image_url, caption, is_primary FROM pet_images WHERE pet_id = ?',
            (pet_id,)
        ).fetchall()
        pet_dict['images'] = [dict(img) for img in images]
        
        # Convert boolean fields
        bool_fields = ['vaccinated', 'spayed_neutered', 'microchipped', 
                      'good_with_kids', 'good_with_pets', 'good_with_dogs', 'good_with_cats']
        for field in bool_fields:
            pet_dict[field] = bool(pet_dict[field]) if field in pet_dict else False
        
        conn.close()
        return jsonify(pet_dict)
        
    except Exception as e:
        print(f"Error in adoption pet detail API: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/adoption/update-status', methods=['POST'])
def api_adoption_update_status():
    """API: Update adoption status from Django system"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['pet_id', 'status', 'application_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        pet_id = data['pet_id']
        status = data['status']
        application_id = data['application_id']
        applicant_name = data.get('applicant_name', 'Unknown')
        pet_name = data.get('pet_name', 'Unknown Pet')
        
        conn = get_db_connection()
        
        if status == 'approved':
            # Mark pet as adopted in your shelter system
            conn.execute('UPDATE pets SET status = "adopted" WHERE id = ?', (pet_id,))
            
            # Log the adoption activity
            conn.execute('''
                INSERT INTO activity_logs (pet_id, user_id, action, description)
                VALUES (?, 1, 'adopted', ?)
            ''', (pet_id, f'Pet {pet_name} adopted by {applicant_name} via application {application_id}'))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Pet {pet_id} ({pet_name}) marked as ADOPTED - Application: {application_id}")
            
            return jsonify({
                'success': True,
                'message': f'Pet {pet_name} marked as adopted successfully',
                'application_id': application_id,
                'pet_id': pet_id
            })
            
        elif status == 'rejected':
            # Log the rejection (pet remains available)
            conn.execute('''
                INSERT INTO activity_logs (pet_id, user_id, action, description)
                VALUES (?, 1, 'rejection', ?)
            ''', (pet_id, f'Adoption application {application_id} for {pet_name} from {applicant_name} rejected'))
            
            conn.commit()
            conn.close()
            
            print(f"❌ Adoption REJECTED - Pet: {pet_id} ({pet_name}), Application: {application_id}")
            
            return jsonify({
                'success': True,
                'message': f'Adoption application {application_id} rejected',
                'application_id': application_id,
                'pet_id': pet_id
            })
        else:
            return jsonify({'error': 'Invalid status. Use "approved" or "rejected"'}), 400
        
    except Exception as e:
        print(f"❌ Error updating adoption status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/adoption/apply', methods=['POST'])
def api_adoption_apply():
    """API: Receive adoption application from Django system"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['pet_id', 'applicant_name', 'applicant_email']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        pet_id = data['pet_id']
        applicant_name = data['applicant_name']
        applicant_email = data['applicant_email']
        applicant_phone = data.get('applicant_phone', '')
        pet_name = data.get('pet_name', 'Unknown')
        
        conn = get_db_connection()
        
        # Log the adoption application
        conn.execute('''
            INSERT INTO activity_logs (pet_id, user_id, action, description)
            VALUES (?, 1, 'application', ?)
        ''', (pet_id, f'Adoption application received for {pet_name} from {applicant_name} ({applicant_email})'))
        
        conn.commit()
        conn.close()
        
        print(f"📝 Adoption application received - Pet: {pet_id} ({pet_name}), Applicant: {applicant_name}")
        
        return jsonify({
            'success': True,
            'message': 'Adoption application received successfully',
            'application_id': f"SHELTER-APP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        })
        
    except Exception as e:
        print(f"❌ Error processing adoption application: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/adoption/applications', methods=['GET'])
def api_adoption_applications():
    """API: Get all adoption applications (for admin)"""
    try:
        # This would return applications from your database
        # For now, return empty array as placeholder
        return jsonify([])
        
    except Exception as e:
        print(f"Error fetching adoption applications: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ===== EXISTING ROUTES =====
# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND is_active = 1', 
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """User registration (admin only)"""
    # Check if current user is admin
    if session.get('role') != 'admin':
        flash('Access denied. Administrator privileges required to create new users.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        full_name = request.form['full_name']
        role = request.form.get('role', 'staff')
        
        # Basic validation
        if not all([username, password, confirm_password, email, full_name]):
            flash('All fields are required.', 'danger')
            return render_template('register.html', current_user=get_current_user())
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', current_user=get_current_user())
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html', current_user=get_current_user())
        
        try:
            conn = get_db_connection()
            
            # Check if username already exists
            existing_user = conn.execute(
                'SELECT id FROM users WHERE username = ?', (username,)
            ).fetchone()
            
            if existing_user:
                flash('Username already exists. Please choose a different one.', 'danger')
                return render_template('register.html', current_user=get_current_user())
            
            # Check if email already exists
            existing_email = conn.execute(
                'SELECT id FROM users WHERE email = ?', (email,)
            ).fetchone()
            
            if existing_email:
                flash('Email address already exists. Please use a different email.', 'danger')
                return render_template('register.html', current_user=get_current_user())
            
            # Create new user
            conn.execute('''
                INSERT INTO users (username, password_hash, email, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                username,
                hash_password(password),
                email,
                full_name,
                role
            ))
            
            conn.commit()
            conn.close()
            
            flash(f'User {full_name} created successfully!', 'success')
            return redirect(url_for('list_users'))
            
        except sqlite3.IntegrityError as e:
            flash('Username or email already exists. Please choose different credentials.', 'danger')
            return render_template('register.html', current_user=get_current_user())
        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'danger')
            return render_template('register.html', current_user=get_current_user())
    
    current_user = get_current_user()
    return render_template('register.html', current_user=current_user)

# Protected Routes
@app.route('/')
@login_required
def index():
    """Dashboard homepage"""
    conn = get_db_connection()
    
    # Get basic statistics
    stats = {}
    stats['total_pets'] = conn.execute('SELECT COUNT(*) FROM pets').fetchone()[0]
    stats['available'] = conn.execute('SELECT COUNT(*) FROM pets WHERE status = "available"').fetchone()[0]
    stats['pending'] = conn.execute('SELECT COUNT(*) FROM pets WHERE status = "pending"').fetchone()[0]
    stats['adopted'] = conn.execute('SELECT COUNT(*) FROM pets WHERE status = "adopted"').fetchone()[0]
    
    # Get recent additions
    recent_pets = conn.execute('''
        SELECT p.*, u.full_name as created_by_name 
        FROM pets p 
        LEFT JOIN users u ON p.created_by = u.id 
        ORDER BY p.created_at DESC 
        LIMIT 5
    ''').fetchall()
    stats['recent_additions'] = [dict(pet) for pet in recent_pets]
    
    # Get recent activity
    recent_logs = conn.execute('''
        SELECT al.*, p.name as pet_name, u.full_name as user_name 
        FROM activity_logs al 
        LEFT JOIN pets p ON al.pet_id = p.id 
        LEFT JOIN users u ON al.user_id = u.id 
        ORDER BY al.timestamp DESC 
        LIMIT 5
    ''').fetchall()
    stats['recent_logs'] = [dict(log) for log in recent_logs]
    
    conn.close()
    
    current_user = get_current_user()
    return render_template('index.html', stats=stats, current_user=current_user)

@app.route('/pets')
@login_required
def list_pets():
    """List all pets with filtering"""
    species = request.args.get('species', '')
    status = request.args.get('status', '')
    breed = request.args.get('breed', '')
    
    conn = get_db_connection()
    query = 'SELECT p.*, u.full_name as created_by_name FROM pets p LEFT JOIN users u ON p.created_by = u.id WHERE 1=1'
    params = []
    
    if species:
        query += ' AND p.species = ?'
        params.append(species)
    if status:
        query += ' AND p.status = ?'
        params.append(status)
    if breed:
        query += ' AND p.breed LIKE ?'
        params.append(f'%{breed}%')
    
    query += ' ORDER BY p.created_at DESC'
    pets = conn.execute(query, params).fetchall()
    
    # Get images for each pet
    pets_with_images = []
    for pet in pets:
        pet_dict = dict(pet)
        images = conn.execute(
            'SELECT * FROM pet_images WHERE pet_id = ?', 
            (pet_dict['id'],)
        ).fetchall()
        pet_dict['images'] = [dict(img) for img in images]
        pets_with_images.append(pet_dict)
    
    conn.close()
    
    current_user = get_current_user()
    return render_template('list_pets.html', pets=pets_with_images, current_user=current_user)

@app.route('/pets/add', methods=['GET', 'POST'])
@login_required
def add_pet():
    """Add a new pet"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            
            # Insert pet data
            cursor = conn.execute('''
                INSERT INTO pets (
                    name, species, breed, age, gender, status, description,
                    vaccinated, spayed_neutered, microchipped, special_needs,
                    good_with_kids, good_with_pets, good_with_dogs, good_with_cats,
                    energy_level, image_url, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form['name'],
                request.form['species'],
                request.form.get('breed', ''),
                int(request.form['age']),
                request.form['gender'],
                request.form['status'],
                request.form['description'],
                1 if request.form.get('vaccinated') else 0,
                1 if request.form.get('spayed_neutered') else 0,
                1 if request.form.get('microchipped') else 0,
                request.form.get('special_needs', ''),
                1 if request.form.get('good_with_kids') else 0,
                1 if request.form.get('good_with_pets') else 0,
                1 if request.form.get('good_with_dogs') else 0,
                1 if request.form.get('good_with_cats') else 0,
                request.form.get('energy_level', ''),
                request.form.get('image_url', ''),
                session['user_id']
            ))
            
            pet_id = cursor.lastrowid
            
            # Add primary image if provided
            if request.form.get('image_url'):
                conn.execute('''
                    INSERT INTO pet_images (pet_id, image_url, caption, is_primary)
                    VALUES (?, ?, ?, 1)
                ''', (
                    pet_id,
                    request.form['image_url'],
                    request.form.get('image_caption', '')
                ))
            
            # Log the activity
            conn.execute('''
                INSERT INTO activity_logs (pet_id, user_id, action, description)
                VALUES (?, ?, 'added', 'Added new pet to system')
            ''', (pet_id, session['user_id']))
            
            conn.commit()
            conn.close()
            
            flash(f'Pet {request.form["name"]} added successfully!', 'success')
            return redirect(url_for('view_pet', pet_id=pet_id))
            
        except Exception as e:
            flash(f'Error adding pet: {str(e)}', 'danger')
    
    current_user = get_current_user()
    return render_template('add_pet.html', current_user=current_user)

@app.route('/pets/<int:pet_id>')
@login_required
def view_pet(pet_id):
    """View pet details"""
    conn = get_db_connection()
    
    pet = conn.execute('''
        SELECT p.*, u.full_name as created_by_name 
        FROM pets p 
        LEFT JOIN users u ON p.created_by = u.id 
        WHERE p.id = ?
    ''', (pet_id,)).fetchone()
    
    if not pet:
        flash('Pet not found!', 'danger')
        return redirect(url_for('list_pets'))
    
    images = conn.execute(
        'SELECT * FROM pet_images WHERE pet_id = ?', (pet_id,)
    ).fetchall()
    
    logs = conn.execute('''
        SELECT al.*, u.full_name as user_name 
        FROM activity_logs al 
        LEFT JOIN users u ON al.user_id = u.id 
        WHERE al.pet_id = ? 
        ORDER BY al.timestamp DESC
    ''', (pet_id,)).fetchall()
    
    conn.close()
    
    current_user = get_current_user()
    return render_template('view_pet.html', 
                         pet=dict(pet), 
                         images=[dict(img) for img in images],
                         logs=[dict(log) for log in logs],
                         current_user=current_user)

@app.route('/pets/<int:pet_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    """Edit pet information"""
    conn = get_db_connection()
    
    if request.method == 'POST':
        try:
            # Update pet data
            conn.execute('''
                UPDATE pets SET 
                    name=?, species=?, breed=?, age=?, gender=?, status=?, description=?,
                    vaccinated=?, spayed_neutered=?, microchipped=?, special_needs=?,
                    good_with_kids=?, good_with_pets=?, good_with_dogs=?, good_with_cats=?,
                    energy_level=?
                WHERE id=?
            ''', (
                request.form['name'],
                request.form['species'],
                request.form.get('breed', ''),
                int(request.form['age']),
                request.form['gender'],
                request.form['status'],
                request.form['description'],
                1 if request.form.get('vaccinated') else 0,
                1 if request.form.get('spayed_neutered') else 0,
                1 if request.form.get('microchipped') else 0,
                request.form.get('special_needs', ''),
                1 if request.form.get('good_with_kids') else 0,
                1 if request.form.get('good_with_pets') else 0,
                1 if request.form.get('good_with_dogs') else 0,
                1 if request.form.get('good_with_cats') else 0,
                request.form.get('energy_level', ''),
                pet_id
            ))
            
            # Log the activity
            conn.execute('''
                INSERT INTO activity_logs (pet_id, user_id, action, description)
                VALUES (?, ?, 'updated', 'Updated pet information')
            ''', (pet_id, session['user_id']))
            
            conn.commit()
            conn.close()
            
            flash(f'Pet {request.form["name"]} updated successfully!', 'success')
            return redirect(url_for('view_pet', pet_id=pet_id))
            
        except Exception as e:
            flash(f'Error updating pet: {str(e)}', 'danger')
    
    pet = conn.execute('SELECT * FROM pets WHERE id = ?', (pet_id,)).fetchone()
    conn.close()
    
    if not pet:
        flash('Pet not found!', 'danger')
        return redirect(url_for('list_pets'))
    
    current_user = get_current_user()
    return render_template('edit_pet.html', pet=dict(pet), current_user=current_user)

@app.route('/pets/<int:pet_id>/delete', methods=['POST'])
@login_required
def delete_pet(pet_id):
    """Delete a pet"""
    try:
        conn = get_db_connection()
        
        # Get pet name for flash message
        pet = conn.execute('SELECT name FROM pets WHERE id = ?', (pet_id,)).fetchone()
        
        if not pet:
            flash('Pet not found!', 'danger')
            return redirect(url_for('list_pets'))
        
        # Delete related records first
        conn.execute('DELETE FROM activity_logs WHERE pet_id = ?', (pet_id,))
        conn.execute('DELETE FROM pet_images WHERE pet_id = ?', (pet_id,))
        conn.execute('DELETE FROM pets WHERE id = ?', (pet_id,))
        
        conn.commit()
        conn.close()
        
        flash(f'Pet {pet["name"]} deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting pet: {str(e)}', 'danger')
    
    return redirect(url_for('list_pets'))

# Original API Endpoints (for internal use)
@app.route('/api/pets/', methods=['GET'])
def api_get_pets():
    """API: Get all pets (public for adoption system integration)"""
    conn = get_db_connection()
    pets = conn.execute('SELECT * FROM pets WHERE status = "available"').fetchall()
    conn.close()
    return jsonify([dict(pet) for pet in pets])

@app.route('/api/pets/<int:pet_id>', methods=['GET'])
def api_get_pet(pet_id):
    """API: Get specific pet (public for adoption system integration)"""
    conn = get_db_connection()
    pet = conn.execute('SELECT * FROM pets WHERE id = ?', (pet_id,)).fetchone()
    conn.close()
    
    if pet:
        return jsonify(dict(pet))
    else:
        return jsonify({'error': 'Pet not found'}), 404

@app.route('/api/update-status/', methods=['PUT'])
@login_required
def api_update_status():
    """API: Update pet status (protected)"""
    data = request.get_json()
    pet_id = data.get('pet_id')
    new_status = data.get('status')
    
    conn = get_db_connection()
    conn.execute('UPDATE pets SET status = ? WHERE id = ?', (new_status, pet_id))
    
    # Log the activity
    conn.execute('''
        INSERT INTO activity_logs (pet_id, user_id, action, description)
        VALUES (?, ?, 'status_update', ?)
    ''', (pet_id, session['user_id'], f'Status changed to {new_status}'))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/stats')
@login_required
def api_stats():
    """API: Get shelter statistics (protected)"""
    conn = get_db_connection()
    
    stats = {}
    stats['total_pets'] = conn.execute('SELECT COUNT(*) FROM pets').fetchone()[0]
    stats['available_pets'] = conn.execute('SELECT COUNT(*) FROM pets WHERE status = "available"').fetchone()[0]
    stats['dogs'] = conn.execute('SELECT COUNT(*) FROM pets WHERE species = "dog"').fetchone()[0]
    stats['cats'] = conn.execute('SELECT COUNT(*) FROM pets WHERE species = "cat"').fetchone()[0]
    
    conn.close()
    return jsonify(stats)

# Chatbot Routes
@app.route('/chatbot')
@login_required
def chatbot_page():
    """Chatbot interface"""
    current_user = get_current_user()
    return render_template('chatbot.html', current_user=current_user)

@app.route('/chatbot/api/chat', methods=['POST'])
@login_required
def chatbot_api():
    """Chatbot API endpoint"""
    data = request.get_json()
    user_message = data.get('message', '')
    
    response = chatbot.process_message(user_message)
    return jsonify({'response': response})

# User Management (Admin only)
@app.route('/users')
@login_required
def list_users():
    """List all users (admin only)"""
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    
    current_user = get_current_user()
    return render_template('users.html', users=[dict(user) for user in users], current_user=current_user)

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Prevent admin from deleting themselves
    if user_id == session['user_id']:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('list_users'))
    
    try:
        conn = get_db_connection()
        
        # Get user info for flash message
        user = conn.execute('SELECT username, full_name FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('list_users'))
        
        # Check if this is the last admin
        admin_count = conn.execute('SELECT COUNT(*) FROM users WHERE role = "admin"').fetchone()[0]
        if admin_count <= 1:
            flash('Cannot delete the last administrator account.', 'danger')
            return redirect(url_for('list_users'))
        
        # Delete the user
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        flash(f'User {user["full_name"]} ({user["username"]}) deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('list_users'))

@app.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Toggle user active status (admin only)"""
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Prevent admin from deactivating themselves
    if user_id == session['user_id']:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('list_users'))
    
    try:
        conn = get_db_connection()
        
        # Get current status
        user = conn.execute('SELECT is_active FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('list_users'))
        
        new_status = not user['is_active']
        
        # Update status
        conn.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
        
        conn.commit()
        conn.close()
        
        status_text = 'activated' if new_status else 'deactivated'
        flash(f'User account {status_text} successfully!', 'success')
        
    except Exception as e:
        flash(f'Error updating user status: {str(e)}', 'danger')
    
    return redirect(url_for('list_users'))

@app.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id):
    """Edit user information (admin only)"""
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    try:
        full_name = request.form['full_name']
        username = request.form['username']
        email = request.form.get('email', '')
        role = request.form['role']
        is_active = request.form['is_active'] == '1'
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        conn = get_db_connection()
        
        # Check if username already exists (excluding current user)
        existing_user = conn.execute(
            'SELECT id FROM users WHERE username = ? AND id != ?', 
            (username, user_id)
        ).fetchone()
        
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('list_users'))
        
        # Check if email already exists (excluding current user)
        if email:
            existing_email = conn.execute(
                'SELECT id FROM users WHERE email = ? AND id != ?', 
                (email, user_id)
            ).fetchone()
            
            if existing_email:
                flash('Email address already exists. Please use a different email.', 'danger')
                return redirect(url_for('list_users'))
        
        # Update user data
        if password:
            # Validate password if provided
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('list_users'))
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return redirect(url_for('list_users'))
            
            # Update with new password
            conn.execute('''
                UPDATE users SET 
                    full_name=?, username=?, email=?, role=?, is_active=?, password_hash=?
                WHERE id=?
            ''', (full_name, username, email, role, is_active, hash_password(password), user_id))
        else:
            # Update without changing password
            conn.execute('''
                UPDATE users SET 
                    full_name=?, username=?, email=?, role=?, is_active=?
                WHERE id=?
            ''', (full_name, username, email, role, is_active, user_id))
        
        conn.commit()
        conn.close()
        
        flash(f'User {full_name} updated successfully!', 'success')
        
    except Exception as e:
        flash(f'Error updating user: {str(e)}', 'danger')
    
    return redirect(url_for('list_users'))

if __name__ == '__main__':
    init_db()
    app.run(port=5001, debug=True)