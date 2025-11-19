from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from bson.objectid import ObjectId
import re

auth_bp = Blueprint('auth', __name__)

def get_db():
    from app import mongo
    return mongo.db

def safe_check_password_hash(stored_hash, password):
    """Safely check password hash with support for both werkzeug and bcrypt"""
    if not stored_hash or not password:
        return False
    
    try:
        # Handle bytes conversion - if it's bytes, it's from bcrypt
        if isinstance(stored_hash, bytes):
            print("🔄 Hash is in bytes format - attempting bcrypt check")
            import bcrypt
            try:
                # Try bcrypt check
                result = bcrypt.checkpw(password.encode('utf-8'), stored_hash)
                print(f"✅ Bcrypt password check: {result}")
                return result
            except Exception as e:
                print(f"❌ Bcrypt check failed: {e}")
                return False
        
        # Handle string hash (werkzeug)
        if isinstance(stored_hash, str):
            # Try werkzeug check
            result = check_password_hash(stored_hash, password)
            print(f"✅ Werkzeug password check: {result}")
            return result
        
        print(f"❌ Unknown hash type: {type(stored_hash)}")
        return False
        
    except Exception as e:
        print(f"❌ Password check error: {e}")
        return False

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('index.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            db = get_db()
            email = request.form.get('email')
            password = request.form.get('password')
            
            print(f"=== LOGIN ATTEMPT ===")
            print(f"📧 Email: {email}")
            print(f"🔒 Password provided: {'*' * len(password) if password else 'None'}")
            
            if not email or not password:
                flash('Please enter both email and password', 'error')
                return redirect(url_for('auth.login'))
            
            user_data = db.users.find_one({'email': email})
            
            if user_data:
                print(f"✅ User found: {user_data['email']}")
                print(f"📝 Username: {user_data.get('username', 'N/A')}")
                print(f"🔐 Password field type: {type(user_data['password'])}")
                print(f"🔐 Password value: {user_data['password']}")
                
                # Check password using our safe function
                if safe_check_password_hash(user_data['password'], password):
                    print("🎉 Password check PASSED - logging in user")
                    from models.user import User
                    user_obj = User(user_data)
                    login_user(user_obj)
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard.dashboard'))
                else:
                    print("❌ Password check FAILED")
                    flash('Invalid email or password', 'error')
            else:
                print("❌ User not found")
                flash('Invalid email or password', 'error')
            
            return redirect(url_for('auth.login'))
                
        except Exception as e:
            print(f"💥 LOGIN ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            flash('Login failed. Please try again.', 'error')
            return redirect(url_for('auth.login'))
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            db = get_db()
            
            # Get form data - handle both 'name' and 'username'
            email = request.form.get('email')
            password = request.form.get('password')
            name = request.form.get('name')  # From your form
            username = request.form.get('username') or name  # Use name as username if username not provided
            
            print(f"=== REGISTRATION ATTEMPT ===")
            print(f"📧 Email: {email}")
            print(f"👤 Name: {name}")
            print(f"👤 Username: {username}")
            print(f"🔒 Password: {'*' * len(password) if password else 'None'}")
            
            # Validation
            if not all([email, password, name]):
                flash('All fields are required', 'error')
                return redirect(url_for('auth.register'))
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return redirect(url_for('auth.register'))
            
            if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                flash('Invalid email format', 'error')
                return redirect(url_for('auth.register'))
            
            # Check if user already exists
            if db.users.find_one({'email': email}):
                flash('Email already registered', 'error')
                return redirect(url_for('auth.register'))
            
            # Create new user with proper password hashing
            password_hash = generate_password_hash(password)
            print(f"🔐 Generated hash: {password_hash}")
            print(f"🔐 Hash type: {type(password_hash)}")
            
            user_data = {
                'username': username,
                'email': email,
                'name': name,
                'password': password_hash,
                'created_at': ObjectId().generation_time,
                'wellness_preferences': {},
                'role': 'user'
            }
            
            result = db.users.insert_one(user_data)
            user_data['_id'] = result.inserted_id
            
            print(f"✅ User created successfully: {email}")
            
            # Log the user in
            from models.user import User
            user_obj = User(user_data)
            login_user(user_obj)
            
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard.dashboard'))
            
        except Exception as e:
            print(f"💥 REGISTRATION ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Registration error: {str(e)}', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.index'))

# Emergency route to check database
@auth_bp.route('/debug-users')
def debug_users():
    """Debug route to check all users in database"""
    try:
        db = get_db()
        users = db.users.find({})
        
        result = "<h1>Database Users</h1>"
        for user in users:
            result += f"""
            <div style="border: 1px solid #ccc; margin: 10px; padding: 10px;">
                <h3>User: {user['email']}</h3>
                <p>Username: {user.get('username', 'N/A')}</p>
                <p>Name: {user.get('name', 'N/A')}</p>
                <p>Password Type: {type(user['password'])}</p>
                <p>Password Value: {user['password']}</p>
                <p>Starts with $2b$: {str(user['password']).startswith('$2b$') if user['password'] else 'No'}</p>
            </div>
            """
        return result
    except Exception as e:
        return f"Error: {str(e)}"