"""
Final Setup Script - الحل الشامل والنهائي
COMPLETE WORKING SOLUTION FOR LEVEL 1
"""

import os
import sys
from flask import Flask
from sqlalchemy import text

def create_env_file():
    """Create .env file"""
    env_content = """DATABASE_URL=postgresql://postgres:password@localhost:5432/attendance_db
REDIS_URL=redis://localhost:6379/0
STORAGE_PATH=storage
UPLOAD_FOLDER=storage/uploads
SECRET_KEY=dev-secret-key
FLASK_ENV=development
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")

def setup_storage():
    """Setup storage directories"""
    dirs = ['storage', 'storage/uploads', 'storage/reports', 'storage/temp', 'logs']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    # Create file manager
    storage_content = '''"""File Storage Manager"""
import os

class FileStorageManager:
    def __init__(self):
        self.base_path = 'storage'
    
    def save_file(self, file_data, folder, filename):
        try:
            file_path = os.path.join(self.base_path, folder, filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            return {'success': True, 'path': file_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_storage_stats(self):
        return {'status': 'healthy'}
'''
    
    with open('storage/__init__.py', 'w') as f:
        f.write('')
    with open('storage/file_manager.py', 'w') as f:
        f.write(storage_content)
    print("✅ Storage setup completed")

def create_simple_app():
    """Create working Flask app"""
    create_env_file()
    setup_storage()
    
    # Import after setup
    from config.database import DatabaseConfig, db
    from models import User, Student, UserRole, SectionEnum, StudyTypeEnum, AcademicStatusEnum
    
    # Create app
    app = Flask(__name__)
    app.config.from_object(DatabaseConfig)
    DatabaseConfig.init_app(app)
    
    with app.app_context():
        try:
            print("🔍 Testing database connection...")
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            print("✅ Database connection successful")
            
            print("📋 Creating database tables...")
            db.create_all()
            print("✅ All tables created")
            
            print("📊 Creating sample data...")
            # Create admin user
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@university.edu',
                    full_name='مدير النظام',
                    role=UserRole.ADMIN,
                    is_active=True
                )
                admin.set_password('Admin123!')
                admin.save()
                print("✅ Admin user created: admin / Admin123!")
            
            # Create sample student
            student_user = User.query.filter_by(username='student1').first()
            if not student_user:
                student_user = User(
                    username='student1',
                    email='student1@uni.edu',
                    full_name='أحمد محمد علي',
                    role=UserRole.STUDENT,
                    is_active=True
                )
                student_user.set_password('Student123!')
                student_user.save()
                
                student = Student(
                    user_id=student_user.id,
                    university_id='CS2021001',
                    section=SectionEnum.A,
                    study_year=3,
                    study_type=StudyTypeEnum.MORNING,
                    academic_status=AcademicStatusEnum.ACTIVE
                )
                student.set_secret_code('ABC123')
                student.save()
                print("✅ Sample student created: CS2021001")
            
            # Test Redis
            try:
                from config.database import redis_client
                redis_client.ping()
                print("✅ Redis connection successful")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}")
            
            # Final validation
            users_count = User.query.count()
            students_count = Student.query.count()
            
            print("")
            print("🎉 LEVEL 1 SETUP COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print(f"📊 Database Statistics:")
            print(f"   Users: {users_count}")
            print(f"   Students: {students_count}")
            print(f"   Tables: All created successfully")
            print("")
            print("🔑 Login Information:")
            print("   Admin: admin / Admin123!")
            print("   Student: student1 / Student123!")
            print("   Student ID: CS2021001 / ABC123")
            print("")
            print("✅ Ready to proceed to Level 2: Security & Authentication")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

def main():
    """Main setup function"""
    print("🏗️ Starting Level 1: Database Foundation Setup")
    print("🔧 Complete Working Solution")
    print("=" * 60)
    
    try:
        success = create_simple_app()
        
        if success:
            print("\n🎯 SETUP COMPLETED SUCCESSFULLY!")
            print("🚀 You can now start the application with: python app.py")
        else:
            print("\n❌ SETUP FAILED")
            print("Please check the error messages above")
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
