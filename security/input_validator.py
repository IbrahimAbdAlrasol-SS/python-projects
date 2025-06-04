"""
Input Validation System
نظام التحقق من المدخلات
"""

import re
import bleach
from typing import Optional, Dict, Any
from datetime import datetime


class InputValidator:
    """Comprehensive input validation to prevent XSS and SQL injection"""

    # Regex patterns
    PATTERNS = {
        'university_id': r'^[A-Z]{2}\d{7}$',  # CS2021001
        'employee_id': r'^EMP\d{6}$',         # EMP123456
        'username': r'^[a-zA-Z0-9_]{3,20}$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^(\+964|0)?7[0-9]{9}$',   # Iraqi phone numbers
        'section': r'^[A-C]$',
        'year': r'^[1-4]$',
        'room_name': r'^[A-Z]\d{3}$',        # A101, B205
        'subject_code': r'^[A-Z]{2}\d{3}$'   # CS101
    }

    # Allowed HTML tags (none by default)
    ALLOWED_TAGS = []
    ALLOWED_ATTRIBUTES = {}

    @classmethod
    def sanitize_string(cls, value: Optional[str], max_length: int = 255) -> str:
        """Sanitize string input"""
        if not value:
            return ""
        
        # Strip whitespace
        value = value.strip()
        
        # Remove HTML tags and dangerous characters
        value = bleach.clean(
            value,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        # Limit length
        value = value[:max_length]
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        return value

    @classmethod
    def validate_pattern(cls, value: str, pattern_name: str) -> bool:
        """Validate value against predefined pattern"""
        pattern = cls.PATTERNS.get(pattern_name)
        if not pattern:
            return False
        
        return bool(re.match(pattern, value))

    @classmethod
    def validate_university_id(cls, university_id: str) -> tuple[bool, Optional[str]]:
        """Validate university ID format"""
        if not university_id:
            return False, "University ID is required"
        
        university_id = university_id.strip().upper()
        
        if not cls.validate_pattern(university_id, 'university_id'):
            return False, "Invalid university ID format (expected: CS2021001)"
        
        return True, None

    @classmethod
    def validate_email(cls, email: str) -> tuple[bool, Optional[str]]:
        """Validate email format"""
        if not email:
            return False, "Email is required"
        
        email = email.strip().lower()
        
        if not cls.validate_pattern(email, 'email'):
            return False, "Invalid email format"
        
        # Additional checks
        if '..' in email or email.startswith('.') or email.endswith('.'):
            return False, "Invalid email format"
        
        return True, None

    @classmethod
    def validate_phone(cls, phone: str) -> tuple[bool, Optional[str]]:
        """Validate Iraqi phone number"""
        if not phone:
            return True, None  # Phone is optional
        
        phone = phone.strip()
        
        if not cls.validate_pattern(phone, 'phone'):
            return False, "Invalid phone number format"
        
        return True, None

    @classmethod
    def validate_integer(cls, value: Any, min_value: int = None, max_value: int = None) -> tuple[bool, Optional[str]]:
        """Validate integer value"""
        try:
            int_value = int(value)
            
            if min_value is not None and int_value < min_value:
                return False, f"Value must be at least {min_value}"
            
            if max_value is not None and int_value > max_value:
                return False, f"Value must be at most {max_value}"
            
            return True, None
            
        except (ValueError, TypeError):
            return False, "Invalid integer value"

    @classmethod
    def validate_date(cls, date_string: str, format: str = "%Y-%m-%d") -> tuple[bool, Optional[str]]:
        """Validate date string"""
        try:
            datetime.strptime(date_string, format)
            return True, None
        except ValueError:
            return False, f"Invalid date format (expected: {format})"

    @classmethod
    def validate_gps_coordinates(cls, latitude: float, longitude: float) -> tuple[bool, Optional[str]]:
        """Validate GPS coordinates"""
        try:
            lat = float(latitude)
            lng = float(longitude)
            
            if not (-90 <= lat <= 90):
                return False, "Latitude must be between -90 and 90"
            
            if not (-180 <= lng <= 180):
                return False, "Longitude must be between -180 and 180"
            
            return True, None
            
        except (ValueError, TypeError):
            return False, "Invalid coordinate values"

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], allowed_fields: list) -> Dict[str, Any]:
        """Sanitize dictionary by removing unexpected fields"""
        return {
            key: cls.sanitize_string(value) if isinstance(value, str) else value
            for key, value in data.items()
            if key in allowed_fields
        }

    @classmethod
    def prevent_sql_injection(cls, value: str) -> str:
        """Additional SQL injection prevention"""
        # Remove common SQL injection patterns
        dangerous_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)',
            r'(--|\||;|\/\*|\*\/|xp_|sp_)',
            r'(\bor\b\s*\d+\s*=\s*\d+)',
            r'(\band\b\s*\d+\s*=\s*\d+)'
        ]
        
        clean_value = value
        for pattern in dangerous_patterns:
            clean_value = re.sub(pattern, '', clean_value, flags=re.IGNORECASE)
        
        return clean_value
