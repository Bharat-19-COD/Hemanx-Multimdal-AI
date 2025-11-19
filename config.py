import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/emotion_wellness'
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Model configurations
    FACE_MODEL = "deepface"
    TEXT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    VOICE_MODEL = "superb/wav2vec2-base-superb-er"
    
    # Google Generative AI configuration
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') or 'your-google-ai-key'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)