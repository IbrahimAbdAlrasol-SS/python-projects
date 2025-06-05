#!/usr/bin/env python3
"""
🗄️ Database Setup Script - إعداد قاعدة البيانات الكامل
Complete database initialization for Smart Attendance System
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_postgresql_database():
    """Create PostgreSQL database if it doesn't exist"""
    
    print("🗄️ Setting up PostgreSQL database...")
    
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
        print("\n🔧 Troubleshooting:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Update the password in this script to match your PostgreSQL password")
        print("3. Create database manually if needed:")
        print(f"   createdb -U postgres {db_config['database']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def setup_redis():
    """Setup Redis server"""
    
    print("\n📦 Setting up Redis...")
    
    try:
        import redis
        
        # Test Redis connection
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running and accessible")
        return True
        
    except redis.ConnectionError:
        print("❌ Redis connection failed")
        print("\n🔧 Troubleshooting:")
        print("1. Install Redis: https://redis.io/download")
        print("2. Start Redis server:")
        print("   - Windows: redis-server.exe")
        print("   - Linux/Mac: redis-server")
        print("3. Or install via package manager:")
        print("   - Ubuntu: sudo apt install redis-server")
        print("   - Mac: brew install redis")
        return False
    except ImportError:
        print("❌ Redis Python package not installed")
        print("Install with: pip install redis")
        return False

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
    
    return True

def install_python_dependencies():
    """Install required Python packages"""
    
    print("\n📦 Installing Python dependencies...")
    
    required_packages = [
        'flask',
        'flask-sqlalchemy',
        'flask-cors',
        'flask-restx',
        'psycopg2-binary',
        'redis',
        'pyjwt',
        'bcrypt',
        'bleach',
        'email-validator',
        'python-dateutil',
        'requests',
        'pandas',
        'openpyxl'
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

def initialize_flask_database():
    """Initialize Flask database with tables and sample data"""
    
    print("\n🏗️ Initializing Flask database...")
    
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import Flask app and models
        from run_level3 import create_complete_app
        
        app = create_complete_app()
        
        with app.app_context():
            from config.database import db
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Check if sample data exists
            from models import User
            user_count = User.query.count()
            
            if user_count == 0:
                print("📝 Creating sample data...")
                from run_level3 import create_comprehensive_sample_data
                create_comprehensive_sample_data()
                print("✅ Sample data created")
            else:
                print(f"✅ Sample data already exists ({user_count} users)")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask database initialization failed: {e}")
        print("\nError details:", str(e))
        return False

def test_system_components():
    """Test all system components"""
    
    print("\n🧪 Testing system components...")
    
    test_results = {
        'database': False,
        'redis': False,
        'flask_app': False,
        'storage': False
    }
    
    # Test PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            user='postgres',
            password='password',
            database='smart_attendance'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        cursor.close()
        conn.close()
        test_results['database'] = True
        print("✅ PostgreSQL connection: OK")
    except Exception as e:
        print(f"❌ PostgreSQL connection: FAILED ({e})")
    
    # Test Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        test_results['redis'] = True
        print("✅ Redis connection: OK")
    except Exception as e:
        print(f"❌ Redis connection: FAILED ({e})")
    
    # Test Flask app
    try:
        from run_level3 import create_complete_app
        app = create_complete_app()
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                test_results['flask_app'] = True
                print("✅ Flask application: OK")
            else:
                print(f"❌ Flask application: FAILED (status {response.status_code})")
    except Exception as e:
        print(f"❌ Flask application: FAILED ({e})")
    
    # Test storage directories
    try:
        import os
        storage_dirs = ['storage', 'storage/face_templates', 'logs']
        all_exist = all(os.path.exists(d) and os.access(d, os.W_OK) for d in storage_dirs)
        if all_exist:
            test_results['storage'] = True
            print("✅ Storage directories: OK")
        else:
            print("❌ Storage directories: FAILED")
    except Exception as e:
        print(f"❌ Storage directories: FAILED ({e})")
    
    # Summary
    passed = sum(test_results.values())
    total = len(test_results)
    
    print(f"\n📊 Test Results: {passed}/{total} components OK")
    
    if passed == total:
        print("🎉 All systems ready!")
        return True
    else:
        print("⚠️ Some components need attention")
        return False

def main():
    """Main setup function"""
    
    print("=" * 60)
    print("🚀 Smart Attendance System - Complete Setup")
    print("=" * 60)
    
    setup_success = True
    
    # Step 1: Install Python dependencies
    if not install_python_dependencies():
        setup_success = False
    
    # Step 2: Create storage directories
    if not create_storage_directories():
        setup_success = False
    
    # Step 3: Setup PostgreSQL database
    if not create_postgresql_database():
        setup_success = False
    
    # Step 4: Setup Redis
    if not setup_redis():
        setup_success = False
    
    # Step 5: Initialize Flask database
    if setup_success and not initialize_flask_database():
        setup_success = False
    
    # Step 6: Test all components
    print("\n" + "=" * 60)
    if test_system_components():
        print("🎉 Setup completed successfully!")
        print("\n🚀 Next steps:")
        print("1. Run: python run_level3.py")
        print("2. Open: http://localhost:5000")
        print("3. Test APIs with Postman or Swagger (/docs)")
        print("4. Check health: http://localhost:5000/api/health")
    else:
        print("❌ Setup completed with issues")
        print("\n🔧 Please fix the failed components and run setup again")
    
    print("=" * 60)

if __name__ == '__main__':
    main()