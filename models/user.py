from flask_login import UserMixin
from datetime import datetime
import bcrypt
import re
from bson.objectid import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.name = user_data['name']
        self.role = user_data['role']
        self.created_at = user_data.get('created_at', datetime.utcnow())
        self.badges = user_data.get('badges', [])
        self.level = user_data.get('level', 1)
        self.wellness_score = user_data.get('wellness_score', 0)
        
        # Remove is_active from initialization to avoid conflicts

    # Flask-Login will handle these properties automatically
    # Don't define is_active, is_authenticated, is_anonymous as properties

    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        return True, "Password is valid"

    @staticmethod
    def create_user(db, email, password, name, role='student'):
        users = db.users
        
        if not User.validate_email(email):
            return None, "Invalid email format"
        
        is_valid, msg = User.validate_password(password)
        if not is_valid:
            return None, msg
        
        if users.find_one({'email': email.lower().strip()}):
            return None, "Email already exists"
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_data = {
            'email': email.lower().strip(),
            'password': hashed_password,
            'name': name.strip(),
            'role': role,
            'created_at': datetime.utcnow(),
            'badges': [],
            'level': 1,
            'wellness_score': 0
        }
        
        try:
            result = users.insert_one(user_data)
            user_data['_id'] = result.inserted_id
            return User(user_data), "User created successfully"
        except Exception as e:
            return None, f"Database error: {str(e)}"

    @staticmethod
    def authenticate(db, email, password):
        users = db.users
        
        try:
            user_data = users.find_one({'email': email.lower().strip()})
            
            if not user_data:
                return None
            
            if bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
                return User(user_data)
            return None
                
        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'level': self.level,
            'wellness_score': self.wellness_score,
            'badges': self.badges
        }