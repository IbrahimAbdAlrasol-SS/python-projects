"""
🏥 Health Check API - نظام مراقبة صحة النظام
Implementation: Comprehensive system health monitoring
اليوم 1: تطبيق مراقبة شاملة لصحة النظام
"""

from flask import Blueprint, jsonify, current_app
from config.database import db
from datetime import datetime, timedelta
import psutil
import os
import logging

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api/health')

@health_bp.route('/', methods=['GET'])
def health_check():
    """
    GET /api/health
    Comprehensive system health check
    فحص شامل لصحة النظام
    """
    start_time = datetime.utcnow()
    
    health_status = {
        'status': 'healthy',
        'timestamp': start_time.isoformat(),
        'system_info': {},
        'services': {},
        'performance': {},
        'database': {},
        'storage': {},
        'dependencies': {}
    }
    
    try:
        # 1. System Information
        health_status['system_info'] = {
            'platform': os.name,
            'python_version': f"{psutil.PYTHON_VERSION[0]}.{psutil.PYTHON_VERSION[1]}.{psutil.PYTHON_VERSION[2]}",
            'uptime_seconds': psutil.boot_time(),
            'current_time': start_time.isoformat(),
            'timezone': 'UTC'
        }
        
        # 2. Performance Metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status['performance'] = {
            'cpu_usage_percent': cpu_percent,
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'usage_percent': memory.percent
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'usage_percent': round((disk.used / disk.total) * 100, 2)
            }
        }
        
        # Set performance warnings
        if cpu_percent > 80:
            health_status['status'] = 'degraded'
        if memory.percent > 85:
            health_status['status'] = 'degraded'
        if (disk.used / disk.total) * 100 > 90:
            health_status['status'] = 'degraded'
        
        # 3. Database Health Check
        db_start_time = datetime.utcnow()
        try:
            # Test basic database connection
            result = db.session.execute('SELECT 1 as test').fetchone()
            db_response_time = (datetime.utcnow() - db_start_time).total_seconds() * 1000
            
            if result and result[0] == 1:
                health_status['database']['connection'] = {
                    'status': 'healthy',
                    'response_time_ms': round(db_response_time, 2)
                }
            else:
                health_status['database']['connection'] = {
                    'status': 'unhealthy',
                    'error': 'Invalid test query result'
                }
                health_status['status'] = 'unhealthy'
            
            # Get database statistics
            from models import User, Student, Teacher, Subject, Room, Schedule, Lecture, AttendanceRecord
            
            try:
                db_stats = {
                    'total_users': User.query.count(),
                    'total_students': Student.query.count(),
                    'total_teachers': Teacher.query.count(),
                    'total_subjects': Subject.query.count(),
                    'total_rooms': Room.query.count(),
                    'total_schedules': Schedule.query.count(),
                    'total_lectures': Lecture.query.count(),
                    'total_attendance_records': AttendanceRecord.query.count()
                }
                
                health_status['database']['statistics'] = db_stats
                
                # Check for recent activity (last 24 hours)
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_activity = {
                    'recent_logins': User.query.filter(User.last_login >= yesterday).count(),
                    'recent_lectures': Lecture.query.filter(Lecture.created_at >= yesterday).count(),
                    'recent_attendance': AttendanceRecord.query.filter(AttendanceRecord.check_in_time >= yesterday).count()
                }
                
                health_status['database']['recent_activity'] = recent_activity
                
            except Exception as e:
                health_status['database']['statistics'] = {
                    'error': f'Failed to retrieve database statistics: {str(e)}'
                }
                
        except Exception as e:
            health_status['database']['connection'] = {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': (datetime.utcnow() - db_start_time).total_seconds() * 1000
            }
            health_status['status'] = 'unhealthy'
        
        # 4. Redis Health Check
        try:
            from config.database import redis_client
            redis_start_time = datetime.utcnow()
            
            # Test Redis connection
            redis_client.ping()
            redis_response_time = (datetime.utcnow() - redis_start_time).total_seconds() * 1000
            
            # Get Redis info
            redis_info = redis_client.info()
            
            health_status['services']['redis'] = {
                'status': 'healthy',
                'response_time_ms': round(redis_response_time, 2),
                'version': redis_info.get('redis_version', 'unknown'),
                'connected_clients': redis_info.get('connected_clients', 0),
                'used_memory_mb': round(redis_info.get('used_memory', 0) / (1024 * 1024), 2),
                'uptime_days': round(redis_info.get('uptime_in_seconds', 0) / 86400, 2)
            }
            
        except Exception as e:
            health_status['services']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
        
        # 5. File Storage Health Check
        storage_paths = [
            '/storage',
            '/storage/face_templates',
            '/storage/qr_codes',
            '/storage/reports',
            '/storage/uploads',
            '/storage/backups'
        ]
        
        storage_health = {}
        for path in storage_paths:
            try:
                if os.path.exists(path):
                    if os.access(path, os.W_OK):
                        # Calculate directory size
                        total_size = 0
                        for dirpath, dirnames, filenames in os.walk(path):
                            for filename in filenames:
                                filepath = os.path.join(dirpath, filename)
                                try:
                                    total_size += os.path.getsize(filepath)
                                except OSError:
                                    pass
                        
                        storage_health[path] = {
                            'status': 'healthy',
                            'writable': True,
                            'size_mb': round(total_size / (1024 * 1024), 2)
                        }
                    else:
                        storage_health[path] = {
                            'status': 'unhealthy',
                            'writable': False,
                            'error': 'Directory not writable'
                        }
                        health_status['status'] = 'degraded'
                else:
                    storage_health[path] = {
                        'status': 'unhealthy',
                        'exists': False,
                        'error': 'Directory does not exist'
                    }
                    health_status['status'] = 'degraded'
                    
            except Exception as e:
                storage_health[path] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        health_status['storage'] = storage_health
        
        # 6. Dependencies Check
        dependencies_status = {}
        
        # Check critical Python packages
        critical_packages = [
            'flask', 'sqlalchemy', 'psycopg2', 'redis', 
            'jwt', 'bcrypt', 'psutil', 'requests'
        ]
        
        for package in critical_packages:
            try:
                __import__(package)
                dependencies_status[package] = {'status': 'available'}
            except ImportError:
                dependencies_status[package] = {
                    'status': 'missing',
                    'error': 'Package not installed'
                }
                health_status['status'] = 'unhealthy'
        
        health_status['dependencies'] = dependencies_status
        
        # 7. Flask Application Health
        app_info = {
            'name': current_app.config.get('APP_NAME', 'Smart Attendance System'),
            'version': current_app.config.get('APP_VERSION', '1.0.0'),
            'environment': current_app.config.get('FLASK_ENV', 'production'),
            'debug_mode': current_app.debug,
            'testing_mode': current_app.testing
        }
        
        health_status['services']['application'] = {
            'status': 'healthy',
            'info': app_info
        }
        
        # 8. Overall Health Assessment
        total_checks = 0
        healthy_checks = 0
        
        # Count service checks
        for service_name, service_info in health_status['services'].items():
            total_checks += 1
            if service_info.get('status') == 'healthy':
                healthy_checks += 1
        
        # Count database checks
        if health_status['database'].get('connection', {}).get('status') == 'healthy':
            healthy_checks += 1
        total_checks += 1
        
        # Count storage checks
        for storage_info in health_status['storage'].values():
            total_checks += 1
            if storage_info.get('status') == 'healthy':
                healthy_checks += 1
        
        # Calculate health score
        health_score = round((healthy_checks / total_checks) * 100, 2) if total_checks > 0 else 0
        
        # Final status determination
        if health_score >= 95:
            final_status = 'healthy'
        elif health_score >= 80:
            final_status = 'degraded'
        else:
            final_status = 'unhealthy'
        
        health_status['status'] = final_status
        health_status['health_score'] = health_score
        health_status['checks_summary'] = {
            'total_checks': total_checks,
            'healthy_checks': healthy_checks,
            'failed_checks': total_checks - healthy_checks
        }
        
        # 9. Response Time
        total_response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        health_status['response_time_ms'] = round(total_response_time, 2)
        
        # 10. Recommendations
        recommendations = []
        
        if cpu_percent > 80:
            recommendations.append({
                'type': 'performance',
                'severity': 'high',
                'message': f'CPU usage is high ({cpu_percent}%). Consider scaling up resources.'
            })
        
        if memory.percent > 85:
            recommendations.append({
                'type': 'performance',
                'severity': 'high',
                'message': f'Memory usage is high ({memory.percent}%). Consider increasing memory allocation.'
            })
        
        if (disk.used / disk.total) * 100 > 90:
            recommendations.append({
                'type': 'storage',
                'severity': 'critical',
                'message': f'Disk usage is critical ({round((disk.used / disk.total) * 100, 2)}%). Clean up storage immediately.'
            })
        
        if health_status['database']['connection'].get('response_time_ms', 0) > 1000:
            recommendations.append({
                'type': 'database',
                'severity': 'medium',
                'message': 'Database response time is slow. Consider optimizing queries or scaling database.'
            })
        
        health_status['recommendations'] = recommendations
        
        # 11. Determine HTTP status code
        if final_status == 'healthy':
            status_code = 200
        elif final_status == 'degraded':
            status_code = 200  # Still operational
        else:
            status_code = 503  # Service unavailable
        
        # 12. Log health check
        logging.info(f'Health check completed: {final_status} (score: {health_score}%) in {total_response_time:.2f}ms')
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        # Critical error in health check itself
        error_response = {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': {
                'type': 'health_check_failure',
                'message': 'Health check system failure',
                'details': str(e)
            },
            'response_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
        }
        
        logging.error(f'Health check system failure: {str(e)}', exc_info=True)
        return jsonify(error_response), 503

