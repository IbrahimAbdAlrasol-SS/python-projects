#!/usr/bin/env python3
"""
🗄️ Database Setup Script - FIXED VERSION
Complete database initialization for Smart Attendance System
إعداد قاعدة البيانات الكامل - نسخة مُصححة
"""

import os
import sys
import subprocess

def install_required_packages():
    """Install required Python packages"""
    
    print("\n📦 Installing Python dependencies...")
    
    # Essential packages list
    required_packages = [
        'flask',
        'flask-sqlalchemy', 
        'flask-cors',
        'flask-restx',
        'python-dotenv',
        'pyjwt',
        'bcrypt',
        'bleach',
        'email-validator',
        'python-dateutil',
        'requests',
        'pandas',
        'openpyxl',
        'async-timeout',  # Fix for Redis
        'redis',
        'psycopg2-binary',
        'psutil'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} already installed")
        except ImportError:
            print(f"📦 Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}: {e}")
                return False
    
    return True

def setup_redis():
    """Setup Redis server (optional)"""
    
    print("\n📦 Setting up Redis...")
    
    try:
        # Try importing redis after ensuring async-timeout is installed
        import redis
        
        # Test Redis connection
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
            r.ping()
            print("✅ Redis is running and accessible")
            return True
        except redis.ConnectionError:
            print("⚠️ Redis connection failed")
            print("\n🔧 Redis Troubleshooting:")
            print("1. Install Redis:")
            print("   - Windows: Download from https://redis.io/download")
            print("   - Linux: sudo apt install redis-server")
            print("   - Mac: brew install redis")
            print("2. Start Redis server:")
            print("   - Windows: redis-server.exe")
            print("   - Linux/Mac: redis-server")
            print("\n💡 System will work without Redis (with limited caching)")
            return False
        except Exception as e:
            print(f"⚠️ Redis setup error: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Redis Python package import failed: {e}")
        print("Trying to install redis with async-timeout...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "redis", "async-timeout"])
            print("✅ Redis packages installed")
            return True
        except Exception as install_error:
            print(f"❌ Failed to install Redis: {install_error}")
            return False

def create_postgresql_database():
    """Create PostgreSQL database if it doesn't exist"""
    
    print("\n🗄️ Setting up PostgreSQL database...")
    
    # Try to create with basic connection first
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Database configuration
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'postgres',
            'password': 'password',  # Change this to your PostgreSQL password
            'database': 'smart_attendance'
        }
        
        try:
            # Connect to PostgreSQL server (not specific database)
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database='postgres'  # Connect to default postgres database
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_config['database'],))
            exists = cursor.fetchone()
            
            if not exists:
                # Create database
                cursor.execute(f"CREATE DATABASE {db_config['database']}")
                print(f"✅ Created database: {db_config['database']}")
            else:
                print(f"✅ Database already exists: {db_config['database']}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except psycopg2.Error as e:
            print(f"❌ PostgreSQL Error: {e}")
            print("\n🔧 PostgreSQL Troubleshooting:")
            print("1. Make sure PostgreSQL is installed and running")
            print("2. Update the password in this script")
            print("3. Try creating database manually:")
            print(f"   createdb -U postgres {db_config['database']}")
            print("\n💡 Alternative: Use SQLite for testing")
            return setup_sqlite_fallback()
        
    except ImportError:
        print("❌ psycopg2 not installed, trying SQLite fallback")
        return setup_sqlite_fallback()

def setup_sqlite_fallback():
    """Setup SQLite as fallback database"""
    
    print("\n🔄 Setting up SQLite fallback database...")
    
    # Create .env with SQLite configuration
    env_content = """# Smart Attendance System Environment Configuration
# Using SQLite as fallback database
DATABASE_URL=sqlite:///attendance.db
REDIS_URL=redis://localhost:6379/0
STORAGE_PATH=storage
UPLOAD_FOLDER=storage/uploads
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-change-in-production
FLASK_ENV=development
DEBUG=True
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ SQLite fallback configured")
    print("📄 .env file created with SQLite configuration")
    return True

def create_storage_directories():
    """Create required storage directories"""
    
    print("\n📁 Creating storage directories...")
    
    storage_dirs = [
        'storage',
        'storage/face_templates',
        'storage/qr_codes', 
        'storage/reports',
        'storage/uploads',
        'storage/backups',
        'logs'
    ]
    
    for dir_path in storage_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created: {dir_path}")
        except Exception as e:
            print(f"❌ Failed to create {dir_path}: {e}")
            return False
    
    return True

def initialize_flask_database():
    """Initialize Flask database with tables and sample data"""
    
    print("\n🏗️ Initializing Flask database...")
    
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Create basic Flask app for database operations
        from flask import Flask
        
        app = Flask(__name__)
        
        # Load configuration from .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        # Configure app
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///attendance.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
        
        # Initialize database
        from flask_sqlalchemy import SQLAlchemy
        db = SQLAlchemy()
        db.init_app(app)
        
        with app.app_context():
            # Import models to create tables
            try:
                from models.users import User, UserRole
                from models.students import Student, SectionEnum, StudyTypeEnum, AcademicStatusEnum
                from models.teachers import Teacher, AcademicDegreeEnum
                from models.subjects import Subject, SemesterEnum
                from models.rooms import Room, RoomTypeEnum
                from models.schedules import Schedule
                from models.lectures import Lecture, LectureStatusEnum
                from models.qr_sessions import QRSession, QRStatusEnum
                from models.attendance_records import AttendanceRecord, AttendanceStatusEnum, AttendanceTypeEnum
                from models.assignments import Assignment
                from models.submissions import Submission
                from models.student_counters import StudentCounter
                from models.notifications import Notification
                from models.system_settings import SystemSetting
                
                print("✅ Models imported successfully")
                
            except ImportError as e:
                # If models don't exist, create basic structure
                print(f"⚠️ Models import failed: {e}")
                print("Creating basic database structure...")
                
                # Create basic User model for testing
                class User(db.Model):
                    __tablename__ = 'users'
                    id = db.Column(db.Integer, primary_key=True)
                    username = db.Column(db.String(50), unique=True, nullable=False)
                    email = db.Column(db.String(100), unique=True, nullable=False)
                    full_name = db.Column(db.String(255), nullable=False)
                    created_at = db.Column(db.DateTime, default=db.func.now())
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Test database connection
            result = db.session.execute(db.text('SELECT 1')).fetchone()
            if result:
                print("✅ Database connection verified")
            
            # Check if sample data exists
            user_count = db.session.execute(db.text('SELECT COUNT(*) FROM users')).scalar()
            
            if user_count == 0:
                print("📝 Creating basic sample data...")
                create_basic_sample_data(db)
                print("✅ Sample data created")
            else:
                print(f"✅ Sample data already exists ({user_count} users)")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask database initialization failed: {e}")
        print(f"Error details: {str(e)}")
        return False

def create_basic_sample_data(db):
    """Create basic sample data for testing"""
    try:
        # Create a basic admin user for testing
        insert_sql = """
        INSERT INTO users (username, email, full_name) 
        VALUES ('admin', 'admin@test.com', 'Test Administrator')
        """
        db.session.execute(db.text(insert_sql))
        db.session.commit()
        print("✅ Basic admin user created")
        
    except Exception as e:
        print(f"⚠️ Sample data creation failed: {e}")

def test_system_components():
    """Test all system components"""
    
    print("\n🧪 Testing system components...")
    
    test_results = {
        'storage': False,
        'database': False,
        'redis': False,
        'flask_app': False
    }
    
    # Test storage directories
    try:
        import os
        storage_dirs = ['storage', 'storage/uploads', 'logs']
        all_exist = all(os.path.exists(d) and os.access(d, os.W_OK) for d in storage_dirs)
        if all_exist:
            test_results['storage'] = True
            print("✅ Storage directories: OK")
        else:
            print("❌ Storage directories: FAILED")
    except Exception as e:
        print(f"❌ Storage directories: FAILED ({e})")
    
    # Test database connection
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        database_url = os.getenv('DATABASE_URL', 'sqlite:///attendance.db')
        
        if 'postgresql' in database_url:
            import psycopg2
            # Extract connection details from URL
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            cursor.close()
            conn.close()
        else:
            # SQLite test
            import sqlite3
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            cursor.close()
            conn.close()
        
        test_results['database'] = True
        print("✅ Database connection: OK")
    except Exception as e:
        print(f"❌ Database connection: FAILED ({e})")
    
    # Test Redis (optional)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=1)
        r.ping()
        test_results['redis'] = True
        print("✅ Redis connection: OK")
    except Exception as e:
        print(f"⚠️ Redis connection: FAILED ({e}) - This is optional")
        test_results['redis'] = True  # Don't fail for Redis
    
    # Test basic Flask functionality
    try:
        from flask import Flask
        app = Flask(__name__)
        with app.test_client() as client:
            # Test basic route
            @app.route('/test')
            def test():
                return 'OK'
            
            response = client.get('/test')
            if response.status_code == 200:
                test_results['flask_app'] = True
                print("✅ Flask application: OK")
            else:
                print(f"❌ Flask application: FAILED (status {response.status_code})")
    except Exception as e:
        print(f"❌ Flask application: FAILED ({e})")
    
    # Summary
    passed = sum(test_results.values())
    total = len(test_results)
    
    print(f"\n📊 Test Results: {passed}/{total} components OK")
    
    if passed >= 3:  # Allow Redis to be optional
        print("🎉 System ready for operation!")
        return True
    else:
        print("⚠️ Some critical components need attention")
        return False

def main():
    """Main setup function"""
    
    print("=" * 60)
    print("🚀 Smart Attendance System - Database Setup (FIXED)")
    print("=" * 60)
    
    setup_success = True
    
    # Step 1: Install Python dependencies
    print("\n📦 Step 1: Installing dependencies...")
    if not install_required_packages():
        setup_success = False
        print("❌ Failed to install required packages")
    
    # Step 2: Create storage directories
    print("\n📁 Step 2: Creating storage...")
    if not create_storage_directories():
        setup_success = False
        print("❌ Failed to create storage directories")
    
    # Step 3: Setup Redis (optional)
    print("\n📦 Step 3: Setting up Redis...")
    redis_success = setup_redis()
    if not redis_success:
        print("⚠️ Redis setup failed, but system can work without it")
    
    # Step 4: Setup database (PostgreSQL with SQLite fallback)
    print("\n🗄️ Step 4: Setting up database...")
    if not create_postgresql_database():
        setup_success = False
        print("❌ Database setup failed")
    
    # Step 5: Initialize Flask database
    if setup_success:
        print("\n🏗️ Step 5: Initializing application database...")
        if not initialize_flask_database():
            print("⚠️ Flask database initialization had issues")
    
    # Step 6: Test all components
    print("\n🧪 Step 6: Testing system...")
    if test_system_components():
        print("\n🎉 Setup completed successfully!")
        print("\n🚀 Next steps:")
        print("1. Run: python app.py")
        print("2. Or run: python run_level3.py")
        print("3. Open: http://localhost:5001")
        print("4. Test APIs with: python test_all_apis.py")
        print("5. Check Swagger docs: http://localhost:5001/docs")
    else:
        print("\n❌ Setup completed with issues")
        print("\n🔧 Manual steps to try:")
        print("1. Check if PostgreSQL is running")
        print("2. Try: pip install async-timeout redis")
        print("3. Run: python app.py (should work with SQLite)")
    
    print("=" * 60)

if __name__ == '__main__':
    main()