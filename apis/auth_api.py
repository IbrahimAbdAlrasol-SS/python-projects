"""
🔐 Authentication APIs - مجموعة المصادقة الكاملة
Implementation: 3 core authentication endpoints
اليوم 1: التطبيق الكامل للمصادقة
"""

from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.security import check_password_hash
from security import (
    jwt_manager, PasswordManager, InputValidator,
    jwt_required, get_current_user, require_permission
)
from models import User, Student, Teacher, UserRole
from utils.response_helpers import success_response, error_response
from utils.validation_helpers import validate_required_fields
from datetime import datetime, timedelta
import logging
import uuid

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/student-login', methods=['POST'])
# @current_app.limiter.limit("5 per minute")  # تعليق مؤقت
def student_login():
    """
    POST /api/auth/student-login
    Student authentication with university_id + secret_code
    مصادقة الطلاب بالرقم الجامعي + الكود السري
    """
    try:
        # 1. Input validation
        data = request.get_json()
        if not data:
            return jsonify(error_response(
                'INVALID_INPUT', 
                'البيانات المدخلة غير صحيحة'
            )), 400
        
        # Validate required fields
        required_fields = ['university_id', 'secret_code']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify(validation_error), 400
        
        # Sanitize inputs
        university_id = InputValidator.sanitize_string(data.get('university_id', '')).upper()
        secret_code = InputValidator.sanitize_string(data.get('secret_code', ''))
        device_fingerprint = InputValidator.sanitize_string(data.get('device_fingerprint', ''))
        
        # Validate university ID format
        is_valid, error_msg = InputValidator.validate_university_id(university_id)
        if not is_valid:
            return jsonify(error_response('INVALID_ID_FORMAT', error_msg)), 400
        
        # 2. Check account lockout
        lockout_manager = getattr(current_app, 'lockout_manager', None)
        if lockout_manager:
            is_locked, unlock_time = lockout_manager.is_locked(university_id)
            if is_locked:
                return jsonify(error_response(
                    'ACCOUNT_LOCKED',
                    f'الحساب مقفل حتى {unlock_time.strftime("%H:%M")}',
                    {'unlock_time': unlock_time.isoformat()}
                )), 423
        
        # 3. Find student
        student = Student.query.filter_by(university_id=university_id).first()
        if not student:
            # Record failed attempt
            if lockout_manager:
                is_locked, remaining = lockout_manager.record_failed_attempt(university_id)
                return jsonify(error_response(
                    'INVALID_CREDENTIALS',
                    'الرقم الجامعي أو الكود السري غير صحيح',
                    {'remaining_attempts': remaining}
                )), 401
            return jsonify(error_response('INVALID_CREDENTIALS', 'الرقم الجامعي أو الكود السري غير صحيح')), 401
        
        # 4. Verify secret code
        if not student.verify_secret_code(secret_code):
            if lockout_manager:
                is_locked, remaining = lockout_manager.record_failed_attempt(university_id)
                if is_locked:
                    return jsonify(error_response(
                        'ACCOUNT_LOCKED',
                        'تم قفل الحساب بسبب المحاولات الفاشلة المتكررة',
                        {'lockout_duration': '15 minutes'}
                    )), 423
                
                return jsonify(error_response(
                    'INVALID_CREDENTIALS',
                    'الرقم الجامعي أو الكود السري غير صحيح',
                    {'remaining_attempts': remaining}
                )), 401
            return jsonify(error_response('INVALID_CREDENTIALS', 'الرقم الجامعي أو الكود السري غير صحيح')), 401
        
        # 5. Check if account is active
        user = student.user
        if not user.is_active:
            return jsonify(error_response('ACCOUNT_DISABLED', 'الحساب معطل، يرجى الاتصال بالإدارة')), 403
        
        # 6. Generate JWT tokens
        tokens = jwt_manager.generate_tokens(user, device_fingerprint)
        
        # 7. Reset lockout attempts on successful login
        if lockout_manager:
            lockout_manager.reset_attempts(university_id)
        
        # 8. Update last login
        user.update_last_login()
        
        # 9. Log successful login
        logging.info(f'Successful student login: {university_id} from IP: {request.remote_addr}')
        
        # 10. Return success response
        return jsonify(success_response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'token_type': 'Bearer',
            'user': {
                'id': student.id,
                'user_id': user.id,
                'university_id': student.university_id,
                'full_name': user.full_name,
                'email': user.email,
                'section': student.section.value,
                'study_year': student.study_year,
                'study_type': student.study_type.value,
                'face_registered': student.face_registered,
                'telegram_connected': student.telegram_id is not None,
                'role': user.role.value
            },
            'permissions': [
                'read_own_profile', 'update_own_profile', 'read_own_schedule', 
                'read_own_attendance', 'submit_attendance', 'submit_assignment'
            ]
        }, message='تم تسجيل الدخول بنجاح'))
        
    except Exception as e:
        logging.error(f'Student login error: {str(e)}', exc_info=True)
        return jsonify(error_response('LOGIN_ERROR', 'حدث خطأ أثناء تسجيل الدخول')), 500