@health_bp.route('/simple', methods=['GET'])
def simple_health_check():
    """
    GET /api/health/simple
    Simple health check for load balancers
    فحص صحة بسيط لموازن الأحمال
    """
    try:
        # Quick database test
        db.session.execute('SELECT 1').fetchone()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'System operational'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/database', methods=['GET'])
def database_health_check():
    """
    GET /api/health/database
    Detailed database health check
    فحص تفصيلي لصحة قاعدة البيانات
    """
    start_time = datetime.utcnow()
    
    try:
        from models import User, Student, Teacher, Subject, Room, Schedule, Lecture, AttendanceRecord, QRSession
        
        # Test basic operations
        db_tests = {}
        
        # 1. Connection test
        try:
            result = db.session.execute('SELECT version()').fetchone()
            db_tests['connection'] = {
                'status': 'healthy',
                'postgresql_version': result[0] if result else 'unknown'
            }
        except Exception as e:
            db_tests['connection'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # 2. Table existence test
        tables_to_check = [
            'users', 'students', 'teachers', 'subjects', 'rooms', 
            'schedules', 'lectures', 'attendance_records', 'qr_sessions'
        ]
        
        existing_tables = []
        for table in tables_to_check:
            try:
                db.session.execute(f'SELECT 1 FROM {table} LIMIT 1')
                existing_tables.append(table)
            except Exception:
                pass
        
        db_tests['tables'] = {
            'status': 'healthy' if len(existing_tables) == len(tables_to_check) else 'degraded',
            'expected_tables': len(tables_to_check),
            'existing_tables': len(existing_tables),
            'missing_tables': list(set(tables_to_check) - set(existing_tables))
        }
        
        # 3. Performance test
        perf_start = datetime.utcnow()
        try:
            User.query.count()
            Student.query.count()
            AttendanceRecord.query.limit(100).all()
            
            perf_time = (datetime.utcnow() - perf_start).total_seconds() * 1000
            db_tests['performance'] = {
                'status': 'healthy' if perf_time < 1000 else 'degraded',
                'response_time_ms': round(perf_time, 2)
            }
        except Exception as e:
            db_tests['performance'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # 4. Data integrity test
        try:
            # Check for orphaned records
            orphaned_students = Student.query.filter(~Student.user_id.in_(
                db.session.query(User.id)
            )).count()
            
            orphaned_schedules = Schedule.query.filter(~Schedule.subject_id.in_(
                db.session.query(Subject.id)
            )).count()
            
            db_tests['data_integrity'] = {
                'status': 'healthy' if (orphaned_students + orphaned_schedules) == 0 else 'degraded',
                'orphaned_students': orphaned_students,
                'orphaned_schedules': orphaned_schedules
            }
        except Exception as e:
            db_tests['data_integrity'] = {
                'status': 'unknown',
                'error': str(e)
            }
        
        # Overall database health
        healthy_tests = sum(1 for test in db_tests.values() if test.get('status') == 'healthy')
        total_tests = len(db_tests)
        
        overall_status = 'healthy' if healthy_tests == total_tests else ('degraded' if healthy_tests > 0 else 'unhealthy')
        
        response = {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'response_time_ms': round((datetime.utcnow() - start_time).total_seconds() * 1000, 2),
            'tests': db_tests,
            'summary': {
                'total_tests': total_tests,
                'healthy_tests': healthy_tests,
                'health_score': round((healthy_tests / total_tests) * 100, 2)
            }
        }
        
        status_code = 200 if overall_status in ['healthy', 'degraded'] else 503
        return jsonify(response), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'response_time_ms': round((datetime.utcnow() - start_time).total_seconds() * 1000, 2)
        }), 503

# Error handlers
@health_bp.errorhandler(Exception)
def handle_health_error(e):
    """Handle unexpected errors in health checks"""
    return jsonify({
        'status': 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'error': {
            'type': 'health_system_error',
            'message': str(e)
        }
    }), 503