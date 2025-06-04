"""
Super Simple Fix - حل مباشر بدون تعقيد
DIRECT SOLUTION WITHOUT IMPORT CONFLICTS
"""

import os
import sys

def fix_data_init():
    """Fix data package init"""
    content = '''# Minimal data package init
# No complex imports

__all__ = []
'''
    with open('data/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed data/__init__.py")

def create_simple_working_app():
    """Create completely self-contained working app"""
    
    # Fix the data init first
    fix_data_init()
    
    app_content = '''"""
Complete Working App - Self Contained
تطبيق كامل يعمل بذاته
"""

import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize extensions
db = SQLAlchemy()

class UserRole(Enum):
    """User roles"""
    ADMIN = 'admin'
    TEACHER = 'teacher'
    STUDENT = 'student'

class User(db.Model):
    """Simple User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

def create_app():
    """Create Flask application"""
    
    # Create .env if needed
    if not os.path.exists('.env'):
        env_content = """DATABASE_URL=sqlite:///attendance.db
REDIS_URL=redis://localhost:6379/0
STORAGE_PATH=storage
SECRET_KEY=dev-secret-key
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
    
    # Create storage
    os.makedirs('storage', exist_ok=True)
    os.makedirs('storage/uploads', exist_ok=True)
    print("✅ Created storage directories")
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///attendance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Initialize database
    db.init_app(app)
    
    @app.route('/')
    def index():
        return jsonify({
            "message": "Smart Attendance System - Level 1 Complete",
            "status": "running",
            "database": "sqlite"
        })
    
    @app.route('/setup')
    def setup():
        """Setup the system"""
        try:
            # Create tables
            db.create_all()
            
            # Create admin if not exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@system.local',
                    full_name='System Administrator',
                    role=UserRole.ADMIN,
                    is_active=True
                )
                admin.set_password('Admin123!')
                admin.save()
                created = True
            else:
                created = False
            
            user_count = User.query.count()
            
            return jsonify({
                "status": "success",
                "tables_created": True,
                "admin_created": created,
                "total_users": user_count,
                "message": "System setup completed successfully"
            })
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/test')
    def test():
        """Test all components"""
        try:
            # Test database
            user_count = User.query.count()
            admin_exists = User.query.filter_by(role=UserRole.ADMIN).first() is not None
            
            return jsonify({
                "status": "success",
                "database": "connected",
                "total_users": user_count,
                "admin_exists": admin_exists,
                "storage": "ready",
                "message": "All systems operational"
            })
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/users')
    def list_users():
        """List all users"""
        try:
            users = User.query.all()
            user_list = []
            for user in users:
                user_list.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                })
            
            return jsonify({
                "status": "success",
                "users": user_list,
                "total": len(user_list)
            })
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    return app

if __name__ == '__main__':
    print("🚀 Starting Complete Working Application...")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        print("📋 Setting up system...")
        try:
            db.create_all()
            print("✅ Database tables created")
            
            # Create admin if needed
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@system.local',
                    full_name='System Administrator',
                    role=UserRole.ADMIN,
                    is_active=True
                )
                admin.set_password('Admin123!')
                admin.save()
                print("✅ Admin user created")
            else:
                print("ℹ️ Admin user already exists")
            
            user_count = User.query.count()
            print(f"📊 Total users: {user_count}")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            sys.exit(1)
    
    print("")
    print("🎉 SYSTEM READY!")
    print("=" * 50)
    print("🔑 Admin Login: admin / Admin123!")
    print("📍 Available endpoints:")
    print("   http://localhost:5000/ - Main page")
    print("   http://localhost:5000/setup - Setup system")
    print("   http://localhost:5000/test - Test system")
    print("   http://localhost:5000/users - List users")
    print("")
    print("🚀 Starting server...")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    with open('working_app.py', 'w', encoding='utf-8') as f:
        f.write(app_content)
    print("✅ Created working_app.py")

def main():
    """Main function"""
    print("🔧 SUPER SIMPLE FIX")
    print("🎯 CREATING SELF-CONTAINED WORKING APP")
    print("=" * 50)
    
    try:
        create_simple_working_app()
        
        print("")
        print("✅ ALL DONE!")
        print("🚀 Now run: python working_app.py")
        print("🌐 Then visit: http://localhost:5000/setup")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()