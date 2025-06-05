#!/usr/bin/env python3
"""
🧪 Complete API Testing Script - اختبار شامل لجميع الـ APIs
Test all 20 API endpoints automatically
"""

import requests
import json
import time
from datetime import datetime
import sys

class APITester:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.access_token = None
        self.teacher_token = None
        self.student_id = None
        self.teacher_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, response_time, status_code, error=None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'success': success,
            'response_time': response_time,
            'status_code': status_code,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({response_time:.2f}s)")
        if error:
            print(f"   Error: {error}")
    
    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with timing"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.access_token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        if data and 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        
        try:
            start_time = time.time()
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            response_time = time.time() - start_time
            
            return response, response_time
            
        except requests.exceptions.ConnectionError:
            return None, 0
        except requests.exceptions.Timeout:
            return None, 10
        except Exception as e:
            return None, 0
    
    def test_system_info(self):
        """Test basic system endpoints"""
        print("\n🏠 Testing System Info Endpoints...")
        
        # Test root endpoint
        response, response_time = self.make_request('GET', '/')
        if response and response.status_code == 200:
            self.log_test("Root endpoint", True, response_time, response.status_code)
        else:
            self.log_test("Root endpoint", False, response_time, 
                         response.status_code if response else 0, 
                         "Connection failed" if not response else "Unexpected status")
        
        # Test API info
        response, response_time = self.make_request('GET', '/api/info')
        if response and response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('total_endpoints') == 20:
                self.log_test("API info endpoint", True, response_time, response.status_code)
            else:
                self.log_test("API info endpoint", False, response_time, response.status_code, 
                             "Incorrect endpoint count")
        else:
            self.log_test("API info endpoint", False, response_time, 
                         response.status_code if response else 0)
        
        # Test health check
        response, response_time = self.make_request('GET', '/api/health')
        if response and response.status_code in [200, 503]:
            self.log_test("Health check endpoint", True, response_time, response.status_code)
        else:
            self.log_test("Health check endpoint", False, response_time, 
                         response.status_code if response else 0)
    
    def test_authentication_apis(self):
        """Test authentication endpoints (3 APIs)"""
        print("\n🔐 Testing Authentication APIs...")
        
        # Test student login
        login_data = {
            "university_id": "CS2024001",
            "secret_code": "SEC001",
            "device_fingerprint": "test-device-001"
        }
        
        response, response_time = self.make_request('POST', '/api/auth/student-login', login_data)
        if response and response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('access_token'):
                self.access_token = data['data']['access_token']
                self.student_id = data['data'].get('user', {}).get('id')
                self.log_test("Student login", True, response_time, response.status_code)
            else:
                self.log_test("Student login", False, response_time, response.status_code, 
                             "No access token returned")
        else:
            self.log_test("Student login", False, response_time, 
                         response.status_code if response else 0)
        
        # Test teacher login
        teacher_login_data = {
            "username": "teacher1",
            "password": "Teacher123!",
            "device_fingerprint": "teacher-device-001"
        }
        
        response, response_time = self.make_request('POST', '/api/auth/teacher-login', teacher_login_data)
        if response and response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('access_token'):
                self.teacher_token = data['data']['access_token']
                self.teacher_id = data['data'].get('user', {}).get('id')
                self.log_test("Teacher login", True, response_time, response.status_code)
            else:
                self.log_test("Teacher login", False, response_time, response.status_code, 
                             "No access token returned")
        else:
            self.log_test("Teacher login", False, response_time, 
                         response.status_code if response else 0)
        
        # Test token refresh
        if self.access_token:
            response, response_time = self.make_request('POST', '/api/auth/refresh-token')
            if response and response.status_code == 200:
                self.log_test("Token refresh", True, response_time, response.status_code)
            else:
                self.log_test("Token refresh", False, response_time, 
                             response.status_code if response else 0)
        else:
            self.log_test("Token refresh", False, 0, 0, "No access token available")
    
    def test_pre_sync_apis(self):
        """Test pre-sync endpoints (4 APIs)"""
        print("\n🔄 Testing Pre-Sync APIs...")
        
        if not self.access_token:
            print("❌ Skipping pre-sync tests - no access token")
            return
        
        # Test student sync data
        response, response_time = self.make_request('GET', '/api/student/sync-data')
        if response and response.status_code == 200:
            data = response.json()
            if all(key in data.get('data', {}) for key in ['student_profile', 'subjects', 'schedules', 'rooms']):
                self.log_test("Student sync data", True, response_time, response.status_code)
            else:
                self.log_test("Student sync data", False, response_time, response.status_code, 
                             "Missing required data keys")
        else:
            self.log_test("Student sync data", False, response_time, 
                         response.status_code if response else 0)
        
        # Test incremental sync
        response, response_time = self.make_request('GET', 
            f'/api/student/incremental-sync?last_sync={datetime.now().isoformat()}&data_version=v1.0.0')
        if response and response.status_code == 200:
            self.log_test("Incremental sync", True, response_time, response.status_code)
        else:
            self.log_test("Incremental sync", False, response_time, 
                         response.status_code if response else 0)
        
        # Test student schedule
        response, response_time = self.make_request('GET', 
            '/api/student/schedule?academic_year=2023-2024&semester=first')
        if response and response.status_code == 200:
            self.log_test("Student schedule", True, response_time, response.status_code)
        else:
            self.log_test("Student schedule", False, response_time, 
                         response.status_code if response else 0)
        
        # Test rooms bulk download
        response, response_time = self.make_request('GET', '/api/rooms/bulk-download')
        if response and response.status_code == 200:
            self.log_test("Rooms bulk download", True, response_time, response.status_code)
        else:
            self.log_test("Rooms bulk download", False, response_time, 
                         response.status_code if response else 0)
    
    def test_admin_apis(self):
        """Test admin management endpoints (6 APIs)"""
        print("\n👑 Testing Admin Management APIs...")
        
        if not self.teacher_token:
            print("❌ Skipping admin tests - no teacher token")
            return
        
        headers = {'Authorization': f'Bearer {self.teacher_token}'}
        
        # Test get students list
        response, response_time = self.make_request('GET', '/api/admin/students?page=1&limit=5', 
                                                   headers=headers)
        if response and response.status_code == 200:
            self.log_test("Admin get students", True, response_time, response.status_code)
        else:
            self.log_test("Admin get students", False, response_time, 
                         response.status_code if response else 0)
        
        # Test bulk create students
        bulk_students_data = {
            "students": [
                {
                    "full_name": "Test Student API",
                    "email": "testapi@university.edu",
                    "section": "A",
                    "study_year": 1,
                    "study_type": "morning"
                }
            ],
            "options": {
                "auto_generate_codes": True,
                "skip_duplicates": True
            }
        }
        
        response, response_time = self.make_request('POST', '/api/admin/students/bulk-create', 
                                                   bulk_students_data, headers)
        if response and response.status_code in [200, 201]:
            self.log_test("Admin bulk create students", True, response_time, response.status_code)
        else:
            self.log_test("Admin bulk create students", False, response_time, 
                         response.status_code if response else 0)
        
        # Test create room
        room_data = {
            "name": "TESTAPI",
            "building": "Test Building API",
            "floor": 1,
            "room_type": "classroom",
            "capacity": 25,
            "center_latitude": 33.3152,
            "center_longitude": 44.3661,
            "ground_reference_altitude": 50.0,
            "floor_altitude": 53.0,
            "ceiling_height": 3.0
        }
        
        response, response_time = self.make_request('POST', '/api/admin/rooms', room_data, headers)
        if response and response.status_code in [200, 201]:
            created_room_id = response.json().get('data', {}).get('id')
            self.log_test("Admin create room", True, response_time, response.status_code)
            
            # Test update room if creation succeeded
            if created_room_id:
                update_data = {"capacity": 30, "wifi_ssid": "Updated_SSID"}
                response, response_time = self.make_request('PUT', f'/api/admin/rooms/{created_room_id}', 
                                                           update_data, headers)
                if response and response.status_code == 200:
                    self.log_test("Admin update room", True, response_time, response.status_code)
                else:
                    self.log_test("Admin update room", False, response_time, 
                                 response.status_code if response else 0)
            else:
                self.log_test("Admin update room", False, 0, 0, "No room ID from creation")
        else:
            self.log_test("Admin create room", False, response_time, 
                         response.status_code if response else 0)
            self.log_test("Admin update room", False, 0, 0, "Room creation failed")
        
        # Test bulk create schedules
        schedules_data = {
            "schedules": [
                {
                    "subject_id": 1,
                    "teacher_id": 1,
                    "room_id": 1,
                    "section": "A",
                    "day_of_week": 1,
                    "start_time": "08:00",
                    "end_time": "10:00"
                }
            ],
            "options": {
                "academic_year": "2023-2024",
                "semester": "first",
                "check_conflicts": False
            }
        }
        
        response, response_time = self.make_request('POST', '/api/admin/schedules/bulk-create', 
                                                   schedules_data, headers)
        if response and response.status_code in [200, 201]:
            self.log_test("Admin bulk create schedules", True, response_time, response.status_code)
        else:
            self.log_test("Admin bulk create schedules", False, response_time, 
                         response.status_code if response else 0)
        
        # Test system health
        response, response_time = self.make_request('GET', '/api/admin/system/health', headers=headers)
        if response and response.status_code == 200:
            self.log_test("Admin system health", True, response_time, response.status_code)
        else:
            self.log_test("Admin system health", False, response_time, 
                         response.status_code if response else 0)
    
    def test_attendance_apis(self):
        """Test attendance/core operations endpoints (4 APIs)"""
        print("\n⚡ Testing Attendance APIs...")
        
        if not self.teacher_token:
            print("❌ Skipping attendance tests - no teacher token")
            return
        
        headers = {'Authorization': f'Bearer {self.teacher_token}'}
        
        # Test generate QR code
        qr_data = {
            "duration_minutes": 10,
            "max_usage_count": 50,
            "allow_multiple_scans": True
        }
        
        response, response_time = self.make_request('POST', '/api/attendance/generate-qr/1', 
                                                   qr_data, headers)
        qr_session_id = None
        if response and response.status_code in [200, 201]:
            qr_session_id = response.json().get('data', {}).get('qr_session', {}).get('session_id')
            self.log_test("Generate QR code", True, response_time, response.status_code)
        else:
            self.log_test("Generate QR code", False, response_time, 
                         response.status_code if response else 0)
        
        # Test batch upload attendance
        if self.access_token and qr_session_id:
            upload_data = {
                "attendance_records": [
                    {
                        "local_id": "test_001",
                        "lecture_id": 1,
                        "qr_session_id": qr_session_id,
                        "recorded_latitude": 33.3152,
                        "recorded_longitude": 44.3661,
                        "recorded_altitude": 53.0,
                        "check_in_time": datetime.now().isoformat(),
                        "location_verified": True,
                        "qr_verified": True,
                        "face_verified": True
                    }
                ],
                "batch_options": {
                    "validation_level": "normal"
                }
            }
            
            student_headers = {'Authorization': f'Bearer {self.access_token}'}
            response, response_time = self.make_request('POST', '/api/attendance/batch-upload', 
                                                       upload_data, student_headers)
            if response and response.status_code == 200:
                self.log_test("Batch upload attendance", True, response_time, response.status_code)
            else:
                self.log_test("Batch upload attendance", False, response_time, 
                             response.status_code if response else 0)
        else:
            self.log_test("Batch upload attendance", False, 0, 0, "Missing prerequisites")
        
        # Test resolve conflicts
        conflicts_data = {
            "conflicts": [
                {
                    "student_id": self.student_id or 1,
                    "lecture_id": 1,
                    "resolution_strategy": "merge",
                    "local_record": {
                        "recorded_latitude": 33.3152,
                        "recorded_longitude": 44.3661,
                        "check_in_time": datetime.now().isoformat(),
                        "location_verified": True,
                        "qr_verified": True,
                        "face_verified": True
                    }
                }
            ]
        }
        
        if self.access_token:
            student_headers = {'Authorization': f'Bearer {self.access_token}'}
            response, response_time = self.make_request('POST', '/api/attendance/resolve-conflicts', 
                                                       conflicts_data, student_headers)
            if response and response.status_code == 200:
                self.log_test("Resolve conflicts", True, response_time, response.status_code)
            else:
                self.log_test("Resolve conflicts", False, response_time, 
                             response.status_code if response else 0)
        else:
            self.log_test("Resolve conflicts", False, 0, 0, "No student token")
        
        # Test sync status
        if self.access_token:
            student_headers = {'Authorization': f'Bearer {self.access_token}'}
            response, response_time = self.make_request('GET', '/api/attendance/sync-status', 
                                                       headers=student_headers)
            if response and response.status_code == 200:
                self.log_test("Sync status", True, response_time, response.status_code)
            else:
                self.log_test("Sync status", False, response_time, 
                             response.status_code if response else 0)
        else:
            self.log_test("Sync status", False, 0, 0, "No student token")
    
    def test_reports_apis(self):
        """Test reports endpoints (3 APIs)"""
        print("\n📊 Testing Reports APIs...")
        
        if not self.teacher_token:
            print("❌ Skipping reports tests - no teacher token")
            return
        
        headers = {'Authorization': f'Bearer {self.teacher_token}'}
        
        # Test attendance summary report
        response, response_time = self.make_request('GET', 
            '/api/reports/attendance/summary?start_date=2023-01-01&end_date=2023-12-31', 
            headers=headers)
        if response and response.status_code == 200:
            self.log_test("Attendance summary report", True, response_time, response.status_code)
        else:
            self.log_test("Attendance summary report", False, response_time, 
                         response.status_code if response else 0)
        
        # Test student detailed report
        student_id = self.student_id or 1
        response, response_time = self.make_request('GET', 
            f'/api/reports/student/{student_id}?start_date=2023-01-01&end_date=2023-12-31', 
            headers=headers)
        if response and response.status_code == 200:
            self.log_test("Student detailed report", True, response_time, response.status_code)
        else:
            self.log_test("Student detailed report", False, response_time, 
                         response.status_code if response else 0)
        
        # Test export report
        export_data = {
            "report_type": "attendance_summary",
            "export_format": "json",
            "filters": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            }
        }
        
        response, response_time = self.make_request('POST', '/api/reports/export', 
                                                   export_data, headers)
        if response and response.status_code == 200:
            self.log_test("Export report", True, response_time, response.status_code)
        else:
            self.log_test("Export report", False, response_time, 
                         response.status_code if response else 0)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"🎯 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test_name']}: {result['error'] or f'Status {result['status_code']}'}")
        
        # Average response time
        response_times = [r['response_time'] for r in self.test_results if r['response_time'] > 0]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            print(f"\n⏱️ Average Response Time: {avg_response_time:.2f}s")
        
        # Test by category
        categories = {
            'System Info': [r for r in self.test_results if 'endpoint' in r['test_name']],
            'Authentication': [r for r in self.test_results if 'login' in r['test_name'] or 'refresh' in r['test_name']],
            'Pre-Sync': [r for r in self.test_results if any(x in r['test_name'] for x in ['sync', 'schedule', 'rooms'])],
            'Admin': [r for r in self.test_results if 'Admin' in r['test_name']],
            'Attendance': [r for r in self.test_results if any(x in r['test_name'] for x in ['QR', 'upload', 'conflicts', 'Sync status'])],
            'Reports': [r for r in self.test_results if 'report' in r['test_name']]
        }
        
        print(f"\n📊 Results by Category:")
        for category, tests in categories.items():
            if tests:
                passed = sum(1 for t in tests if t['success'])
                total = len(tests)
                print(f"   {category}: {passed}/{total} ({'✅' if passed == total else '⚠️'})")
        
        print("=" * 80)
        
        return passed_tests == total_tests

def main():
    """Main testing function"""
    print("🧪 Smart Attendance System - Complete API Testing")
    print("=" * 80)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            print("Please start the server with: python run_level3.py")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:5000")
        print("Please start the server with: python run_level3.py")
        sys.exit(1)
    
    print("✅ Server is running, starting comprehensive tests...")
    
    # Initialize tester
    tester = APITester()
    
    # Run all test suites
    tester.test_system_info()
    tester.test_authentication_apis()
    tester.test_pre_sync_apis()
    tester.test_admin_apis()
    tester.test_attendance_apis()
    tester.test_reports_apis()
    
    # Generate final report
    success = tester.generate_report()
    
    if success:
        print("🎉 All tests passed! Level 3 APIs are working correctly.")
        sys.exit(0)
    else:
        print("⚠️ Some tests failed. Check the report above for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()