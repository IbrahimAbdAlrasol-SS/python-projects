#!/usr/bin/env python3
"""
🔌 Level 3: Core API Endpoints Implementation (FIXED)
Smart Attendance System - Main Application Entry Point
Fixed Application Context Issues
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def create_level3_app():
    """Create and configure Flask application for Level 3"""
    
    print("🔌 Starting Level 3: Core API Endpoints")
    print("=" * 50)
    
    # Create Flask app using existing create_app from app.py
    try:
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
    except ImportError:
        # Fallback: Create minimal Flask app
        from flask import Flask
        from config.database import DatabaseConfig
        
        app = Flask(__name__)
        app.config.from_object(DatabaseConfig)
        
        # Initialize database
        from config.database import db
        db.init_app(app)
        print("✅ Fallback Flask app created")
    
    # Setup security within app context
    with app.app_context():
        try:
            # Check if security is already setup
            if not hasattr(app, 'jwt_manager'):
                from security import setup_security_layer
                setup_security_layer(app)
            print("🔐 Security layer verified/setup completed!")
        except Exception as e:
            print(f"⚠️ Security setup warning: {e}")
    
    # Import and setup models within app context
    with app.app_context():
        try:
            from models import print_model_summary
            print_model_summary()
        except Exception as e:
            print(f"⚠️ Models import warning: {e}")
    
    # Register API blueprints AFTER app context is established
    register_api_blueprints(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Initialize/verify database within app context
    with app.app_context():
        setup_database(app)
    
    print("\n🚀 Level 3 Application Ready!")
    print("📋 Available APIs:")
    print("   • Authentication: 3 endpoints")
    print("   • Pre-Sync: 4 endpoints") 
    print("   • Core Operations: 4 endpoints")
    print("   • Admin Management: 6 endpoints")
    print("   • Reports: 3 endpoints")
    print("   • Health Check: 1 endpoint")
    print("=" * 50)
    
    return app

def register_api_blueprints(app):
    """Register all API blueprints with proper error handling"""
    
    try:
        # Import blueprints within try-catch to handle missing modules
        blueprints_to_register = []
        
        # Core authentication APIs
        try:
            from apis.auth_api import auth_bp
            blueprints_to_register.append(('auth_bp', auth_bp, 'Authentication APIs'))
        except ImportError as e:
            print(f"⚠️ Warning: Could not import auth_api: {e}")
        
        # Student and room APIs  
        try:
            from apis.student_api import student_bp
            blueprints_to_register.append(('student_bp', student_bp, 'Student APIs'))
        except ImportError:
            print("⚠️ Warning: Could not import student_api")
            
        try:
            from apis.student_api import rooms_bp
            blueprints_to_register.append(('rooms_bp', rooms_bp, 'Rooms API'))
        except ImportError:
            print("⚠️ Warning: Could not import rooms_bp from student_api")
        
        # Admin APIs
        try:
            from apis.admin_api import admin_bp
            blueprints_to_register.append(('admin_bp', admin_bp, 'Admin APIs'))
        except ImportError:
            print("⚠️ Warning: Could not import admin_api")
        
        # Attendance APIs
        try:
            from apis.attendance_api import attendance_bp
            blueprints_to_register.append(('attendance_bp', attendance_bp, 'Attendance APIs'))
        except ImportError:
            print("⚠️ Warning: Could not import attendance_api")
        
        # Reports APIs
        try:
            from apis.reports_api import reports_bp
            blueprints_to_register.append(('reports_bp', reports_bp, 'Reports APIs'))
        except ImportError:
            print("⚠️ Warning: Could not import reports_api")
        
        # Health check API
        try:
            from apis.health_api import health_bp
            blueprints_to_register.append(('health_bp', health_bp, 'Health API'))
        except ImportError:
            print("⚠️ Warning: Could not import health_api")
        
        # Register all successfully imported blueprints
        registered_count = 0
        for name, blueprint, description in blueprints_to_register:
            try:
                app.register_blueprint(blueprint)
                print(f"✅ Registered: {description}")
                registered_count += 1
            except Exception as e:
                print(f"❌ Failed to register {description}: {e}")
        
        print(f"✅ Total blueprints registered: {registered_count}")
        
        # Register basic health endpoint if no health_bp
        if not any(name == 'health_bp' for name, _, _ in blueprints_to_register):
            register_basic_health_endpoint(app)
            
    except Exception as e:
        print(f"❌ Error in blueprint registration: {str(e)}")
        # Register minimal endpoints for testing
        register_minimal_endpoints(app)

def register_basic_health_endpoint(app):
    """Register basic health check endpoint"""
    @app.route('/api/health', methods=['GET'])
    def basic_health():
        return {
            'status': 'healthy',
            'service': 'Smart Attendance System',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
    print("✅ Basic health endpoint registered")

def register_minimal_endpoints(app):
    """Register minimal endpoints for testing"""
    @app.route('/', methods=['GET'])
    def index():
        return {
            'service': 'Smart Attendance System API',
            'status': 'operational',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @app.route('/api/info', methods=['GET'])
    def api_info():
        return {
            'api_version': '1.0.0',
            'status': 'minimal_mode',
            'available_endpoints': ['/', '/api/info', '/api/health'],
            'message': 'Sistema en modo mínimo - algunos blueprints no están disponibles'
        }
    
    register_basic_health_endpoint(app)
    print("✅ Minimal endpoints registered")

def setup_error_handlers(app):
    """Setup global error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'المورد المطلوب غير موجود'
            }
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'حدث خطأ داخلي في الخادم'
            }
        }, 500
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return {
            'success': False,
            'error': {
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': 'تم تجاوز الحد المسموح من الطلبات'
            }
        }, 429

