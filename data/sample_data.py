"""
Sample Data Generator
إنشاء بيانات تجريبية للاختبار
"""

from datetime import datetime, date, time
from models import *
from config.database import db
import random
import string

class SampleDataGenerator:
    """Generate sample data for testing"""
    
    @staticmethod
    def create_admin_user():
        """Create default admin user"""
        try:
            admin_user = User(
                username='admin',
                email='admin@university.edu',
                full_name='مدير النظام',
                role=UserRole.ADMIN,
                is_active=True
            )
            admin_user.set_password('Admin123!')
            admin_user.save()
            
            print("✅ Admin user created: admin / Admin123!")
            return admin_user
            
        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")
            return None
    
    @classmethod
    def generate_all_sample_data(cls):
        """Generate all sample data"""
        print("🚀 Starting sample data generation...")
        
        try:
            # Clear existing data (optional)
            print("🗑️ Clearing existing data...")
            db.session.query(User).delete()
            db.session.commit()
            
            # Generate data
            print("1️⃣ Creating admin user...")
            admin = cls.create_admin_user()
            
            print("✅ Sample data generation completed!")
            print(f"📊 Generated: 1 admin user")
            
            return {
                'admin': admin
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to generate sample data: {e}")
            return None

def test_sample_data():
    """Test sample data functionality"""
    print("🧪 Testing sample data...")
    
    # Test basic queries
    users_count = User.query.count()
    
    print(f"📊 Data counts:")
    print(f"   Users: {users_count}")
    
    # Test sample user
    sample_user = User.query.first()
    if sample_user:
        print(f"👤 Sample user: {sample_user.username}")
        print(f"   Name: {sample_user.full_name}")
        print(f"   Role: {sample_user.role.value}")
    
    print("✅ Sample data testing completed!")
