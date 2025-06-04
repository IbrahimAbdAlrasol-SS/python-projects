import os
import sys
from flask import Flask, g
from datetime import datetime

def test_security_layer():
    """Test all security components"""
    print("🔐 Testing Security Layer - Level 2")
    print("=" * 60)

    # Create test app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['TESTING'] = True

    # Import after app creation
    from config.database import DatabaseConfig, db
    from models import User, Student, UserRole, SectionEnum, StudyTypeEnum

    # Initialize app
    app.config.from_object(DatabaseConfig)
    DatabaseConfig.init_app(app)

    with app.app_context():
        # Create tables if needed
        db.create_all()

        # ===== 1. TEST JWT MANAGER =====
        print("\n1️⃣ Testing JWT Manager...")
        
        from security import jwt_manager

            # Initialize JWT manager
        jwt_manager.init_app(app)

            # Create test user
        test_user = User.query.filter_by(username='test_jwt').first()
        if not test_user:
            test_user = User(
                username='test_jwt',
                email='jwt@test.com',
                full_name='JWT Test User',
                role=UserRole.STUDENT,
                is_active=True
                )
            test_user.set_password('Test@123')
            test_user.save()

            # Generate tokens
            tokens = jwt_manager.generate_tokens(
                test_user,
                device_fingerprint='test-device-123'
            )

            print(f"✅ Access token generated: {tokens['access_token'][:50]}...")