def setup_database(app):
    """Initialize database if needed"""
    
    try:
        from config.database import db
        
        # Test database connection
        result = db.session.execute('SELECT 1').fetchone()
        if result:
            print("✅ Database connection verified")
        
        # Create tables if they don't exist
        db.create_all()
        print("✅ Database tables verified/created")
        
        # Check if we need sample data
        from models import User, Student, Subject, Room
        
        user_count = User.query.count()
        print(f"📊 Current users in database: {user_count}")
        
        if user_count == 0:
            print("📊 Creating sample data...")
            create_sample_data()
            print("✅ Sample data created")
        else:
            print("📊 Sample data already exists")
            
    except Exception as e:
        print(f"❌ Database setup error: {str(e)}")
        print("⚠️ Continuing without database setup...")

def create_sample_data():
    """Create sample data for testing"""
    
    try:
        from config.database import db
        from models import User, Student, Teacher, Subject, Room, UserRole, SectionEnum, StudyTypeEnum, RoomTypeEnum, SemesterEnum
        import secrets
        
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@university.edu',
            full_name='System Administrator',
            role=UserRole.ADMIN,
            is_active=True
        )
        admin_user.set_password('Admin123!')
        db.session.add(admin_user)
        
        # Create sample teacher
        teacher_user = User(
            username='teacher1',
            email='teacher1@university.edu',
            full_name='Dr. Ahmed Mohammed',
            role=UserRole.TEACHER,
            is_active=True
        )
        teacher_user.set_password('Teacher123!')
        db.session.add(teacher_user)
        db.session.flush()
        
        teacher = Teacher(
            user_id=teacher_user.id,
            employee_id='T001',
            department='Computer Science',
            specialization='Software Engineering'
        )
        db.session.add(teacher)
        
        # Create sample students
        for i in range(1, 6):
            student_user = User(
                username=f'cs202400{i}',
                email=f'student{i}@student.university.edu',
                full_name=f'Student {i}',
                role=UserRole.STUDENT,
                is_active=True
            )
            student_user.set_password('Student123!')
            db.session.add(student_user)
            db.session.flush()
            
            student = Student(
                user_id=student_user.id,
                university_id=f'CS202400{i}',
                section=SectionEnum.A,
                study_year=2,
                study_type=StudyTypeEnum.MORNING
            )
            student.set_secret_code(f'SEC{i:03d}')
            db.session.add(student)
        
        # Create sample subjects
        subjects_data = [
            {'code': 'CS201', 'name': 'Data Structures', 'credit_hours': 3, 'study_year': 2, 'semester': SemesterEnum.FIRST},
            {'code': 'CS202', 'name': 'Algorithms', 'credit_hours': 3, 'study_year': 2, 'semester': SemesterEnum.FIRST},
            {'code': 'CS203', 'name': 'Database Systems', 'credit_hours': 3, 'study_year': 2, 'semester': SemesterEnum.SECOND}
        ]
        
        for subject_data in subjects_data:
            subject = Subject(
                department='Computer Science',
                **subject_data
            )
            db.session.add(subject)
        
        # Create sample rooms
        rooms_data = [
            {'name': 'A101', 'building': 'Building A', 'floor': 1, 'capacity': 30, 'lat': 33.3152, 'lng': 44.3661},
            {'name': 'A102', 'building': 'Building A', 'floor': 1, 'capacity': 25, 'lat': 33.3153, 'lng': 44.3662},
            {'name': 'B201', 'building': 'Building B', 'floor': 2, 'capacity': 40, 'lat': 33.3154, 'lng': 44.3663}
        ]
        
        for room_data in rooms_data:
            room = Room(
                name=room_data['name'],
                building=room_data['building'],
                floor=room_data['floor'],
                room_type=RoomTypeEnum.CLASSROOM,
                capacity=room_data['capacity'],
                center_latitude=room_data['lat'],
                center_longitude=room_data['lng'],
                ground_reference_altitude=50.0,
                floor_altitude=50.0 + (room_data['floor'] * 3),
                ceiling_height=3.0
            )
            # Auto-generate GPS polygon
            room.set_rectangular_polygon(room_data['lat'], room_data['lng'])
            db.session.add(room)
        
        db.session.commit()
        print("✅ Sample data created successfully")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating sample data: {str(e)}")

def setup_logging():
    """Setup application logging"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/level3_app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    
    try:
        # Create application
        app = create_level3_app()
        
        # Run development server
        print("\n🌐 Starting development server...")
        print("📍 Server URL: http://localhost:5000")
        print("📚 API Documentation: http://localhost:5000/docs")
        print("🏥 Health Check: http://localhost:5000/api/health")
        print("\n⚡ Press Ctrl+C to stop the server")
        print("=" * 50)
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Avoid reloader issues with context
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Application failed to start: {str(e)}")
        logging.error(f"Application startup error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()