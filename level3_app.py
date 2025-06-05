"""
🔌 Level 3: Core API Endpoints & Routing
نظام الـ APIs الأساسية - المرحلة الثالثة
"""

from flask import Flask
from datetime import datetime

def create_level3_app():
    """Create Level 3 Application with Core APIs"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Import configurations
    from config.database import DatabaseConfig
    from security.setup_security import setup_complete_security
    
    # Configure app
    app.config.from_object(DatabaseConfig)
    DatabaseConfig.init_app(app)
    
    # Setup security layer
    setup_complete_security(app)
    
    # Register API blueprints
    register_api_blueprints(app)
    
    # Setup error handlers
    setup_api_error_handlers(app)
    
    # Setup middleware
    setup_api_middleware(app)
    
    return app

def register_api_blueprints(app):
    """Register all API blueprints"""
    
    # Import blueprints
    from apis.auth_api import auth_bp
    from apis.student_api import student_bp
    from apis.admin_api import admin_bp
    from apis.attendance_api import attendance_bp
    from apis.reports_api import reports_bp
    from apis.health_api import health_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(health_bp)
    
    print("✅ All API blueprints registered")

def setup_api_error_handlers(app):
    """Setup comprehensive error handlers"""
    from flask import jsonify
    from werkzeug.exceptions import HTTPException
    
    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        """Handle HTTP errors with standardized format"""
        return jsonify({
            'success': False,
            'error': {
                'code': f'HTTP_{e.code}',
                'message': e.description or 'An error occurred',
                'timestamp': datetime.utcnow().isoformat()
            }
        }), e.code

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        """Handle unexpected errors"""
        app.logger.error(f'Unhandled exception: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'حدث خطأ غير متوقع، يرجى المحاولة لاحقاً',
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 500

    @app.errorhandler(ValueError)
    def handle_validation_error(e):
        """Handle input validation errors"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'بيانات غير صحيحة',
                'details': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 400

def setup_api_middleware(app):
    """Setup API middleware"""
    from flask import request, g
    import time
    
    @app.before_request
    def before_request():
        """Execute before each request"""
        g.start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID', 'unknown')
    
    @app.after_request
    def after_request(response):
        """Execute after each request"""
        total_time = time.time() - g.start_time
        
        # Log slow requests
        if total_time > 2.0:
            app.logger.warning(
                f'Slow request: {request.method} {request.path} '
                f'took {total_time:.2f}s - Request ID: {g.request_id}'
            )
        
        # Add performance headers
        response.headers['X-Response-Time'] = f'{total_time:.3f}s'
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-API-Version'] = '1.0'
        
        return response

if __name__ == '__main__':
    print("🔌 Starting Level 3: Core API Endpoints")
    print("=" * 50)
    
    app = create_level3_app()
    
    print("🚀 Level 3 application ready!")
    print("📍 API Endpoints: 20 total")
    print("🔐 Security: Enabled")
    print("📊 Monitoring: Active")
    
    app.run(debug=True, host='0.0.0.0', port=5000)