@auth_bp.route('/teacher-login', methods=['POST'])
@current_app.limiter.limit("5 per minute")
def teacher_login():
    """
    POST /api/auth/teacher-login
    Teacher authentication with username + password
    مصادقة المدرسين باسم المستخدم + كلمة المرور
    """
    try:
        # 1. Input validation
        data = request.get_json()
        if not data:
            return jsonify(error_response('INVALID_INPUT', 'البيانات المدخلة غير صحيحة')), 400
        
        # Validate required fields
        required_fields = ['username', 'password']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify(validation_error), 400
        
        # Sanitize inputs
        username = InputValidator.sanitize_string(data.get('username', '')).lower()
        password = data.get('password', '')
        device_fingerprint = InputValidator.sanitize_string(data.get('device_fingerprint', ''))
        
        # Basic validation
        if len(username) < 3:
            return jsonify(error_response('INVALID_USERNAME', 'اسم المستخدم قصير جداً')), 400
        
        if len(password) < 6:
            return jsonify(error_response('INVALID_PASSWORD', 'كلمة المرور قصيرة جداً')), 400
        
        # 2. Check account lockout
        lockout_manager = getattr(current_app, 'lockout_manager', None)
        if lockout_manager:
            is_locked, unlock_time = lockout_manager.is_locked(username)
            if is_locked:
                return jsonify(error_response(
                    'ACCOUNT_LOCKED',
                    f'الحساب مقفل حتى {unlock_time.strftime("%H:%M")}',
                    {'unlock_time': unlock_time.isoformat()}
                )), 423
        
        # 3. Find teacher by username
        user = User.query.filter_by(username=username, role=UserRole.TEACHER).first()
        if not user:
            # Record failed attempt
            if lockout_manager:
                is_locked, remaining = lockout_manager.record_failed_attempt(username)
                return jsonify(error_response(
                    'INVALID_CREDENTIALS',
                    'اسم المستخدم أو كلمة المرور غير صحيحة',
                    {'remaining_attempts': remaining}
                )), 401
            return jsonify(error_response('INVALID_CREDENTIALS', 'اسم المستخدم أو كلمة المرور غير صحيحة')), 401
        
        # 4. Verify password
        if not user.check_password(password):
            if lockout_manager:
                is_locked, remaining = lockout_manager.record_failed_attempt(username)
                if is_locked:
                    return jsonify(error_response(
                        'ACCOUNT_LOCKED',
                        'تم قفل الحساب بسبب المحاولات الفاشلة المتكررة',
                        {'lockout_duration': '15 minutes'}
                    )), 423
                
                return jsonify(error_response(
                    'INVALID_CREDENTIALS',
                    'اسم المستخدم أو كلمة المرور غير صحيحة',
                    {'remaining_attempts': remaining}
                )), 401
            return jsonify(error_response('INVALID_CREDENTIALS', 'اسم المستخدم أو كلمة المرور غير صحيحة')), 401
        
        # 5. Check if account is active
        if not user.is_active:
            return jsonify(error_response('ACCOUNT_DISABLED', 'الحساب معطل، يرجى الاتصال بالإدارة')), 403
        
        # 6. Get teacher profile
        teacher = user.get_teacher_profile()
        if not teacher:
            return jsonify(error_response('PROFILE_NOT_FOUND', 'ملف المدرس غير موجود')), 404
        
        # 7. Generate JWT tokens
        tokens = jwt_manager.generate_tokens(user, device_fingerprint)
        
        # 8. Reset lockout attempts on successful login
        if lockout_manager:
            lockout_manager.reset_attempts(username)
        
        # 9. Update last login
        user.update_last_login()
        
        # 10. Log successful login
        logging.info(f'Successful teacher login: {username} from IP: {request.remote_addr}')
        
        # 11. Return success response
        return jsonify(success_response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'token_type': 'Bearer',
            'user': {
                'id': teacher.id,
                'user_id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'employee_id': teacher.employee_id,
                'department': teacher.department,
                'specialization': teacher.specialization,
                'academic_degree': teacher.academic_degree.value if teacher.academic_degree else None,
                'office_location': teacher.office_location,
                'subjects': teacher.subjects or [],
                'role': user.role.value
            },
            'permissions': [
                'read_student', 'read_schedule', 'read_attendance', 'update_attendance',
                'generate_qr', 'create_lecture', 'update_lecture', 'generate_reports',
                'create_assignment', 'update_assignment', 'grade_assignment'
            ]
        }, message='تم تسجيل الدخول بنجاح'))
        
    except Exception as e:
        logging.error(f'Teacher login error: {str(e)}', exc_info=True)
        return jsonify(error_response('LOGIN_ERROR', 'حدث خطأ أثناء تسجيل الدخول')), 500

