"""
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
