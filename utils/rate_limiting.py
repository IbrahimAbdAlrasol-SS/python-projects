from functools import wraps
from flask import current_app, jsonify, request

def rate_limit(limit_string):
    """Custom rate limiting decorator that works with application context"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if hasattr(current_app, 'limiter'):
                try:
                    # Apply rate limiting based on IP
                    key = f"{request.endpoint}:{request.remote_addr}"
                    current_app.limiter.check(limit_string, key)
                except Exception as e:
                    return jsonify({
                        'error': 'RATE_LIMIT_EXCEEDED',
                        'message': 'تم تجاوز الحد المسموح من المحاولات، يرجى المحاولة لاحقاً',
                        'retry_after': '60 seconds'
                    }), 429
            return f(*args, **kwargs)
        return decorated_function
    return decorator