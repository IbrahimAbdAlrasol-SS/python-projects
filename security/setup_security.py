"""
Complete Security Setup
إعداد نظام الأمان الكامل
"""
from flask import Flask
from .jwt_manager import jwt_manager
from .rate_limiter import setup_rate_limiting
from .security_headers import setup_security_headers
from .cors_config import setup_cors
from .account_lockout import AccountLockoutManager


def setup_complete_security(app: Flask):
    """Setup all security components"""
    print("🔐 Setting up security layer...")

    # 1. Initialize JWT Manager
    jwt_manager.init_app(app)
    print("✅ JWT authentication configured")

    # 2. Setup rate limiting
    limiter = setup_rate_limiting(app)
    app.limiter = limiter
    print("✅ Rate limiting configured")

    # 3. Setup security headers
    setup_security_headers(app)
    print("✅ Security headers configured")

    # 4. Setup CORS
    setup_cors(app)
    print("✅ CORS configured")

    # 5. Initialize account lockout manager
    try:
        lockout_manager = AccountLockoutManager()
        app.lockout_manager = lockout_manager
        print("✅ Account lockout system configured")
    except Exception as e:
        print(f"⚠️ Account lockout system failed: {e}")
        app.lockout_manager = None

    # 6. Register security error handlers
    register_security_error_handlers(app)
    print("✅ Security error handlers registered")

    print("🔐 Security layer setup completed!")

    return True


def register_security_error_handlers(app: Flask):
    """Register error handlers for security events"""
    @app.errorhandler(401)
    def unauthorized(e):
        return {
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'code': 'UNAUTHORIZED'
        }, 401

    @app.errorhandler(403)
    def forbidden(e):
        return {
            'error': 'Forbidden',
            'message': 'Insufficient permissions',
            'code': 'FORBIDDEN'
        }, 403

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return {
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded, please try again later',
            'code': 'RATE_LIMIT_EXCEEDED'
        }, 429
