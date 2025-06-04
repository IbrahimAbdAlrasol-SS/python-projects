"""
CORS Configuration
إعدادات CORS
"""
from flask import Flask
from flask_cors import CORS


def setup_cors(app: Flask):
    """Setup CORS for the application"""
    # CORS configuration
    cors_config = {
        'origins': [
            'https://attendance.university.edu',
            'https://admin.attendance.university.edu',
            'http://localhost:3000',  # للتطوير
            'http://localhost:8080'   # للتطوير
        ],
        'methods': [
            'GET',
            'POST', 
            'PUT',
            'DELETE',
            'OPTIONS'
        ],
        'allow_headers': [
            'Content-Type',
            'Authorization', 
            'X-Requested-With',
            'X-Device-Fingerprint'
        ],
        'expose_headers': [
            'X-Total-Count',
            'X-Page-Count',
            'X-Current-Page',
            'X-Response-Time'
        ],
        'supports_credentials': True,
        'max_age': 3600  # 1 hour
    }

    # Initialize CORS
    CORS(app, resources={
        r"/api/*": cors_config
    })

    print("✅ CORS configured for allowed origins")
