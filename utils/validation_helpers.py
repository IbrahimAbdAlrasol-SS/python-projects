"""
🔍 Validation Helpers - نظام التحقق الشامل
Comprehensive validation for all API inputs
نظام التحقق الشامل لجميع مدخلات الـ APIs
"""

import re
import bleach
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime, date
import email_validator
from urllib.parse import urlparse

class ValidationError(Exception):
    """Custom validation exception"""
    def __init__(self, message: str, field: str = None, details: Dict = None):
        self.message = message
        self.field = field
        self.details = details or {}
        super().__init__(self.message)

class InputValidator:
    """Comprehensive input validation class"""
    
    # Regex patterns
    UNIVERSITY_ID_PATTERN = r'^[A-Z]{2}\d{7}$'  # CS2021001
    PHONE_PATTERN = r'^\+964[0-9]{10}$'          # +96477123456789
    EMPLOYEE_ID_PATTERN = r'^[A-Z]\d{3,6}$'     # T001, E12345
    
    # Allowed HTML tags (very restrictive)
    ALLOWED_TAGS = []
    ALLOWED_ATTRIBUTES = {}
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255, allow_arabic: bool = True) -> str:
        """
        Clean and sanitize string input
        
        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length
            allow_arabic: Whether to allow Arabic characters
        
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # Remove HTML tags and dangerous characters
        cleaned = bleach.clean(input_str.strip(), tags=InputValidator.ALLOWED_TAGS, strip=True)
        
        # Remove or replace dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\\', '/', '`']
        for char in dangerous_chars:
            cleaned = cleaned.replace(char, '')
        
        # Trim to max length
        cleaned = cleaned[:max_length]
        
        # Validate character set if Arabic not allowed
        if not allow_arabic:
            # Keep only ASCII characters, numbers, and basic punctuation
            cleaned = re.sub(r'[^\x00-\x7F]+', '', cleaned)
        
        return cleaned.strip()
    
    @staticmethod
    def validate_university_id(university_id: str) -> Tuple[bool, str]:
        """
        Validate university ID format
        
        Args:
            university_id: University ID to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not university_id:
            return False, "الرقم الجامعي مطلوب"
        
        if not re.match(InputValidator.UNIVERSITY_ID_PATTERN, university_id):
            return False, "صيغة الرقم الجامعي غير صحيحة (مثال: CS2021001)"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email address
        
        Args:
            email: Email address to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "البريد الإلكتروني مطلوب"
        
        try:
            # Use email-validator library for comprehensive validation
            email_validator.validate_email(email)
            return True, ""
        except email_validator.EmailNotValidError as e:
            return False, f"البريد الإلكتروني غير صحيح: {str(e)}"
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """
        Validate Iraqi phone number
        
        Args:
            phone: Phone number to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return False, "رقم الهاتف مطلوب"
        
        if not re.match(InputValidator.PHONE_PATTERN, phone):
            return False, "صيغة رقم الهاتف غير صحيحة (مثال: +96477123456789)"
        
        return True, ""
    
    @staticmethod
    def validate_employee_id(employee_id: str) -> Tuple[bool, str]:
        """
        Validate employee ID format
        
        Args:
            employee_id: Employee ID to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not employee_id:
            return False, "رقم الموظف مطلوب"
        
        if not re.match(InputValidator.EMPLOYEE_ID_PATTERN, employee_id):
            return False, "صيغة رقم الموظف غير صحيحة (مثال: T001)"
        
        return True, ""
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> Tuple[bool, str]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            min_length: Minimum password length
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "كلمة المرور مطلوبة"
        
        if len(password) < min_length:
            return False, f"كلمة المرور يجب أن تكون {min_length} أحرف على الأقل"
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            return False, "كلمة المرور يجب أن تحتوي على رقم واحد على الأقل"
        
        # Check for at least one letter
        if not re.search(r'[a-zA-Z]', password):
            return False, "كلمة المرور يجب أن تحتوي على حرف واحد على الأقل"
        
        return True, ""
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> Tuple[bool, str]:
        """
        Validate GPS coordinates
        
        Args:
            latitude: Latitude value
            longitude: Longitude value
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not (-90 <= latitude <= 90):
            return False, "خط العرض يجب أن يكون بين -90 و 90"
        
        if not (-180 <= longitude <= 180):
            return False, "خط الطول يجب أن يكون بين -180 و 180"
        
        return True, ""

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Optional[Dict[str, Any]]:
    """
    Validate that all required fields are present and not empty
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
    
    Returns:
        Error response dict if validation fails, None if valid
    """
    if not data:
        return {
            'success': False,
            'error': {
                'code': 'INVALID_INPUT',
                'message': 'البيانات مطلوبة'
            }
        }
    
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
            empty_fields.append(field)
    
    if missing_fields or empty_fields:
        error_details = {}
        if missing_fields:
            error_details['missing_fields'] = missing_fields
        if empty_fields:
            error_details['empty_fields'] = empty_fields
        
        return {
            'success': False,
            'error': {
                'code': 'MISSING_REQUIRED_FIELDS',
                'message': 'حقول مطلوبة مفقودة أو فارغة',
                'details': error_details
            }
        }
    
    return None

def validate_pagination_params(page: int, limit: int, max_limit: int = 100) -> Tuple[int, int, Optional[Dict]]:
    """
    Validate and normalize pagination parameters
    
    Args:
        page: Page number (1-based)
        limit: Items per page
        max_limit: Maximum allowed limit
    
    Returns:
        Tuple of (normalized_page, normalized_limit, error_dict)
    """
    # Normalize page
    if page < 1:
        normalized_page = 1
    else:
        normalized_page = page
    
    # Normalize limit
    if limit < 1:
        normalized_limit = 20  # Default
    elif limit > max_limit:
        normalized_limit = max_limit
    else:
        normalized_limit = limit
    
    # Check for unreasonable values
    if page > 10000:  # Prevent excessive pagination
        return normalized_page, normalized_limit, {
            'success': False,
            'error': {
                'code': 'INVALID_PAGINATION',
                'message': 'رقم الصفحة كبير جداً'
            }
        }
    
    return normalized_page, normalized_limit, None

def validate_date_range(start_date_str: str, end_date_str: str) -> Tuple[Optional[date], Optional[date], Optional[Dict]]:
    """
    Validate date range parameters
    
    Args:
        start_date_str: Start date string (YYYY-MM-DD)
        end_date_str: End date string (YYYY-MM-DD)
    
    Returns:
        Tuple of (start_date, end_date, error_dict)
    """
    start_date = None
    end_date = None
    
    # Parse start date
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
        except ValueError:
            return None, None, {
                'success': False,
                'error': {
                    'code': 'INVALID_START_DATE',
                    'message': 'تنسيق تاريخ البداية غير صحيح (استخدم YYYY-MM-DD)'
                }
            }
    
    # Parse end date
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str).date()
        except ValueError:
            return None, None, {
                'success': False,
                'error': {
                    'code': 'INVALID_END_DATE',
                    'message': 'تنسيق تاريخ النهاية غير صحيح (استخدم YYYY-MM-DD)'
                }
            }
    
    # Validate date range logic
    if start_date and end_date:
        if start_date > end_date:
            return None, None, {
                'success': False,
                'error': {
                    'code': 'INVALID_DATE_RANGE',
                    'message': 'تاريخ البداية يجب أن يكون قبل تاريخ النهاية'
                }
            }
        
        # Check for reasonable range (not more than 1 year)
        if (end_date - start_date).days > 365:
            return None, None, {
                'success': False,
                'error': {
                    'code': 'DATE_RANGE_TOO_LARGE',
                    'message': 'نطاق التاريخ كبير جداً (الحد الأقصى سنة واحدة)'
                }
            }
    
    return start_date, end_date, None

def validate_filters(filters: Dict[str, Any], allowed_filters: List[str]) -> Tuple[Dict[str, Any], Optional[Dict]]:
    """
    Validate and sanitize filter parameters
    
    Args:
        filters: Filter parameters dictionary
        allowed_filters: List of allowed filter keys
    
    Returns:
        Tuple of (sanitized_filters, error_dict)
    """
    sanitized_filters = {}
    
    for key, value in filters.items():
        if key not in allowed_filters:
            continue  # Skip unknown filters silently
        
        if value is None or value == '':
            continue  # Skip empty filters
        
        # Sanitize filter value
        if isinstance(value, str):
            sanitized_value = InputValidator.sanitize_string(value, max_length=100)
            if sanitized_value:
                sanitized_filters[key] = sanitized_value
        else:
            sanitized_filters[key] = value
    
    return sanitized_filters, None

def validate_bulk_operation_limit(items: List[Any], max_items: int = 100) -> Optional[Dict]:
    """
    Validate bulk operation limits
    
    Args:
        items: List of items to process
        max_items: Maximum allowed items
    
    Returns:
        Error dict if limit exceeded, None if valid
    """
    if not items:
        return {
            'success': False,
            'error': {
                'code': 'EMPTY_BULK_OPERATION',
                'message': 'قائمة العناصر فارغة'
            }
        }
    
    if len(items) > max_items:
        return {
            'success': False,
            'error': {
                'code': 'BULK_LIMIT_EXCEEDED',
                'message': f'عدد العناصر يتجاوز الحد المسموح ({max_items})',
                'details': {
                    'submitted_count': len(items),
                    'max_allowed': max_items
                }
            }
        }
    
    return None

def validate_ids_list(ids: List[Union[int, str]], resource_type: str = "عنصر") -> Optional[Dict]:
    """
    Validate list of IDs
    
    Args:
        ids: List of IDs to validate
        resource_type: Type of resource for error messages
    
    Returns:
        Error dict if validation fails, None if valid
    """
    if not ids:
        return {
            'success': False,
            'error': {
                'code': 'EMPTY_IDS_LIST',
                'message': f'قائمة معرفات الـ{resource_type} فارغة'
            }
        }
    
    # Check for duplicates
    if len(ids) != len(set(ids)):
        return {
            'success': False,
            'error': {
                'code': 'DUPLICATE_IDS',
                'message': f'معرفات مكررة في قائمة الـ{resource_type}'
            }
        }
    
    # Validate each ID
    invalid_ids = []
    for id_val in ids:
        if isinstance(id_val, str):
            if not id_val.strip():
                invalid_ids.append(id_val)
        elif isinstance(id_val, int):
            if id_val <= 0:
                invalid_ids.append(id_val)
        else:
            invalid_ids.append(id_val)
    
    if invalid_ids:
        return {
            'success': False,
            'error': {
                'code': 'INVALID_IDS',
                'message': f'معرفات غير صحيحة في قائمة الـ{resource_type}',
                'details': {'invalid_ids': invalid_ids}
            }
        }
    
    return None

def validate_sort_params(sort_by: str, sort_order: str, allowed_fields: List[str]) -> Optional[Dict]:
    """
    Validate sorting parameters
    
    Args:
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        allowed_fields: List of allowed sort fields
    
    Returns:
        Error dict if validation fails, None if valid
    """
    if sort_by and sort_by not in allowed_fields:
        return {
            'success': False,
            'error': {
                'code': 'INVALID_SORT_FIELD',
                'message': f'حقل الترتيب غير مدعوم. الحقول المدعومة: {", ".join(allowed_fields)}'
            }
        }
    
    if sort_order and sort_order.lower() not in ['asc', 'desc']:
        return {
            'success': False,
            'error': {
                'code': 'INVALID_SORT_ORDER',
                'message': 'اتجاه الترتيب يجب أن يكون asc أو desc'
            }
        }
    
    return None

# Specific validation functions for common use cases

def validate_section(section: str) -> Tuple[bool, str]:
    """Validate section value"""
    valid_sections = ['A', 'B', 'C', 'D', 'E']
    if section not in valid_sections:
        return False, f'الشعبة غير صحيحة. الشعب المدعومة: {", ".join(valid_sections)}'
    return True, ""

def validate_study_year(study_year: int) -> Tuple[bool, str]:
    """Validate study year"""
    if not isinstance(study_year, int) or not (1 <= study_year <= 4):
        return False, 'السنة الدراسية يجب أن تكون بين 1 و 4'
    return True, ""

def validate_academic_year(academic_year: str) -> Tuple[bool, str]:
    """Validate academic year format"""
    pattern = r'^\d{4}-\d{4}$'
    if not re.match(pattern, academic_year):
        return False, 'صيغة السنة الأكاديمية غير صحيحة (مثال: 2023-2024)'
    
    # Check year logic
    years = academic_year.split('-')
    if int(years[1]) - int(years[0]) != 1:
        return False, 'السنة الأكاديمية يجب أن تكون متتالية (مثال: 2023-2024)'
    
    return True, ""

def validate_semester(semester: str) -> Tuple[bool, str]:
    """Validate semester value"""
    valid_semesters = ['first', 'second', 'summer']
    if semester not in valid_semesters:
        return False, f'الفصل الدراسي غير صحيح. الفصول المدعومة: {", ".join(valid_semesters)}'
    return True, ""

# Export all validation functions
__all__ = [
    'ValidationError',
    'InputValidator',
    'validate_required_fields',
    'validate_pagination_params', 
    'validate_date_range',
    'validate_filters',
    'validate_bulk_operation_limit',
    'validate_ids_list',
    'validate_sort_params',
    'validate_section',
    'validate_study_year',
    'validate_academic_year',
    'validate_semester'
]