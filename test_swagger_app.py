#!/usr/bin/env python3
"""
🧪 Test Swagger Application - تطبيق اختبار Swagger
Simple app to test if Swagger documentation works
"""

import os
import sys
from datetime import datetime
from flask import Flask, jsonify

def create_swagger_test_app():
    """Create simple Flask app with working Swagger"""
    
    print("🧪 Creating Swagger Test Application...")
    print("=" * 50)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Basic configuration
    app.config.update({
        'SECRET_KEY': 'test-swagger-key',
        'DEBUG': True,
        'TESTING': True
    })
    
    print("✅ Flask app created")
    
    # Try to setup Swagger
    try:
        from swagger_fixed import setup_simple_swagger, setup_swagger_error_handlers
        
        print("📚 Setting up Swagger documentation...")
        api = setup_simple_swagger(app)
        
        if api:
            setup_swagger_error_handlers(api)
            print("✅ Swagger setup successful!")
        else:
            print("❌ Swagger setup failed!")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 Please install: pip install flask-restx")
        
        # Create manual Swagger route as fallback
        @app.route('/docs/')
        def swagger_fallback():
            return jsonify({
                'error': 'Flask-RESTX not installed',
                'message': 'Please install flask-restx to see Swagger documentation',
                'install_command': 'pip install flask-restx',
                'alternative': 'Use /api/info for API information'
            })
    
    # Basic routes for testing
    @app.route('/')
    def index():
        return jsonify({
            'success': True,
            'message': 'Swagger Test Application',
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'service': 'Smart Attendance System API - Swagger Test',
                'version': '1.0.0',
                'status': 'testing',
                'swagger_url': '/docs/',
                'api_info': '/api/info',
                'health_check': '/api/health',
                'test_endpoint': '/api/test/swagger-working'
            }
        })
    
    @app.route('/api/info')
    def api_info():
        return jsonify({
            'success': True,
            'data': {
                'api_name': 'Smart Attendance System API',
                'version': '1.0.0',
                'total_endpoints': 20,
                'documentation': {
                    'swagger_ui': '/docs/',
                    'description': 'Interactive API documentation',
                    'status': 'available' if 'flask_restx' in sys.modules else 'unavailable'
                },
                'test_endpoints': {
                    'health': '/api/health',
                    'swagger_test': '/api/test/swagger-working'
                },
                'endpoint_groups': {
                    'authentication': 3,
                    'pre_sync': 4,
                    'admin_management': 6,
                    'core_operations': 4,
                    'reports': 3
                }
            }
        })
    
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'flask': 'running',
                'swagger': 'available' if 'flask_restx' in sys.modules else 'unavailable'
            },
            'swagger_info': {
                'documentation_url': '/docs/',
                'flask_restx_installed': 'flask_restx' in sys.modules,
                'recommendation': 'Install flask-restx for full Swagger support' if 'flask_restx' not in sys.modules else 'Swagger ready!'
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'الصفحة غير موجودة',
                'available_endpoints': [
                    '/',
                    '/api/info', 
                    '/api/health',
                    '/docs/ (Swagger UI)'
                ]
            }
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'خطأ في الخادم'
            }
        }), 500
    
    print("=" * 50)
    print("🎉 Swagger Test App Ready!")
    
    return app

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking Dependencies...")
    
    required_packages = {
        'flask': 'Flask',
        'flask_restx': 'Flask-RESTX (for Swagger)',
        'werkzeug': 'Werkzeug'
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {description}: Installed")
        except ImportError:
            print(f"❌ {description}: Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Install missing packages:")
        for package in missing_packages:
            if package == 'flask_restx':
                print(f"   pip install flask-restx")
            else:
                print(f"   pip install {package}")
        print()
    
    return len(missing_packages) == 0

def main():
    """Main function"""
    print("🧪 SWAGGER TEST APPLICATION")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("⚠️ Some dependencies are missing, but app will still run with limited features")
        print()
    
    try:
        # Create and run app
        app = create_swagger_test_app()
        
        print("\n🌐 Server Starting...")
        print("=" * 50)
        print("📍 Main URL: http://localhost:5001")
        print("📚 Swagger UI: http://localhost:5001/docs/")
        print("ℹ️ API Info: http://localhost:5001/api/info")
        print("🏥 Health Check: http://localhost:5001/api/health")
        print("")
        print("🔍 Swagger Troubleshooting:")
        print("   1. Check if flask-restx is installed")
        print("   2. Visit /docs/ (with trailing slash)")
        print("   3. Check browser console for errors") 
        print("   4. Try /api/info for API information")
        print("")
        print("⚡ Press Ctrl+C to stop")
        print("=" * 50)
        
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n👋 Test application stopped")
    except Exception as e:
        print(f"\n❌ Application failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure port 5001 is not in use")
        print("   2. Install flask-restx: pip install flask-restx")
        print("   3. Check Python version (3.8+ recommended)")

if __name__ == '__main__':
    main()