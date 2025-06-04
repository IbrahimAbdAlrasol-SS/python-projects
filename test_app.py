"""
Simple Test Application
تطبيق اختبار بسيط للتحقق من النظام
"""

from flask import Flask, jsonify
import os

def create_test_app():
    """Create simple test app"""
    
    # Ensure .env exists
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
    
    try:
        # Import after env setup
        from config.database import DatabaseConfig, db
        from models import User, UserRole
        
        app = Flask(__name__)
        app.config.from_object(DatabaseConfig)
        DatabaseConfig.init_app(app)
        
        @app.route('/')
        def index():
            return "Smart Attendance System - Level 1: Database Foundation"
        
        @app.route('/test')
        def test():
            """Test all components"""
            results = {}
            
            try:
                # Test database
                db.session.execute('SELECT 1')
                results['database'] = 'connected'
                
                # Test tables
                db.create_all()
                results['tables'] = 'created'
                
                # Test user creation
                admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
                if admin_count == 0:
                    admin = User(
                        username='admin',
                        email='admin@test.local',
                        full_name='Test Admin',
                        role=UserRole.ADMIN,
                        is_active=True
                    )
                    admin.set_password('Admin123!')
                    admin.save()
                    results['admin'] = 'created'
                else:
                    results['admin'] = 'exists'
                
                # Count users
                user_count = User.query.count()
                results['user_count'] = user_count
                results['status'] = 'success'
                
            except Exception as e:
                results['error'] = str(e)
                results['status'] = 'failed'
            
            return jsonify(results)
        
        @app.route('/health')
        def health():
            return jsonify({
                'status': 'healthy',
                'database': 'sqlite',
                'storage': 'ready'
            })
        
        return app
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return None

if __name__ == '__main__':
    print("🧪 Starting Test Application...")
    
    app = create_test_app()
    
    if app:
        print("✅ Test app created successfully")
        print("📍 Available endpoints:")
        print("   http://localhost:5000/ - Main page")
        print("   http://localhost:5000/test - System test")
        print("   http://localhost:5000/health - Health check")
        print("")
        print("🚀 Starting server...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Failed to create test app")