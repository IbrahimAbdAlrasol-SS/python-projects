"""
Rate Limiting System
نظام تحديد معدل الطلبات
"""
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

def setup_rate_limiting(app: Flask):
    """Setup rate limiting for the application"""
    # Configure storage backend
    try:
        storage_uri = "redis://localhost:6379/2"  # Use db=2 for rate limiting
        
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["1000 per hour", "100 per minute"],
            storage_uri=storage_uri,
            storage_options={"socket_connect_timeout": 30},
            strategy="fixed-window-elastic-expiry"
        )
        
        # Apply specific limits to sensitive endpoints
        # These will be applied in the route definitions
        app.config['RATE_LIMITS'] = {
            'login': '5 per minute',
            'register': '10 per hour',
            'password_reset': '3 per hour',
            'api_heavy': '10 per minute',
            'export': '5 per hour',
            'batch_upload': '10 per minute'
        }
        
        print("✅ Rate limiting configured with Redis backend")
        return limiter
        
    except Exception as e:
        print(f"⚠️ Rate limiting setup failed, using memory backend: {e}")
        
        # Fallback to memory backend
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["1000 per hour", "100 per minute"],
            storage_uri=storage_uri,
            storage_options={"socket_connect_timeout": 30},
            strategy="fixed-window"  # تغيير من "fixed-window-elastic-expiry"
        )
        
        return limiter
