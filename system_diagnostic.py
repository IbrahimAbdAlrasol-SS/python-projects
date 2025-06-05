#!/usr/bin/env python3
"""
🔍 System Diagnostic Tool - أداة تشخيص النظام
Quick diagnostic and validation for Level 3 implementation
تشخيص سريع والتحقق من تطبيق المستوى الثالث
"""

import sys
import os
import subprocess
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

class Colors:
    """Console colors for better output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class SystemDiagnostic:
    """System diagnostic and validation tool"""
    
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warnings': 0,
            'errors': []
        }
    
    def print_header(self, title: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}🔍 {title}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    
    def print_test(self, test_name: str, success: bool, details: str = ""):
        """Print test result"""
        self.results['total_tests'] += 1
        
        if success:
            self.results['passed_tests'] += 1
            icon = f"{Colors.GREEN}✅{Colors.END}"
            print(f"{icon} {test_name}")
            if details:
                print(f"   {Colors.CYAN}└─ {details}{Colors.END}")
        else:
            self.results['failed_tests'] += 1
            icon = f"{Colors.RED}❌{Colors.END}"
            print(f"{icon} {test_name}")
            if details:
                print(f"   {Colors.RED}└─ {details}{Colors.END}")
                self.results['errors'].append(f"{test_name}: {details}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        self.results['warnings'] += 1
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility"""
        version = sys.version_info
        required_version = (3, 8)
        
        if version >= required_version:
            self.print_test(
                f"Python Version: {version.major}.{version.minor}.{version.micro}",
                True,
                f"✅ Compatible (required: {required_version[0]}.{required_version[1]}+)"
            )
            return True
        else:
            self.print_test(
                f"Python Version: {version.major}.{version.minor}.{version.micro}",
                False,
                f"❌ Incompatible (required: {required_version[0]}.{required_version[1]}+)"
            )
            return False
    
    def check_required_modules(self) -> Dict[str, bool]:
        """Check if required Python modules are installed"""
        required_modules = [
            'flask', 'sqlalchemy', 'psycopg2', 'redis', 
            'bcrypt', 'jwt', 'bleach', 'email_validator'
        ]
        
        results = {}
        for module in required_modules:
            try:
                __import__(module)
                results[module] = True
                self.print_test(f"Module: {module}", True, "Installed")
            except ImportError:
                results[module] = False
                self.print_test(f"Module: {module}", False, "Not installed")
        
        return results
    
    def check_database_connection(self) -> bool:
        """Check PostgreSQL database connection"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host='localhost',
                database='smart_attendance',
                user='postgres',
                password='password'
            )
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            self.print_test("PostgreSQL Connection", True, f"Connected: {version[:50]}...")
            return True
        except Exception as e:
            self.print_test("PostgreSQL Connection", False, str(e))
            return False
    
    def check_redis_connection(self) -> bool:
        """Check Redis connection"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            info = r.info()
            
            self.print_test(
                "Redis Connection", 
                True, 
                f"Connected: Redis {info['redis_version']}"
            )
            return True
        except Exception as e:
            self.print_test("Redis Connection", False, str(e))
            return False
    
    def check_file_permissions(self) -> bool:
        """Check file and directory permissions"""
        paths_to_check = [
            'level3_app.py',
            'apis/',
            'models/',
            'config/',
            'utils/'
        ]
        
        all_good = True
        for path in paths_to_check:
            if os.path.exists(path):
                if os.access(path, os.R_OK):
                    self.print_test(f"File Access: {path}", True, "Readable")
                else:
                    self.print_test(f"File Access: {path}", False, "Not readable")
                    all_good = False
            else:
                self.print_test(f"File Exists: {path}", False, "Not found")
                all_good = False
        
        return all_good
    
    def start_application(self) -> subprocess.Popen:
        """Start the Flask application"""
        try:
            process = subprocess.Popen(
                [sys.executable, 'level3_app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for startup
            time.sleep(5)
            
            if process.poll() is None:  # Process is still running
                self.print_test("Application Startup", True, "Process started successfully")
                return process
            else:
                stdout, stderr = process.communicate()
                self.print_test("Application Startup", False, f"Process died: {stderr}")
                return None
        except Exception as e:
            self.print_test("Application Startup", False, str(e))
            return None
    
    def test_api_endpoint(self, endpoint: str, method: str = 'GET', 
                         data: Dict = None, headers: Dict = None) -> Tuple[bool, Dict]:
        """Test a single API endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                return False, {'error': f'Unsupported method: {method}'}
            
            if response.status_code < 400:
                try:
                    json_data = response.json()
                    return True, json_data
                except:
                    return True, {'raw_response': response.text}
            else:
                return False, {
                    'status_code': response.status_code,
                    'response': response.text
                }
                
        except requests.exceptions.ConnectionError:
            return False, {'error': 'Connection refused - server not running?'}
        except requests.exceptions.Timeout:
            return False, {'error': 'Request timeout'}
        except Exception as e:
            return False, {'error': str(e)}
    
    def test_core_endpoints(self) -> Dict[str, bool]:
        """Test core API endpoints"""
        endpoints = {
            'Root Endpoint': '/',
            'API Info': '/api/info',
            'Health Check': '/api/health',
            'Health Basic': '/api/health/basic'
        }
        
        results = {}
        for name, endpoint in endpoints.items():
            success, response = self.test_api_endpoint(endpoint)
            results[name] = success
            
            if success:
                # Check for expected response structure
                if isinstance(response, dict):
                    if 'success' in response or 'status' in response:
                        self.print_test(f"API: {name} ({endpoint})", True, "Valid response structure")
                    else:
                        self.print_test(f"API: {name} ({endpoint})", True, "Response received (non-standard)")
                        self.print_warning(f"Endpoint {endpoint} returned non-standard response")
                else:
                    self.print_test(f"API: {name} ({endpoint})", True, "Response received")
            else:
                error_msg = response.get('error', 'Unknown error')
                self.print_test(f"API: {name} ({endpoint})", False, error_msg)
        
        return results
    
    def test_authentication_flow(self) -> bool:
        """Test authentication endpoints"""
        # Test student login
        login_data = {
            "university_id": "CS2024001",
            "secret_code": "SEC001",
            "device_fingerprint": "diagnostic-test-001"
        }
        
        success, response = self.test_api_endpoint(
            '/api/auth/student-login', 
            'POST', 
            login_data
        )
        
        if success and isinstance(response, dict) and response.get('success'):
            access_token = response.get('data', {}).get('access_token')
            if access_token:
                self.print_test("Student Login", True, "Token received")
                
                # Test token validation
                headers = {'Authorization': f'Bearer {access_token}'}
                success2, response2 = self.test_api_endpoint(
                    '/api/auth/validate-token',
                    'GET',
                    headers=headers
                )
                
                if success2:
                    self.print_test("Token Validation", True, "Token is valid")
                    return True
                else:
                    self.print_test("Token Validation", False, "Token validation failed")
                    return False
            else:
                self.print_test("Student Login", False, "No token in response")
                return False
        else:
            error_msg = response.get('error', {}).get('message', 'Login failed')
            self.print_test("Student Login", False, error_msg)
            return False
    
    def generate_summary_report(self):
        """Generate final summary report"""
        self.print_header("📊 DIAGNOSTIC SUMMARY REPORT")
        
        total = self.results['total_tests']
        passed = self.results['passed_tests']
        failed = self.results['failed_tests']
        warnings = self.results['warnings']
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}🎯 Test Results:{Colors.END}")
        print(f"   Total Tests: {total}")
        print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
        print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
        print(f"   {Colors.YELLOW}⚠️  Warnings: {warnings}{Colors.END}")
        print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
        
        print(f"\n{Colors.BOLD}🏆 Overall Status:{Colors.END}")
        if success_rate >= 90:
            print(f"   {Colors.GREEN}🎉 EXCELLENT - Level 3 is ready for production!{Colors.END}")
        elif success_rate >= 75:
            print(f"   {Colors.YELLOW}👍 GOOD - Level 3 is mostly working, minor issues to fix{Colors.END}")
        elif success_rate >= 50:
            print(f"   {Colors.YELLOW}⚠️  PARTIAL - Level 3 has significant issues{Colors.END}")
        else:
            print(f"   {Colors.RED}❌ CRITICAL - Level 3 needs major fixes{Colors.END}")
        
        if self.results['errors']:
            print(f"\n{Colors.BOLD}{Colors.RED}🚨 Critical Errors to Fix:{Colors.END}")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        print(f"\n{Colors.BOLD}📋 Next Steps:{Colors.END}")
        if success_rate >= 90:
            print(f"   ✅ Proceed to Level 4: Business Logic & Advanced Features")
            print(f"   ✅ Run comprehensive Postman tests")
            print(f"   ✅ Begin performance optimization")
        elif success_rate >= 75:
            print(f"   🔧 Fix remaining issues")
            print(f"   🧪 Re-run diagnostics")
            print(f"   📝 Check logs for detailed error messages")
        else:
            print(f"   🚨 Review system requirements")
            print(f"   🔧 Fix critical infrastructure issues")
            print(f"   📞 Check database and Redis connectivity")
    
    def run_full_diagnostic(self):
        """Run complete system diagnostic"""
        print(f"{Colors.BOLD}{Colors.PURPLE}")
        print("🔍 Smart Attendance System - Level 3 Diagnostic Tool")
        print("=" * 60)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.END}")
        
        # 1. System Requirements
        self.print_header("🐍 Python Environment Check")
        self.check_python_version()
        
        # 2. Required Modules
        self.print_header("📦 Required Modules Check")
        self.check_required_modules()
        
        # 3. Infrastructure
        self.print_header("🏗️ Infrastructure Check")
        self.check_database_connection()
        self.check_redis_connection()
        
        # 4. File System
        self.print_header("📁 File System Check")
        self.check_file_permissions()
        
        # 5. Application Startup
        self.print_header("🚀 Application Startup Test")
        app_process = self.start_application()
        
        if app_process:
            try:
                # 6. Core APIs
                self.print_header("🔗 Core API Endpoints Test")
                self.test_core_endpoints()
                
                # 7. Authentication Flow
                self.print_header("🔐 Authentication Flow Test")
                self.test_authentication_flow()
                
            finally:
                # Stop the application
                if app_process and app_process.poll() is None:
                    app_process.terminate()
                    time.sleep(2)
                    if app_process.poll() is None:
                        app_process.kill()
                    self.print_test("Application Cleanup", True, "Process terminated")
        
        # 8. Generate Report
        self.generate_summary_report()

def main():
    """Main entry point"""
    diagnostic = SystemDiagnostic()
    
    try:
        diagnostic.run_full_diagnostic()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Diagnostic interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Diagnostic failed with error: {e}{Colors.END}")
    finally:
        print(f"\n{Colors.BOLD}🔍 Diagnostic completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")

if __name__ == '__main__':
    main()