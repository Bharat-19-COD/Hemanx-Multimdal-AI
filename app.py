import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_pymongo import PyMongo
from flask_wtf import CSRFProtect
from config import Config
from bson.objectid import ObjectId

mongo = PyMongo()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # Initialize extensions
    mongo.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
        except Exception as e:
            print("Error loading user:", e)
        return None

    # Register blueprints
    from routes.auth import auth_bp
    from routes.emotion import emotion_bp
    from routes.dashboard import dashboard_bp
    from routes.admin import admin_bp
    from routes.wellness import wellness_bp
    from routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(emotion_bp, url_prefix='/emotion')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(wellness_bp, url_prefix='/wellness')
    app.register_blueprint(settings_bp, url_prefix='/settings')

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error_code=404), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error_code=500), 500

    return app

# Global get_db function
def get_db():
    return mongo.db

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)