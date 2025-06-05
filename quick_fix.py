#!/usr/bin/env python3
"""
⚡ Quick Fix Script - إصلاح سريع لجميع المشاكل
Smart Attendance System - Emergency Fix
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run command and show result"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print("⚡ QUICK FIX - Smart Attendance System")
    print("=" * 50)
    
    # Fix 1: Install missing packages
    packages = [
        "async-timeout",
        "redis", 
        "flask",
        "flask-sqlalchemy",
        "python-dotenv",
        "werkzeug"
    ]
    
    for package in packages:
        run_command(f"pip install {package}", f"Installing {package}")
    
    # Fix 2: Create .env file
    print("\n📄 Creating .env file...")
    env_content = """DATABASE_URL=sqlite:///attendance.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key
DEBUG=True
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
    except Exception as e:
        print(f"❌ .env creation failed: {e}")
    
    # Fix 3: Create storage directories
    print("\n📁 Creating directories...")
    dirs = ['storage', 'storage/uploads', 'logs']
    for directory in dirs:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created {directory}")
        except Exception as e:
            print(f"❌ Failed to create {directory}: {e}")
    
    # Fix 4: Test system
    print("\n🧪 Testing system...")
    
    # Test imports
    test_imports = ['flask', 'sqlite3', 'datetime']
    for module in test_imports:
        try:
            __import__(module)
            print(f"✅ {module} import OK")
        except ImportError as e:
            print(f"❌ {module} import failed: {e}")
    
    print("\n🎉 Quick fix completed!")
    print("\n🚀 Try running:")
    print("   python run_simple.py")
    print("   or")
    print("   python setup_database_fixed.py")

if __name__ == '__main__':
    main()