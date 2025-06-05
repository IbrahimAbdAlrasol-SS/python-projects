"""
🚀 Smart Attendance System - Main Application
نظام الحضور الذكي - التطبيق الرئيسي
المستوى الثالث: API Layer - Implementation Complete
"""

import os
import logging
import logging.handlers
from datetime import datetime, timedelta
from flask import Flask, request, g, jsonify
from flask_cors import CORS
#from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import configurations
from config.database import db, redis_client
from config.settings import Config

# Import security components
from security import (
    jwt_manager, PasswordManager, InputValidator,
    init_security, jwt_required, get_current_user
)

# Import all API blueprints
from apis.auth_api import auth_bp
from apis.student_api import student_bp, rooms_bp  # إضافة rooms_bp هنا
from apis.student_api import student_bp  # ✅ استخدام الملف الموجود
from apis.admin_api import admin_bp      # ✅ استخدام الملف الموجود
from apis.attendance_api import attendance_bp
from apis.reports_api import reports_bp
from apis.health_api import health_bp

# Import core operations (alternative implementation)
#from core_operations_complete import core_ops_bp

# Import utilities
from utils.response_helpers import success_response, error_response
from utils.validation_helpers import InputValidator

# Import models for initialization
from models import *
from data.sample_data import generate_complete_sample_data
# Import configurations
from config.database import db, redis_client, init_db  # إضافة init_db
from config.settings import Config
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 1. Initialize database
    init_db(app)
    
    # 2. Setup security (includes rate limiting)
    init_security(app)
    
    # Remove these lines (60-68):
    # limiter = Limiter(
    #     app,
    #     key_func=get_remote_address,
    #     default_limits=["1000 per hour", "100 per minute"],
    #     storage_uri="redis://localhost:6379"
    # )
    # app.limiter = limiter
    
    # ... existing code ...
    # 5. Configure logging
    setup_logging(app)
    
    # 6. Request/Response middleware
    setup_middleware(app)
    
    # 7. Register all API blueprints
    register_blueprints(app)
    
    # 8. Register error handlers
    register_error_handlers(app)
    
    # 9. Setup application context
    setup_app_context(app)
    
    return app

def setup_logging(app):
    """Configure comprehensive logging"""
    
    if not app.debug:
        # Create logs directory if not exists
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Main application log
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/smart_attendance.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Security audit log
        security_handler = logging.handlers.RotatingFileHandler(
            'logs/security_audit.log',
            maxBytes=10240000,
            backupCount=10
        )
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - User: %(user_id)s - Action: %(action)s - IP: %(ip)s - %(message)s'
        ))
        
        security_logger = logging.getLogger('security')
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.INFO)
        
        # API access log
        api_handler = logging.handlers.RotatingFileHandler(
            'logs/api_access.log',
            maxBytes=10240000,
            backupCount=10
        )
        api_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(method)s %(url)s - %(status_code)s - %(response_time)sms - User: %(user_id)s'
        ))
        
        api_logger = logging.getLogger('api')
        api_logger.addHandler(api_handler)
        api_logger.setLevel(logging.INFO)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Smart Attendance System startup')

def setup_middleware(app):
    """Setup request/response middleware"""
    
    @app.before_request
    def before_request():
        """Execute before each request"""
        g.start_time = datetime.utcnow()
        g.request_id = f"{datetime.utcnow().timestamp()}-{request.remote_addr}"
        
        # Log incoming request
        if not request.path.startswith('/static'):
            app.logger.info(f'Request: {request.method} {request.path} from {request.remote_addr}')
    
    @app.after_request
    def after_request(response):
        """Execute after each request"""
        
        # Calculate response time
        if hasattr(g, 'start_time'):
            response_time = (datetime.utcnow() - g.start_time).total_seconds() * 1000
            response.headers['X-Response-Time'] = f'{response_time:.2f}ms'
            
            # Log slow requests
            if response_time > 2000:  # Slower than 2 seconds
                app.logger.warning(f'Slow request: {request.method} {request.path} took {response_time:.2f}ms')
            
            # Log API access
            if request.path.startswith('/api/'):
                user_id = getattr(g, 'current_user', {}).get('id', 'anonymous')
                api_logger = logging.getLogger('api')
                api_logger.info('', extra={
                    'method': request.method,
                    'url': request.path,
                    'status_code': response.status_code,
                    'response_time': f'{response_time:.2f}',
                    'user_id': user_id
                })
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    @app.teardown_appcontext
    def close_db(error):
        """Clean up database connections"""
        if error:
            db.session.rollback()
        db.session.remove()

