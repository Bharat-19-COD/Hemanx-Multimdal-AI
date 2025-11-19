#!/usr/bin/env python3
"""
Production runner for HEMANX Emotion Analysis Platform
"""
import os
from app import app

if __name__ == '__main__':
    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"""
    🚀 HEMANX Emotion Analysis Platform
    📍 Starting server on {host}:{port}
    🔧 Debug mode: {debug}
    🗄️  Database: {os.environ.get('MONGO_URI', 'Local MongoDB')}
    
    Press Ctrl+C to stop the server
    """)
    
    app.run(host=host, port=port, debug=debug)