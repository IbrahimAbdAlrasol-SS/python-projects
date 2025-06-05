#!/usr/bin/env python3
"""
🚀 Smart Attendance System - Simple Runner (No Redis Required)
تشغيل بسيط للنظام بدون Redis
"""

import os
import sys
from datetime import datetime
from flask import Flask, jsonify

def create_simple_app():
    """Create Flask app that works without Redis"""
    
    print("🚀 Starting Smart Attendance System (Simple Mode)")
    print("=" * 60)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Basic configuration
    app.config.update({
        'SECRET_KEY': 'dev-secret-key-simple',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///attendance.db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': True
    })
    
    print("✅ Flask app configured")
    
    # Initialize database (simple)
    try:
        from flask_sqlalchemy import SQLAlchemy
        db = SQLAlchemy(app)
        
        # Create basic User model
        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(50), unique=True, nullable=False)
            email = db.Column(db.String(100), unique=True, nullable=False)
            password_hash = db.Column(db.String(255), nullable=False)
            full_name = db.Column(db.String(255), nullable=False)
            role = db.Column(db.String(20), nullable=False, default='student')
            is_active = db.Column(db.Boolean, default=True)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            
            def to_dict(self):
                return {
                    'id': self.id,
                    'username': self.username,
                    'email': self.email,
                    'full_name': self.full_name,
                    'role': self.role,
                    'is_active': self.is_active
                }
        
        with app.app_context():
            db.create_all()
            
            # Create sample user if none exist
            if User.query.count() == 0:
                from werkzeug.security import generate_password_hash
                
                admin = User(
                    username='admin',
                    email='admin@test.com',
                    password_hash=generate_password_hash('admin123'),
                    full_name='Test Administrator',
                    role='admin'
                )
                
                student = User(
                    username='CS2024001',
                    email='student@test.com',
                    password_hash=generate_password_hash('SEC001'),
                    full_name='Test Student',
                    role='student'
                )
                
                db.session.add(admin)
                db.session.add(student)
                db.session.commit()
                print("✅ Sample users created")
        
        print("✅ Database initialized")
        
    except Exception as e:
        print(f"⚠️ Database error: {e}")
    
    # Setup basic routes
    @app.route('/')
    def index():
        return jsonify({
            'success': True,
            'message': 'Smart Attendance System API - Simple Mode',
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'service': 'Smart Attendance System API',
                'version': '1.0.0',
                'mode': 'simple',
                'status': 'operational',
                'endpoints': {
                    'health': '/health',
                    'info': '/info',
                    'users': '/users',
                    'test_login': '/test-login'
                }
            }
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': 'healthy',
                'storage': 'healthy'
            }
        })
    
    @app.route('/info')
    def info():
        return jsonify({
            'success': True,
            'data': {
                'api_version': '1.0.0',
                'mode': 'simple',
                'database': 'SQLite',
                'redis': 'disabled',
                'total_endpoints': 4,
                'test_credentials': {
                    'admin': 'admin / admin123',
                    'student': 'CS2024001 / SEC001'
                }
            }
        })
    
    @app.route('/users')
    def users():
        try:
            users = User.query.all()
            return jsonify({
                'success': True,
                'data': {
                    'users': [user.to_dict() for user in users],
                    'total': len(users)
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
    
    @app.route('/test-login', methods=['GET'])
    def test_login():
        return jsonify({
            'success': True,
            'message': 'Login test endpoint',
            'instructions': {
                'method': 'POST',
                'url': '/test-login',
                'body': {
                    'username': 'admin or CS2024001',
                    'password': 'admin123 or SEC001'
                }
            }
        })
    
    @app.route('/test-login', methods=['POST'])
    def do_test_login():
        try:
            from flask import request
            from werkzeug.security import check_password_hash
            
            data = request.get_json() or {}
            username = data.get('username', '')
            password = data.get('password', '')
            
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': user.to_dict()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid credentials'
                }), 401
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return app

def main():
    """Main function"""
    try:
        app = create_simple_app()
        
        print("\n🌐 Server Information:")
        print("=" * 60)
        print("📍 URL: http://localhost:5000")
        print("🏥 Health: http://localhost:5000/health")
        print("ℹ️ Info: http://localhost:5000/info")
        print("👥 Users: http://localhost:5000/users")
        print("")
        print("🧪 Test Credentials:")
        print("   Admin: admin / admin123")
        print("   Student: CS2024001 / SEC001")
        print("")
        print("⚡ Press Ctrl+C to stop")
        print("=" * 60)
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    main()