def register_blueprints(app):
    """Register all API blueprints with comprehensive endpoint mapping"""
    
    # API Blueprint mapping - 20 endpoints total
    blueprints = [
        # Authentication APIs (3 endpoints)
        (auth_bp, 'Authentication APIs'),
        
        # Pre-Sync APIs (4 endpoints) 
        (student_bp, 'Student/Pre-Sync APIs'),
        (rooms_bp, 'Rooms API'),
        
        # Admin Management APIs (6 endpoints)
        (admin_bp, 'Admin Management APIs'),
        
        # Core Operations APIs (4 endpoints)
        (attendance_bp, 'Attendance APIs'),
        #(core_ops_bp, 'Core Operations APIs'),  # Alternative implementation
        
        # Reports APIs (3 endpoints)
        (reports_bp, 'Reports APIs'),
        
        # Health Check API (1 endpoint)
        (health_bp, 'Health Check API')
    ]
    
    registered_count = 0
    for blueprint, description in blueprints:
        try:
            app.register_blueprint(blueprint)
            registered_count += 1
            app.logger.info(f'Registered: {description}')
        except Exception as e:
            app.logger.error(f'Failed to register {description}: {str(e)}')
    
    app.logger.info(f'Total blueprints registered: {registered_count}')
    
    # Register root endpoints
    @app.route('/')
    def index():
        """API root endpoint"""
        return jsonify(success_response({
            'service': 'Smart Attendance System API',
            'version': '1.0.0',
            'status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'endpoints': {
                'authentication': '/api/auth',
                'student_apis': '/api/student',
                'admin_apis': '/api/admin', 
                'attendance_apis': '/api/attendance',
                'reports_apis': '/api/reports',
                'health_check': '/api/health',
                'documentation': '/docs',
                'api_info': '/api/info'
            },
            'features': [
                'JWT Authentication',
                'Role-based Access Control',
                'Triple Verification System',
                'Offline Data Synchronization',
                'Real-time Conflict Resolution',
                'Comprehensive Reporting',
                'GPS Location Validation',
                'QR Code Generation',
                'Face Recognition Integration'
            ]
        }))
    
    @app.route('/api/info')
    def api_info():
        """API information endpoint"""
        return jsonify(success_response({
            'api_version': '1.0.0',
            'total_endpoints': 20,
            'endpoint_categories': {
                'authentication': 3,
                'pre_sync': 4,
                'admin_management': 6,
                'core_operations': 4,
                'reports': 3
            },
            'supported_features': {
                'authentication': ['JWT tokens', 'Role-based permissions', 'Rate limiting'],
                'data_sync': ['Full sync', 'Incremental sync', 'Conflict resolution'],
                'attendance': ['GPS verification', 'QR codes', 'Face recognition'],
                'admin': ['Bulk operations', 'User management', 'System monitoring'],
                'reports': ['Attendance analytics', 'Export formats', 'Real-time data']
            },
            'server_info': {
                'timezone': 'UTC',
                'max_request_size': '10MB',
                'rate_limits': '1000/hour, 100/minute',
                'supported_formats': ['JSON'],
                'cors_enabled': True
            }
        }))

def register_error_handlers(app):
    """Register comprehensive error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify(error_response(
            'BAD_REQUEST',
            'طلب غير صحيح - تحقق من البيانات المرسلة'
        )), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify(error_response(
            'UNAUTHORIZED',
            'غير مصرح - يرجى تسجيل الدخول أولاً'
        )), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify(error_response(
            'FORBIDDEN',
            'ممنوع - صلاحيات غير كافية'
        )), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify(error_response(
            'NOT_FOUND',
            'المورد المطلوب غير موجود'
        )), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify(error_response(
            'METHOD_NOT_ALLOWED',
            'الطريقة غير مسموحة لهذا المسار'
        )), 405
    
    @app.errorhandler(413)
    def payload_too_large(error):
        return jsonify(error_response(
            'PAYLOAD_TOO_LARGE',
            'حجم البيانات كبير جداً'
        )), 413
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify(error_response(
            'RATE_LIMIT_EXCEEDED',
            'تم تجاوز الحد المسموح من الطلبات'
        )), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {str(error)}', exc_info=True)
        return jsonify(error_response(
            'INTERNAL_SERVER_ERROR',
            'خطأ في الخادم - يرجى المحاولة لاحقاً'
        )), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        return jsonify(error_response(
            'SERVICE_UNAVAILABLE',
            'الخدمة غير متاحة مؤقتاً'
        )), 503

def setup_app_context(app):
    """Setup application context and initialize data"""
    
    @app.cli.command()
    
    @app.cli.command()
    def create_sample_data():
        """Generate sample data for testing"""
        try:
            print("Generating sample data...")
            result = generate_complete_sample_data()
            if result:
                print("✅ Sample data generated successfully!")
            else:
                print("❌ Sample data generation failed!")
        except Exception as e:
            print(f"❌ Sample data generation error: {str(e)}")
    
    @app.cli.command()
    def reset_db():
        """Reset database completely"""
        try:
            print("Resetting database...")
            db.drop_all()
            db.create_all()
            
            # Create performance indexes
            from database.indexes import create_performance_indexes
            create_performance_indexes()
            
            print("✅ Database reset successfully!")
        except Exception as e:
            print(f"❌ Database reset failed: {str(e)}")
    
    # Application context setup
    with app.app_context():
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            app.logger.info('Database connection established')
            
            # Test Redis connection
            redis_client.ping()
            app.logger.info('Redis connection established')
            
        except Exception as e:
            app.logger.error(f'Application context setup error: {str(e)}')

# CLI commands for development
def setup_cli_commands(app):
    """Setup CLI commands for management"""
    
    @app.cli.command()
    def test_apis():
        """Test all API endpoints"""
        print("Testing API endpoints...")
        
        with app.test_client() as client:
            # Test root endpoint
            response = client.get('/')
            print(f"Root endpoint: {response.status_code}")
            
            # Test health check
            response = client.get('/api/health')
            print(f"Health check: {response.status_code}")
            
            # Test API info
            response = client.get('/api/info')
            print(f"API info: {response.status_code}")
            
        print("✅ Basic API tests completed!")
    
    @app.cli.command()
    def create_admin():
        """Create admin user"""
        try:
            from models import User, UserRole
            
            admin = User(
                username='admin',
                email='admin@university.edu',
                full_name='System Administrator',
                role=UserRole.ADMIN,
                is_active=True
            )
            admin.set_password('AdminPass123!')
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created successfully!")
            print(f"Username: admin")
            print(f"Password: AdminPass123!")
            
        except Exception as e:
            print(f"❌ Admin creation failed: {str(e)}")

# Create the application instance
app = create_app()

# Setup CLI commands
setup_cli_commands(app)

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
else:
    # Production configuration
    # This will be used by WSGI servers like Gunicorn
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)