"""
Database Testing Module
اختبار قاعدة البيانات والنماذج
"""

import unittest
from datetime import datetime, date, time
from config.database import db, DatabaseConfig
from models import *
from flask import Flask

class DatabaseTestCase(unittest.TestCase):
    """Base test case for database tests"""
    
    def setUp(self):
        """Set up test database"""
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['TESTING'] = True
        
        DatabaseConfig.init_app(self.app)
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up test database"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

class UserModelTest(DatabaseTestCase):
    """Test User model"""
    
    def test_user_creation(self):
        """Test creating a user"""
        with self.app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                full_name='Test User',
                role=UserRole.STUDENT
            )
            user.set_password('password123')
            user.save()
            
            # Verify user was created
            saved_user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(saved_user)
            self.assertEqual(saved_user.email, 'test@example.com')
            self.assertTrue(saved_user.check_password('password123'))
            self.assertFalse(saved_user.check_password('wrongpassword'))

def run_database_tests():
    """Run all database tests"""
    print("🧪 Running database tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UserModelTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print results
    if result.wasSuccessful():
        print("✅ All database tests passed!")
        return True
    else:
        print(f"❌ {len(result.failures)} tests failed, {len(result.errors)} errors")
        return False
