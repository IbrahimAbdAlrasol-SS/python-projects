"""
Security Headers Configuration
إعدادات رؤوس الأمان
"""
from flask import Flask, Response
from flask_talisman import Talisman


def setup_security_headers(app: Flask):
    """Setup security headers for the application"""
    # Content Security Policy
    csp = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            "'unsafe-inline'",  # للتطوير فقط
            'https://cdn.jsdelivr.net',  # للمكتبات
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",  # للتطوير فقط
            'https://fonts.googleapis.com',
        ],
        'font-src': [
            "'self'",
            'https://fonts.gstatic.com',
        ],
        'img-src': [
            "'self'",
            'data:',
            'https:',
        ],
        'connect-src': [
            "'self'",
            'wss:',  # للـ WebSocket
        ],
    }

    # Initialize Talisman for security headers
    Talisman(
        app,
        force_https=True,  # Force HTTPS in production
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,  # 1 year
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],
        feature_policy={
            'geolocation': "'self'",  # للـ GPS
            'camera': "'self'",       # للـ face recognition
        }
    )

    # Additional security headers
    @app.after_request
    def add_security_headers(response: Response):
        """Add additional security headers"""
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions policy (modern replacement for feature policy)
        response.headers['Permissions-Policy'] = (
            'geolocation=(self), '
            'camera=(self), '
            'microphone=(), '
            'payment=(), '
            'usb=()'
        )
        
        # Remove server header
        response.headers.pop('Server', None)
        
        # Add custom security header
        response.headers['X-Attendance-System'] = 'Smart-Attendance-v1.0'
        
        return response

    print("✅ Security headers configured")
