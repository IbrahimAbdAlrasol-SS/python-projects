"""
Level 1 Setup Script
سكريبت إعداد وتشغيل المستوى الأول - Windows Compatible
"""

import os
import sys
from flask import Flask
from config.database import DatabaseConfig, db, redis_client
from models import *
from database.indexes import create_performance_indexes
from cache.redis_manager import test_redis_connection, clear_all_cache
from storage.file_manager import FileStorageManager
from data.sample_data import SampleDataGenerator, test_sample_data
from tests.test_database import run_database_tests

def create_app():
    """Create Flask application"""
    app = Flask(__name__)
    app.config.from_object(DatabaseConfig)
    DatabaseConfig.init_app(app)
    return app

def setup_database():
    """Set up database with tables and indexes"""
    print("🗄️ Setting up PostgreSQL database...")
    
    try:
        if not DatabaseConfig.test_connection():
            return False
        
        print("📋 Creating database tables...")
        db.create_all()
        print("✅ All tables created successfully")
        
        print("🔍 Creating performance indexes...")
        create_performance_indexes()
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def setup_redis():
    """Set up Redis cache"""
    print("🔄 Setting up Redis cache...")
    
    try:
        if not DatabaseConfig.test_redis():
            return False
        
        if not test_redis_connection():
            return False
        
        print("🗑️ Clearing existing cache...")
        clear_all_cache()
        
        return True
        
    except Exception as e:
        print(f"❌ Redis setup failed: {e}")
        return False

def setup_storage():
    """Set up file storage"""
    print("📁 Setting up file storage...")
    
    try:
        storage_manager = FileStorageManager()
        
        # Test storage operations
        test_data = b"Test file content"
        result = storage_manager.save_file(test_data, 'temp', 'test.txt')
        
        if result['success']:
            print("✅ File storage setup successful")
            return True
        else:
            print(f"❌ File storage test failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Storage setup failed: {e}")
        return False

def generate_sample_data():
    """Generate sample data for testing"""
    print("📊 Generating sample data...")
    
    try:
        sample_data = SampleDataGenerator.generate_all_sample_data()
        
        if sample_data:
            print("✅ Sample data generated successfully")
            test_sample_data()
            return True
        else:
            print("❌ Sample data generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Sample data generation failed: {e}")
        return False

def validate_setup():
    """Validate the complete setup"""
    print("🔍 Validating setup...")
    
    validation_results = {
        'database_connection': False,
        'redis_connection': False,
        'file_storage': False,
        'sample_data': False,
        'performance_tests': False
    }
    
    try:
        # Test database connection
        validation_results['database_connection'] = DatabaseConfig.test_connection()
        
        # Test Redis connection
        validation_results['redis_connection'] = DatabaseConfig.test_redis()
        
        # Test file storage
        storage_manager = FileStorageManager()
        stats = storage_manager.get_storage_stats()
        validation_results['file_storage'] = bool(stats)
        
        # Test sample data
        validation_results['sample_data'] = User.query.count() > 0
        
        # Run performance tests
        validation_results['performance_tests'] = run_database_tests()
        
        # Print results
        print("")
        print("📊 Validation Results:")
        for test_name, result in validation_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        # Overall result
        all_passed = all(validation_results.values())
        if all_passed:
            print("")
            print("🎉 Level 1 setup completed successfully!")
            print("🚀 Ready to proceed to Level 2 (Security & Authentication)")
        else:
            print("")
            print("⚠️ Some validation tests failed. Please check the issues above.")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🏗️ Starting Level 1: Database Foundation Setup (Windows)")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        steps = [
            ("Database Setup", setup_database),
            ("Redis Setup", setup_redis),
            ("Storage Setup", setup_storage),
            ("Sample Data Generation", generate_sample_data),
            ("Setup Validation", validate_setup)
        ]
        
        failed_steps = []
        
        for step_name, step_function in steps:
            print(f"")
            print(f"🔄 {step_name}...")
            try:
                if not step_function():
                    failed_steps.append(step_name)
            except Exception as e:
                print(f"❌ {step_name} failed with exception: {e}")
                failed_steps.append(step_name)
        
        # Final summary
        print("")
        print("=" * 60)
        if not failed_steps:
            print("🎉 LEVEL 1 COMPLETED SUCCESSFULLY!")
            print("✅ Database Foundation is ready")
            print("🚀 You can now proceed to Level 2: Security & Authentication")
            
            # Print useful information
            print("")
            print("📝 Useful Information:")
            print("   Admin Login: admin / Admin123!")
            print("   Redis: localhost:6379")
            print("   Storage: .\\storage\\ directory structure created")
            
        else:
            print("❌ LEVEL 1 SETUP FAILED")
            print(f"⚠️ Failed steps: {', '.join(failed_steps)}")
            print("🔧 Please check the error messages above and fix the issues")
        
        print("=" * 60)

if __name__ == "__main__":
    main()
