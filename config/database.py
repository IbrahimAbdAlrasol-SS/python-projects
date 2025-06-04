"""
Database Configuration Module
إعدادات قاعدة البيانات والاتصال
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_redis import FlaskRedis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
"""
Database Configuration Module
إعدادات قاعدة البيانات والاتصال - FIXED VERSION
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_redis import FlaskRedis
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
redis_client = FlaskRedis()

class DatabaseConfig:
    """Database configuration class"""
    
    # PostgreSQL Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/attendance_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'max_overflow': 20
    }
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Storage Configuration (Windows compatible)
    STORAGE_PATH = os.getenv('STORAGE_PATH', r'.\storage')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', r'.\storage\uploads')
    
    @staticmethod
    def init_app(app: Flask):
        """Initialize database with Flask app"""
        db.init_app(app)
        migrate.init_app(app, db)
        redis_client.init_app(app)
        
        # Create storage directories (Windows compatible)
        import pathlib
        pathlib.Path(app.config['STORAGE_PATH']).mkdir(parents=True, exist_ok=True)
        pathlib.Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
        
    @staticmethod
    def create_tables():
        """Create all database tables"""
        db.create_all()
            
    @staticmethod
    def test_connection():
        """Test database connection - FIXED"""
        try:
            # FIX: Use text() for raw SQL
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            print("✅ PostgreSQL connection successful")
            return True
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    @staticmethod
    def test_redis():
        """Test Redis connection"""
        try:
            redis_client.ping()
            print("✅ Redis connection successful")
            return True
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return Falseextensions
db = SQLAlchemy()
migrate = Migrate()
redis_client = FlaskRedis()

class DatabaseConfig:
    """Database configuration class"""
    
    # PostgreSQL Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'max_overflow': 20
    }
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL')
    
    # Storage Configuration (Windows compatible)
    STORAGE_PATH = os.getenv('STORAGE_PATH', r'.\storage')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', r'.\storage\uploads')
    
    @staticmethod
    def init_app(app: Flask):
        """Initialize database with Flask app"""
        db.init_app(app)
        migrate.init_app(app, db)
        redis_client.init_app(app)
        
        # Create storage directories (Windows compatible)
        import pathlib
        pathlib.Path(app.config['STORAGE_PATH']).mkdir(parents=True, exist_ok=True)
        pathlib.Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
        
    @staticmethod
    def create_tables():
        """Create all database tables"""
        db.create_all()
            
    @staticmethod
    def test_connection():
        """Test database connection"""
        try:
            db.session.execute('SELECT 1')
            print("✅ PostgreSQL connection successful")
            return True
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    @staticmethod
    def test_redis():
        """Test Redis connection"""
        try:
            redis_client.ping()
            print("✅ Redis connection successful")
            return True
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False
