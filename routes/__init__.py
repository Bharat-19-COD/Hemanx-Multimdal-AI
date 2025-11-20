"""
Routes package for HEMANX Emotion Analysis Platform
"""
from routes.auth import auth_bp
from routes.emotion import emotion_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp
from routes.wellness import wellness_bp
from routes.settings import settings_bp

__all__ = [
    'auth_bp',
    'emotion_bp',
    'dashboard_bp',
    'admin_bp',
    'wellness_bp',
    'settings_bp'
]
