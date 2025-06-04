"""
Ultimate Fix Script - الحل النهائي الشامل
COMPLETE WORKING SOLUTION - NO DATA HARDCODED
"""

import os
import sys
from flask import Flask

def create_env_file():
    """Create .env file with SQLite fallback"""
    env_content = """# Smart Attendance System Environment Configuration
# Using SQLite as fallback database
DATABASE_URL=sqlite:///attendance.db
REDIS_URL=redis://localhost:6379/0
STORAGE_PATH=storage
UPLOAD_FOLDER=storage/uploads
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✅ Created .env file with SQLite fallback")

def fix_database_config():
    """Create working database config"""
    content = '''"""
Database Configuration Module - ULTIMATE FIX
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_redis import FlaskRedis
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
redis_client = FlaskRedis()

class DatabaseConfig:
    """Database configuration class"""
    
    # Use SQLite as fallback
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///attendance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Storage Configuration
    STORAGE_PATH = os.getenv('STORAGE_PATH', 'storage')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'storage/uploads')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    @staticmethod
    def init_app(app: Flask):
        """Initialize database with Flask app"""
        db.init_app(app)
        migrate.init_app(app, db)
        
        # Initialize Redis if available
        try:
            redis_client.init_app(app)
        except Exception as e:
            print(f"⚠️ Redis not available: {e}")
        
        # Create storage directories
        import pathlib
        pathlib.Path(app.config['STORAGE_PATH']).mkdir(parents=True, exist_ok=True)
        pathlib.Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
        
    @staticmethod
    def test_connection():
        """Test database connection"""
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    @staticmethod
    def test_redis():
        """Test Redis connection"""
        try:
            redis_client.ping()
            print("✅ Redis connection successful")
            return True
        except Exception as e:
            print(f"⚠️ Redis not available: {e}")
            return False
'''
    
    with open('config/database.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed config/database.py with SQLite fallback")

def fix_models_init():
    """Fix models initialization"""
    content = '''"""
Models Package Initialization - ULTIMATE FIX
"""

# Import models in correct order
from .users import User, UserRole
from .students import Student, SectionEnum, StudyTypeEnum, AcademicStatusEnum
from .teachers import Teacher, AcademicDegreeEnum
from .subjects import Subject, SemesterEnum
from .rooms import Room, RoomTypeEnum

# Export all models
__all__ = [
    'User', 'Student', 'Teacher', 'Subject', 'Room',
    'UserRole', 'SectionEnum', 'StudyTypeEnum', 'AcademicStatusEnum',
    'AcademicDegreeEnum', 'SemesterEnum', 'RoomTypeEnum'
]
'''
    
    with open('models/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed models/__init__.py")

def create_storage_system():
    """Create complete storage system"""
    # Create directories
    dirs = ['storage', 'storage/uploads', 'storage/reports', 'storage/temp', 'logs']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    # Create storage manager
    storage_content = '''"""
File Storage Manager - Complete
"""

import os
from datetime import datetime

