#!/usr/bin/env python3
"""
🔧 Fix Swagger Issues - حل مشاكل Swagger الشائعة
Comprehensive troubleshooting and fixing for Swagger UI
"""

import sys
import subprocess
import importlib
import traceback

class SwaggerTroubleshooter:
    """مشخص ومصلح مشاكل Swagger"""
    
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
    
    def check_python_version(self):
        """Check Python version compatibility"""
        print("🐍 Checking Python Version...")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} (Compatible)")
            return True
        else:
            print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (Requires 3.8+)")
            self.issues_found.append("Python version too old")
            return False
    
    def check_package_installation(self):
        """Check if required packages are installed"""
        print("\n📦 Checking Package Installation...")
        
        required_packages = {
            'flask': 'Flask>=2.0.0',
            'flask_restx': 'flask-restx>=1.0.0',
            'werkzeug': 'Werkzeug>=2.0.0'
        }
        
        all_installed = True
        
        for package, version_info in required_packages.items():
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'unknown')
                print(f"   ✅ {package}: {version}")
            except ImportError:
                print(f"   ❌ {package}: Not installed ({version_info})")
                self.issues_found.append(f"Missing package: {package}")
                all_installed = False
        
        return all_installed
    
    def install_missing_packages(self):
        """Install missing packages"""
        print("\n📥 Installing Missing Packages...")
        
        commands = [
            "pip install --upgrade pip",
            "pip install flask>=2.0.0",
            "pip install flask-restx>=1.0.0", 
            "pip install werkzeug>=2.0.0",
            "pip install flask-cors>=4.0.0"
        ]
        
        for cmd in commands:
            try:
                print(f"   🔄 Running: {cmd}")
                result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    print(f"   ✅ Success")
                else:
                    print(f"   ❌ Failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"   ⏰ Timeout")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    def test_flask_restx_import(self):
        """Test if flask-restx can be imported correctly"""
        print("\n🧪 Testing Flask-RESTX Import...")
        
        try:
            from flask import Flask
            from flask_restx import Api, Resource, fields
            
            print("   ✅ Basic imports successful")
            
            # Test creating API object
            app = Flask(__name__)
            api = Api(app, doc='/test-docs/')
            
            print("   ✅ API object creation successful")
            
            # Test model creation
            test_model = api.model('TestModel', {
                'test_field': fields.String(description='Test field')
            })
            
            print("   ✅ Model creation successful")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Import test failed: {e}")
            traceback.print_exc()
            self.issues_found.append(f"Flask-RESTX import error: {e}")
            return False
    
    def check_port_availability(self, port=5001):
        """Check if port is available"""
        print(f"\n🔌 Checking Port {port} Availability...")
        
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                print(f"   ✅ Port {port} is available")
                return True
        except OSError:
            print(f"   ❌ Port {port} is in use")
            self.issues_found.append(f"Port {port} is occupied")
            return False
    
    def create_minimal_swagger_test(self):
        """Create minimal Swagger test application"""
        print("\n🧪 Creating Minimal Swagger Test...")
        
        test_code = '''
from flask import Flask, jsonify
from datetime import datetime

try:
    from flask_restx import Api, Resource, fields
    
    app = Flask(__name__)
    api = Api(app, 
              title='Test API',
              description='Minimal Swagger Test',
              doc='/docs/')
    
    test_model = api.model('TestResponse', {
        'success': fields.Boolean(description='Success status'),
        'message': fields.String(description='Response message'),
        'timestamp': fields.String(description='Response timestamp')
    })
    
    @api.route('/test')
    class TestEndpoint(Resource):
        @api.marshal_with(test_model)
        def get(self):
            """Test endpoint to verify Swagger is working"""
            return {
                'success': True,
                'message': 'Swagger is working perfectly!',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Swagger Test Server',
            'swagger_url': '/docs/',
            'test_endpoint': '/test'
        })
    
    if __name__ == '__main__':
        print("🚀 Starting Swagger Test Server...")
        print("📚 Swagger UI: http://localhost:5001/docs/")
        print("🧪 Test endpoint: http://localhost:5001/test")
        app.run(debug=True, port=5001)

except ImportError as e:
    print(f"❌ Flask-RESTX not available: {e}")
    print("📦 Install with: pip install flask-restx")
'''
        
        try:
            with open('swagger_test.py', 'w', encoding='utf-8') as f:
                f.write(test_code)
            print("   ✅ Created swagger_test.py")
            self.fixes_applied.append("Created minimal test file")
            return True
        except Exception as e:
            print(f"   ❌ Failed to create test file: {e}")
            return False
    
    def test_swagger_access(self):
        """Test accessing Swagger UI"""
        print("\n🌐 Testing Swagger UI Access...")
        
        try:
            import requests
            import threading
            import time
            from flask import Flask
            from flask_restx import Api
            
            # Create test app
            app = Flask(__name__)
            api = Api(app, doc='/docs/')
            
            @app.route('/health')
            def health():
                return {'status': 'ok'}
            
            # Start server in thread
            def run_server():
                app.run(port=5001, debug=False, use_reloader=False)
            
            server_thread = threading.Thread(target=run_server)
            server_thread.daemon = True
            server_thread.start()
            
            # Wait for server to start
            time.sleep(2)
            
            # Test access
            response = requests.get('http://localhost:5001/docs/', timeout=5)
            if response.status_code == 200:
                print("   ✅ Swagger UI accessible")
                return True
            else:
                print(f"   ❌ Swagger UI returned status {response.status_code}")
                return False
                
        except ImportError:
            print("   ⚠️ Requests module not available for testing")
            return None
        except Exception as e:
            print(f"   ❌ Access test failed: {e}")
            return False
    
    def provide_solutions(self):
        """Provide solutions for found issues"""
        print("\n🔧 SOLUTIONS FOR FOUND ISSUES:")
        print("=" * 50)
        
        if not self.issues_found:
            print("✅ No issues found! Swagger should be working.")
            return
        
        solutions = {
            'Python version too old': [
                "📥 Install Python 3.8 or higher",
                "🔗 Download from: https://python.org/downloads",
                "⚠️ Make sure to update PATH after installation"
            ],
            'Missing package': [
                "📦 Install packages with: pip install flask-restx flask-cors",
                "🔄 Upgrade pip first: pip install --upgrade pip",
                "🌐 Use alternative index if needed: pip install -i https://pypi.org/simple/ flask-restx"
            ],
            'Port': [
                "🔌 Stop other services using port 5001",
                "🔄 Or use different port: app.run(port=5001)",
                "🔍 Find process using port: netstat -ano | findstr :5001 (Windows) or lsof -i :5001 (Mac/Linux)"
            ],
            'Flask-RESTX import error': [
                "🧹 Uninstall and reinstall: pip uninstall flask-restx && pip install flask-restx",
                "🔄 Try different version: pip install flask-restx==1.1.0", 
                "🐍 Check virtual environment is activated"
            ]
        }
        
        for issue in self.issues_found:
            print(f"\n❌ Issue: {issue}")
            
            # Find matching solutions
            for key, solution_list in solutions.items():
                if key.lower() in issue.lower():
                    for solution in solution_list:
                        print(f"   {solution}")
                    break
            else:
                print("   🔍 Try general troubleshooting steps below")
        
        print(f"\n🔧 GENERAL TROUBLESHOOTING:")
        print("   1. 🐍 Ensure Python 3.8+ is installed")
        print("   2. 📦 Install/reinstall packages: pip install flask-restx")
        print("   3. 🔄 Restart your terminal/IDE")
        print("   4. 🧹 Clear Python cache: python -m pip cache purge")
        print("   5. 🌐 Test minimal example: python swagger_test.py")
        print("   6. 📚 Visit /docs/ URL (note the trailing slash)")
    
    def run_full_diagnosis(self):
        """Run complete diagnosis"""
        print("🔍 SWAGGER TROUBLESHOOTER")
        print("=" * 50)
        
        # Run all checks
        python_ok = self.check_python_version()
        packages_ok = self.check_package_installation()
        
        if not packages_ok:
            install_choice = input("\n📥 Install missing packages? (y/n): ").lower()
            if install_choice == 'y':
                self.install_missing_packages()
                print("\n🔄 Re-checking after installation...")
                packages_ok = self.check_package_installation()
        
        import_ok = self.test_flask_restx_import()
        port_ok = self.check_port_availability()
        
        # Create test file
        test_created = self.create_minimal_swagger_test()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 DIAGNOSIS SUMMARY:")
        print("=" * 50)
        
        checks = [
            ("Python Version", python_ok),
            ("Package Installation", packages_ok), 
            ("Flask-RESTX Import", import_ok),
            ("Port Availability", port_ok),
            ("Test File Created", test_created)
        ]
        
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")
        
        # Provide solutions if needed
        self.provide_solutions()
        
        # Final recommendations
        print(f"\n🎯 NEXT STEPS:")
        if all(result for _, result in checks):
            print("   ✅ All checks passed! Try running:")
            print("      python swagger_test.py")
            print("      then visit http://localhost:5001/docs/")
        else:
            print("   🔧 Fix the issues above, then try:")
            print("      python swagger_test.py")
        
        print("\n📚 Alternative URLs to try:")
        print("   • http://localhost:5001/docs/")
        print("   • http://localhost:5001/docs")  
        print("   • http://127.0.0.1:5001/docs/")

def main():
    """Main troubleshooting function"""
    troubleshooter = SwaggerTroubleshooter()
    
    try:
        troubleshooter.run_full_diagnosis()
    except KeyboardInterrupt:
        print("\n👋 Troubleshooting interrupted")
    except Exception as e:
        print(f"\n❌ Troubleshooter error: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    main()