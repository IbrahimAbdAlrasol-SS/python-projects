"""
Example authentication routes using the security layer
مثال على استخدام نظام الأمان
"""
from flask import Blueprint, request, jsonify
from security import (
    jwt_manager, PasswordManager, InputValidator,
    jwt_required, get_current_user, require_permission
)
from models import User, Student, UserRole

auth_bp = Blueprint('auth', name, url_prefix='/api/auth')

@auth_bp.route('/student-login', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting
def student_login():
    """Student login with complete security"""
    # 1. Input validation
    data = request.get_json()

    university_id = InputValidator.sanitize_string(data.get('university_id', ''))
    secret_code = InputValidator.sanitize_string(data.get('secret_code', ''))
    device_fingerprint = InputValidator.sanitize_string(data.get('device_fingerprint', ''))

    # Validate university ID format
    is_valid, error = InputValidator.validate_university_id(university_id)
    if not is_valid:
        return jsonify({'error': error}), 400

    # 2. Check account lockout
    lockout_manager = current_app.lockout_manager
    if lockout_manager:
        is_locked, unlock_time = lockout_manager.is_locked(university_id)
        if is_locked:
            return jsonify({
                'error': 'Account is locked',
                'unlock_time': unlock_time.isoformat(),
                'message': 'Too many failed login attempts'
            }), 423  # Locked status

    # 3. Find student
    student = Student.find_by_university_id(university_id)
    if not student:
        # Record failed attempt
        if lockout_manager:
            is_locked, remaining = lockout_manager.record_failed_attempt(university_id)
            return jsonify({
                'error': 'Invalid credentials',
                'remaining_attempts': remaining
            }), 401
        return jsonify({'error': 'Invalid credentials'}), 401

    # 4. Verify secret code
    if not student.verify_secret_code(secret_code):
        # Record failed attempt
        if lockout_manager:
            is_locked, remaining = lockout_manager.record_failed_attempt(university_id)
            if is_locked:
                return jsonify({
                    'error': 'Account locked due to multiple failed attempts',
                    'lockout_duration': '15 minutes'
                }), 423
            
            return jsonify({
                'error': 'Invalid credentials',
                'remaining_attempts': remaining
            }), 401
        return jsonify({'error': 'Invalid credentials'}), 401

    # 5. Check if account is active
    user = student.user
    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403

    # 6. Generate JWT tokens
    tokens = jwt_manager.generate_tokens(user, device_fingerprint)

    # 7. Reset lockout attempts on successful login
    if lockout_manager:
        lockout_manager.reset_attempts(university_id)

    # 8. Update last login
    user.update_last_login()

    # 9. Return success response
    return jsonify({
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'expires_in': tokens['expires_in'],
        'user': {
            'id': student.id,
            'university_id': student.university_id,
            'full_name': user.full_name,
            'section': student.section.value,
            'study_year': student.study_year,
            'face_registered': student.face_registered
        }
    })

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required
def refresh_token():
    """Refresh access token"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    tokens = jwt_manager.generate_tokens(user)

    return jsonify({
        'access_token': tokens['access_token'],
        'expires_in': tokens['expires_in']
    })

@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """Logout and blacklist token"""
    jti = g.jwt_payload.get('jti')
    exp = g.jwt_payload.get('exp')
    if jti and exp:
        # Add token to blacklist
        jwt_manager.blacklist_token(jti, datetime.fromtimestamp(exp))

    return jsonify({'message': 'Successfully logged out'})
