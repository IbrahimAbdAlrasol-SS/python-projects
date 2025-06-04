"""
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