@auth_bp.route('/refresh-token', methods=['POST'])
@jwt_required
def refresh_token():
    """
    POST /api/auth/refresh-token
    Refresh JWT access token
    تجديد الرمز المميز للوصول
    """
    try:
        # 1. Get current user
        user = get_current_user()
        if not user:
            return jsonify(error_response('USER_NOT_FOUND', 'المستخدم غير موجود')), 404
        
        # 2. Check if user is still active
        if not user.is_active:
            return jsonify(error_response('ACCOUNT_DISABLED', 'الحساب معطل')), 403
        
        # 3. Get device fingerprint from current token
        device_fingerprint = g.jwt_payload.get('device_fingerprint')
        
        # 4. Generate new tokens
        tokens = jwt_manager.generate_tokens(user, device_fingerprint)
        
        # 5. Optionally blacklist old token
        old_jti = g.jwt_payload.get('jti')
        old_exp = g.jwt_payload.get('exp')
        if old_jti and old_exp:
            jwt_manager.blacklist_token(old_jti, datetime.fromtimestamp(old_exp))
        
        # 6. Log token refresh
        logging.info(f'Token refreshed for user: {user.username} ({user.role.value})')
        
        # 7. Return new tokens
        return jsonify(success_response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'token_type': 'Bearer',
            'refreshed_at': datetime.utcnow().isoformat()
        }, message='تم تجديد الرمز المميز بنجاح'))
        
    except Exception as e:
        logging.error(f'Token refresh error: {str(e)}', exc_info=True)
        return jsonify(error_response('REFRESH_ERROR', 'حدث خطأ أثناء تجديد الرمز المميز')), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """
    POST /api/auth/logout
    Logout and blacklist token
    تسجيل الخروج وإبطال الرمز المميز
    """
    try:
        # 1. Get token info
        jti = g.jwt_payload.get('jti')
        exp = g.jwt_payload.get('exp')
        user_id = g.jwt_payload.get('user_id')
        
        # 2. Blacklist token
        if jti and exp:
            success = jwt_manager.blacklist_token(jti, datetime.fromtimestamp(exp))
            if not success:
                logging.warning(f'Failed to blacklist token for user {user_id}')
        
        # 3. Log logout
        logging.info(f'User logged out: {user_id} from IP: {request.remote_addr}')
        
        # 4. Return success
        return jsonify(success_response({
            'logged_out_at': datetime.utcnow().isoformat()
        }, message='تم تسجيل الخروج بنجاح'))
        
    except Exception as e:
        logging.error(f'Logout error: {str(e)}', exc_info=True)
        return jsonify(error_response('LOGOUT_ERROR', 'حدث خطأ أثناء تسجيل الخروج')), 500

@auth_bp.route('/validate-token', methods=['GET'])
@jwt_required
def validate_token():
    """
    GET /api/auth/validate-token
    Validate current token and return user info
    التحقق من صحة الرمز المميز وإرجاع معلومات المستخدم
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify(error_response('TOKEN_INVALID', 'الرمز المميز غير صالح')), 401
        
        # Prepare user data based on role
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email,
            'role': user.role.value,
            'is_active': user.is_active,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        
        # Add role-specific data
        if user.role == UserRole.STUDENT:
            student = user.get_student_profile()
            if student:
                user_data.update({
                    'student_id': student.id,
                    'university_id': student.university_id,
                    'section': student.section.value,
                    'study_year': student.study_year,
                    'study_type': student.study_type.value,
                    'face_registered': student.face_registered,
                    'telegram_connected': student.telegram_id is not None
                })
        
        elif user.role == UserRole.TEACHER:
            teacher = user.get_teacher_profile()
            if teacher:
                user_data.update({
                    'teacher_id': teacher.id,
                    'employee_id': teacher.employee_id,
                    'department': teacher.department,
                    'academic_degree': teacher.academic_degree.value if teacher.academic_degree else None
                })
        
        return jsonify(success_response({
            'valid': True,
            'user': user_data,
            'token_info': {
                'expires_at': datetime.fromtimestamp(g.jwt_payload.get('exp')).isoformat(),
                'issued_at': datetime.fromtimestamp(g.jwt_payload.get('iat')).isoformat(),
                'issuer': g.jwt_payload.get('iss', 'attendance-system')
            }
        }))
        
    except Exception as e:
        logging.error(f'Token validation error: {str(e)}', exc_info=True)
        return jsonify(error_response('VALIDATION_ERROR', 'حدث خطأ أثناء التحقق من الرمز المميز')), 500

# Error handlers specific to auth blueprint
@auth_bp.errorhandler(429)
def auth_rate_limit_exceeded(e):
    """Handle rate limit exceeded for auth endpoints"""
    return jsonify(error_response(
        'RATE_LIMIT_EXCEEDED',
        'تم تجاوز الحد المسموح من المحاولات، يرجى المحاولة لاحقاً',
        {'retry_after': '60 seconds'}
    )), 429

@auth_bp.errorhandler(400)
def auth_bad_request(e):
    """Handle bad request errors in auth"""
    return jsonify(error_response(
        'BAD_REQUEST',
        'طلب غير صحيح، يرجى التحقق من البيانات المرسلة'
    )), 400

@auth_bp.errorhandler(401)
def auth_unauthorized(e):
    """Handle unauthorized errors in auth"""
    return jsonify(error_response(
        'UNAUTHORIZED',
        'غير مصرح، يرجى تسجيل الدخول أولاً'
    )), 401