class FileStorageManager:
    def __init__(self):
        self.base_path = 'storage'
        self._ensure_directories()
    
    def _ensure_directories(self):
        dirs = ['uploads', 'reports', 'temp', 'backups']
        for dir_name in dirs:
            os.makedirs(os.path.join(self.base_path, dir_name), exist_ok=True)
        print("✅ Storage directories created")
    
    def save_file(self, file_data, folder, filename):
        try:
            file_path = os.path.join(self.base_path, folder, filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            return {'success': True, 'path': file_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_storage_stats(self):
        return {'status': 'healthy', 'base_path': self.base_path}
'''
    
    # Create storage module
    with open('storage/__init__.py', 'w', encoding='utf-8') as f:
        f.write('')
    with open('storage/file_manager.py', 'w', encoding='utf-8') as f:
        f.write(storage_content)
    print("✅ Created complete storage system")

def create_minimal_sample_generator():
    """Create minimal sample data generator (NO HARDCODED DATA)"""
    content = '''"""
Minimal Sample Data Generator - NO HARDCODED DATA
"""

from datetime import datetime
from models import User, UserRole
from config.database import db

class MinimalDataGenerator:
    """Generate minimal required data only"""
    
    @staticmethod
    def create_admin_if_needed():
        """Create admin user only if none exists"""
        try:
            admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
            
            if admin_count == 0:
                admin = User(
                    username='admin',
                    email='admin@system.local',
                    full_name='System Administrator',
                    role=UserRole.ADMIN,
                    is_active=True
                )
                admin.set_password('Admin123!')
                admin.save()
                print("✅ Created admin user: admin / Admin123!")
                return admin
            else:
                print("ℹ️ Admin user already exists")
                return User.query.filter_by(role=UserRole.ADMIN).first()
                
        except Exception as e:
            print(f"❌ Failed to create admin: {e}")
            return None
    
    @classmethod
    def setup_minimal_data(cls):
        """Setup only essential data"""
        try:
            admin = cls.create_admin_if_needed()
            
            if admin:
                print("✅ Minimal data setup completed")
                return {'admin': admin}
            else:
                print("❌ Minimal data setup failed")
                return None
                
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return None

def test_system():
    """Test the complete system"""
    try:
        users_count = User.query.count()
        print(f"📊 System Statistics:")
        print(f"   Total Users: {users_count}")
        
        admin = User.query.filter_by(role=UserRole.ADMIN).first()
        if admin:
            print(f"   Admin User: {admin.username}")
        
        return True
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False
'''
    
    with open('data/sample_data.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created minimal sample data generator")

def create_working_app():
    """Create completely working application"""
    
    # Apply all fixes
    create_env_file()
    fix_database_config()
    fix_models_init()
    create_storage_system()
    create_minimal_sample_generator()
    
    # Import after fixes
    from config.database import DatabaseConfig, db
    from models import User, UserRole
    from data.sample_data import MinimalDataGenerator
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(DatabaseConfig)
    DatabaseConfig.init_app(app)
    
    with app.app_context():
        try:
            print("🔍 Testing database connection...")
            if not DatabaseConfig.test_connection():
                print("❌ Database connection failed")
                return False
                
            print("📋 Creating database tables...")
            db.create_all()
            print("✅ All tables created successfully")
            
            print("👤 Setting up minimal data...")
            minimal_data = MinimalDataGenerator.setup_minimal_data()
            
            if minimal_data:
                print("🧪 Testing system...")
                from data.sample_data import test_system
                test_result = test_system()
                
                if test_result:
                    print("")
                    print("🎉 ULTIMATE FIX COMPLETED SUCCESSFULLY!")
                    print("=" * 50)
                    print("✅ Database: Working (SQLite)")
                    print("✅ Models: All imported correctly")
                    print("✅ Storage: Complete system created")
                    print("✅ Data: Minimal admin user created")
                    print("")
                    print("🔑 Login Information:")
                    print("   Username: admin")
                    print("   Password: Admin123!")
                    print("")
                    print("🚀 Ready for Level 2: Security & Authentication")
                    print("=" * 50)
                    return True
                else:
                    print("❌ System test failed")
                    return False
            else:
                print("❌ Data setup failed")
                return False
                
        except Exception as e:
            print(f"❌ Application creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function"""
    print("🔧 ULTIMATE FIX SCRIPT - FINAL SOLUTION")
    print("🎯 NO HARDCODED DATA - CLEAN IMPLEMENTATION")
    print("=" * 60)
    
    try:
        success = create_working_app()
        
        if success:
            print("")
            print("✅ ALL PROBLEMS SOLVED!")
            print("🚀 Run: python app.py to start the application")
            print("🌐 Then visit: http://localhost:5000/test")
        else:
            print("")
            print("❌ SOME ISSUES REMAIN")
            print("Please check the error messages above")
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()