"""
Role-Based Access Control (RBAC)
نظام التحكم في الصلاحيات
"""
from functools import wraps
from flask import g, jsonify

# Permission definitions
PERMISSIONS = {
    'admin': [
        # Student management
        'create_student', 'read_student', 'update_student', 'delete_student',
        'bulk_create_students', 'export_students',

        # Teacher management
        'create_teacher', 'read_teacher', 'update_teacher', 'delete_teacher',
        
        # Room management
        'create_room', 'read_room', 'update_room', 'delete_room',
        
        # Schedule management
        'create_schedule', 'read_schedule', 'update_schedule', 'delete_schedule',
        
        # Attendance management
        'read_all_attendance', 'update_attendance', 'delete_attendance',
        'approve_exceptional_attendance',
        
        # Reports
        'generate_all_reports', 'export_reports',
        
        # System
        'system_settings', 'user_management', 'view_logs', 'system_health'
    ],

    'teacher': [
        # Students (limited)
        'read_student', 'read_assigned_students',
        
        # Schedules
        'read_schedule', 'read_own_schedule',
        
        # Attendance
        'read_attendance', 'update_attendance', 'generate_qr',
        'approve_exceptional_attendance',
        
        # Lectures
        'create_lecture', 'update_lecture', 'cancel_lecture',
        
        # Reports
        'generate_class_reports', 'generate_student_reports',
        
        # Assignments (للبوت)
        'create_assignment', 'update_assignment', 'delete_assignment',
        'grade_assignment'
    ],

    'student': [
        # Profile
        'read_own_profile', 'update_own_profile',
        
        # Schedule
        'read_own_schedule',
        
        # Attendance
        'read_own_attendance', 'submit_attendance',
        
        # Assignments
        'read_assignments', 'submit_assignment'
    ]
}

def get_user_permissions(role):
    """Get permissions for a role"""
    return PERMISSIONS.get(role, [])

def has_permission(user_role, permission):
    """Check if role has permission"""
    return permission in get_user_permissions(user_role)

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'current_user_role'):
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # Check permission
            if not has_permission(g.current_user_role, permission):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'code': 'PERMISSION_DENIED',
                    'required_permission': permission
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_permission(permission):
    """Check if current user has permission (non-decorator)"""
    if not hasattr(g, 'current_user_role'):
        return False
    return has_permission(g.current_user_role, permission)

def require_any_permission(*permissions):
    """Require at least one of the specified permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user_role'):
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # Check if user has any of the required permissions
            user_permissions = get_user_permissions(g.current_user_role)
            if not any(perm in user_permissions for perm in permissions):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'code': 'PERMISSION_DENIED',
                    'required_permissions': list(permissions)
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
