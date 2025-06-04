"""
Quick Fix Script - حل سريع لجميع المشاكل
IMMEDIATE SOLUTION FOR ALL ISSUES
"""

import os
import sys

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_content = """# Smart Attendance System Environment Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/attendance_db
REDIS_URL=redis://localhost:6379/0
STORAGE_PATH=storage
UPLOAD_FOLDER=storage/uploads
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Created .env file")
    else:
        print("ℹ️ .env file already exists")

def update_models_init():
    """Update models/__init__.py to fix import issues"""
    content = '''"""
Models Package Initialization
تهيئة جميع النماذج وتصديرها - FIXED VERSION
"""

# Import models in order to avoid circular imports
from .users import User, UserRole
from .students import Student, SectionEnum, StudyTypeEnum, AcademicStatusEnum  
from .teachers import Teacher, AcademicDegreeEnum
from .subjects import Subject, SemesterEnum
from .rooms import Room, RoomTypeEnum

# Export all models and enums
__all__ = [
    'User', 'Student', 'Teacher', 'Subject', 'Room',
    'UserRole', 'SectionEnum', 'StudyTypeEnum', 'AcademicStatusEnum',
    'AcademicDegreeEnum', 'SemesterEnum', 'RoomTypeEnum'
]
'''
    
    with open('models/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Updated models/__init__.py")

def update_database_config():
    """Update database config to fix SQL syntax"""
    content = '''"""
Database Configuration Module - FIXED
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
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/attendance_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    STORAGE_PATH = os.getenv('STORAGE_PATH', 'storage')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'storage/uploads')
    
    @staticmethod
    def init_app(app: Flask):
        db.init_app(app)
        migrate.init_app(app, db)
        redis_client.init_app(app)
        
        import pathlib
        pathlib.Path(app.config['STORAGE_PATH']).mkdir(parents=True, exist_ok=True)
        pathlib.Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
        
    @staticmethod
    def test_connection():
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            print("✅ PostgreSQL connection successful")
            return True
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    @staticmethod
    def test_redis():
        try:
            redis_client.ping()
            print("✅ Redis connection successful")
            return True
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False
'''
    
    with open('config/database.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Updated config/database.py")

def create_missing_storage_manager():
    """Create missing storage manager"""
    os.makedirs('storage', exist_ok=True)
    
    storage_content = '''"""
File Storage Manager
إدارة الملفات والتخزين
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
        print("✅ Storage directory structure created at storage")
    
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
    
    os.makedirs('storage', exist_ok=True)
    with open('storage/__init__.py', 'w', encoding='utf-8') as f:
        f.write('')
        
    with open('storage/file_manager.py', 'w', encoding='utf-8') as f:
        f.write(storage_content)
    print("✅ Created storage/file_manager.py")

def main():
    """Run all fixes"""
    print("🔧 Running Quick Fix Script...")
    print("=" * 50)
    
    try:
        create_env_file()
        update_models_init()
        update_database_config()
        create_missing_storage_manager()
        
        print("=" * 50)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
        print("🚀 Now run: python setup_level1.py")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")

if __name__ == "__main__":
    main()
