"""
🔧 Core API Helpers - مساعدات الـ APIs الأساسية
Implementation: Response helpers, validation helpers, and core utilities
اليوم 1: أدوات مساعدة أساسية لجميع الـ APIs
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
import bleach
from functools import wraps
from flask import request, jsonify, g

# ============================================================================
# RESPONSE HELPERS - مساعدات الاستجابات
# ============================================================================

@dataclass
class StandardResponse:
    """Standardized API response format"""
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    pagination: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def to_dict(self):
        result = {
            'success': self.success,
            'timestamp': self.timestamp or datetime.utcnow().isoformat()
        }
        
        if self.data is not None:
            result['data'] = self.data
        if self.error is not None:
            result['error'] = self.error
        if self.pagination is not None:
            result['pagination'] = self.pagination
        if self.meta is not None:
            result['meta'] = self.meta
            
        return result

def success_response(data=None, pagination=None, meta=None, message=None):
    """
    Create standardized success response
    
    Args:
        data: Response data
        pagination: Pagination info for list endpoints
        meta: Additional metadata
        message: Success message
    
    Returns:
        dict: Standardized success response
    """
    response = StandardResponse(success=True, data=data, pagination=pagination, meta=meta)
    
    if message:
        if response.meta is None:
            response.meta = {}
        response.meta['message'] = message
        response.meta['message_type'] = 'success'
    
    return response.to_dict()

def error_response(code, message, details=None, status_code=None):
    """
    Create standardized error response
    
    Args:
        code: Error code (e.g., 'INVALID_INPUT')
        message: Human-readable error message
        details: Additional error details
        status_code: HTTP status code
    
    Returns:
        dict: Standardized error response
    """
    error = {
        'code': code,
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': getattr(g, 'request_id', None)
    }
    
    if details:
        error['details'] = details
    
    if status_code:
        error['status_code'] = status_code
    
    return StandardResponse(success=False, error=error).to_dict()

def paginated_response(items, page, limit, total_count, additional_data=None):
    """
    Create paginated response
    
    Args:
        items: List of items for current page
        page: Current page number
        limit: Items per page
        total_count: Total number of items
        additional_data: Additional data to include
    
    Returns:
        dict: Paginated response
    """
    total_pages = (total_count + limit - 1) // limit  # Ceiling division
    
    pagination = {
        'current_page': page,
        'items_per_page': limit,
        'total_items': total_count,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_previous': page > 1,
        'next_page': page + 1 if page < total_pages else None,
        'previous_page': page - 1 if page > 1 else None,
        'first_page': 1,
        'last_page': total_pages,
        'items_on_page': len(items)
    }
    
    data = {
        'items': items,
        'count': len(items)
    }
    
    if additional_data:
        data.update(additional_data)
    
    return success_response(data=data, pagination=pagination)

def validation_error_response(field_errors):
    """
    Create validation error response
    
    Args:
        field_errors: Dict of field validation errors
    
    Returns:
        dict: Validation error response
    """
    return error_response(
        code='VALIDATION_ERROR',
        message='بيانات غير صحيحة',
        details={
            'field_errors': field_errors,
            'total_errors': len(field_errors),
            'error_type': 'validation'
        }
    )

def not_found_response(resource_type, identifier=None):
    """
    Create not found error response
    
    Args:
        resource_type: Type of resource (e.g., 'student', 'lecture')
        identifier: Resource identifier
    
    Returns:
        dict: Not found error response
    """
    message = f'{resource_type} غير موجود'
    if identifier:
        message += f': {identifier}'
    
    return error_response(
        code='NOT_FOUND',
        message=message,
        details={'resource_type': resource_type, 'identifier': identifier}
    )

def unauthorized_response(message='غير مصرح بالوصول'):
    """Create unauthorized error response"""
    return error_response(
        code='UNAUTHORIZED',
        message=message,
        details={'auth_required': True}
    )

def forbidden_response(message='صلاحيات غير كافية'):
    """Create forbidden error response"""
    return error_response(
        code='FORBIDDEN',
        message=message,
        details={'permission_required': True}
    )

def rate_limit_response(retry_after=None):
    """Create rate limit exceeded error response"""
    details = {'rate_limit_exceeded': True}
    if retry_after:
        details['retry_after'] = retry_after
    
    return error_response(
        code='RATE_LIMIT_EXCEEDED',
        message='تم تجاوز الحد المسموح من الطلبات',
        details=details
    )

def server_error_response(message='حدث خطأ في الخادم'):
    """Create internal server error response"""
    return error_response(
        code='INTERNAL_SERVER_ERROR',
        message=message,
        details={'server_error': True}
    )

def batch_response(results, summary=None):
    """
    Create batch operation response
    
    Args:
        results: List of operation results
        summary: Summary of batch operation
    
    Returns:
        dict: Batch operation response
    """
    if not summary:
        successful = sum(1 for result in results if result.get('success', False))
        failed = len(results) - successful
        
        summary = {
            'total': len(results),
            'successful': successful,
            'failed': failed,
            'success_rate': round((successful / len(results)) * 100, 2) if results else 0,
            'operation_type': 'batch'
        }
    
    return success_response(
        data={'results': results},
        meta={'batch_summary': summary}
    )

# ============================================================================
# VALIDATION HELPERS - مساعدات التحقق
# ============================================================================

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Optional[Dict[str, Any]]:
    """
    Validate that all required fields are present and not empty
    
    Args:
        data: Input data dictionary
        required_fields: List of required field names
    
    Returns:
        dict: Error response if validation fails, None if success
    """
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            empty_fields.append(field)
    
    errors = {}
    if missing_fields:
        errors['missing_fields'] = {
            'fields': missing_fields,
            'message': f'الحقول التالية مطلوبة: {", ".join(missing_fields)}'
        }
    
    if empty_fields:
        errors['empty_fields'] = {
            'fields': empty_fields,
            'message': f'الحقول التالية لا يمكن أن تكون فارغة: {", ".join(empty_fields)}'
        }
    
    if errors:
        return validation_error_response(errors)
    
    return None

def validate_pagination_params(page: Any = None, limit: Any = None, max_limit: int = 100) -> Tuple[int, int, Optional[Dict]]:
    """
    Validate and normalize pagination parameters
    
    Args:
        page: Page number (can be string or int)
        limit: Items per page (can be string or int)
        max_limit: Maximum allowed limit
    
    Returns:
        tuple: (normalized_page, normalized_limit, error_response)
    """
    errors = {}
    
    # Validate page
    try:
        normalized_page = int(page) if page is not None else 1
        if normalized_page < 1:
            errors['page'] = 'رقم الصفحة يجب أن يكون أكبر من صفر'
    except (ValueError, TypeError):
        errors['page'] = 'رقم الصفحة يجب أن يكون رقم صحيح'
        normalized_page = 1
    
    # Validate limit
    try:
        normalized_limit = int(limit) if limit is not None else 20
        if normalized_limit < 1:
            errors['limit'] = 'عدد العناصر يجب أن يكون أكبر من صفر'
        elif normalized_limit > max_limit:
            errors['limit'] = f'عدد العناصر لا يمكن أن يتجاوز {max_limit}'
            normalized_limit = max_limit
    except (ValueError, TypeError):
        errors['limit'] = 'عدد العناصر يجب أن يكون رقم صحيح'
        normalized_limit = 20
    
    error_response_obj = validation_error_response(errors) if errors else None
    
    return normalized_page, normalized_limit, error_response_obj

def validate_date_range(start_date: str = None, end_date: str = None, date_format: str = '%Y-%m-%d') -> Tuple[Optional[datetime.date], Optional[datetime.date], Optional[Dict]]:
    """
    Validate date range parameters
    
    Args:
        start_date: Start date string
        end_date: End date string
        date_format: Expected date format
    
    Returns:
        tuple: (start_date_obj, end_date_obj, error_response)
    """
    errors = {}
    start_date_obj = None
    end_date_obj = None
    
    # Validate start date
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, date_format).date()
        except ValueError:
            errors['start_date'] = f'تنسيق تاريخ البداية غير صحيح (المطلوب: {date_format})'
    
    # Validate end date
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, date_format).date()
        except ValueError:
            errors['end_date'] = f'تنسيق تاريخ النهاية غير صحيح (المطلوب: {date_format})'
    
    # Validate date range logic
    if start_date_obj and end_date_obj:
        if start_date_obj > end_date_obj:
            errors['date_range'] = 'تاريخ البداية يجب أن يكون قبل تاريخ النهاية'
        
        # Check for reasonable date range (not more than 1 year)
        if (end_date_obj - start_date_obj).days > 365:
            errors['date_range'] = 'نطاق التاريخ كبير جداً (أقصى سنة واحدة)'
    
    error_response_obj = validation_error_response(errors) if errors else None
    
    return start_date_obj, end_date_obj, error_response_obj

def validate_academic_year(academic_year: str) -> Tuple[bool, Optional[str]]:
    """
    Validate academic year format (e.g., '2023-2024')
    
    Args:
        academic_year: Academic year string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not academic_year:
        return False, 'السنة الأكاديمية مطلوبة'
    
    pattern = r'^\d{4}-\d{4}$'
    if not re.match(pattern, academic_year):
        return False, 'تنسيق السنة الأكاديمية غير صحيح (المطلوب: YYYY-YYYY)'
    
    try:
        start_year, end_year = map(int, academic_year.split('-'))
        if end_year != start_year + 1:
            return False, 'السنة الأكاديمية يجب أن تكون متتالية (مثال: 2023-2024)'
        
        current_year = datetime.now().year
        if start_year < current_year - 5 or start_year > current_year + 2:
            return False, 'السنة الأكاديمية خارج النطاق المسموح'
        
    except ValueError:
        return False, 'تنسيق السنة الأكاديمية غير صحيح'
    
    return True, None

def validate_section(section: str) -> Tuple[bool, Optional[str]]:
    """
    Validate section format (A, B, C)
    
    Args:
        section: Section string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not section:
        return False, 'الشعبة مطلوبة'
    
    valid_sections = ['A', 'B', 'C']
    if section.upper() not in valid_sections:
        return False, f'الشعبة يجب أن تكون إحدى: {", ".join(valid_sections)}'
    
    return True, None

def validate_study_year(study_year: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate study year (1-4)
    
    Args:
        study_year: Study year (can be string or int)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        year = int(study_year)
        if not (1 <= year <= 4):
            return False, 'السنة الدراسية يجب أن تكون بين 1 و 4'
        return True, None
    except (ValueError, TypeError):
        return False, 'السنة الدراسية يجب أن تكون رقم صحيح'

def validate_semester(semester: str) -> Tuple[bool, Optional[str]]:
    """
    Validate semester (first, second, summer)
    
    Args:
        semester: Semester string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not semester:
        return False, 'الفصل الدراسي مطلوب'
    
    valid_semesters = ['first', 'second', 'summer']
    if semester.lower() not in valid_semesters:
        return False, f'الفصل الدراسي يجب أن يكون إحدى: {", ".join(valid_semesters)}'
    
    return True, None

def validate_filters(filters: Dict[str, Any], allowed_filters: List[str]) -> Tuple[Dict[str, Any], Optional[Dict]]:
    """
    Validate and clean filter parameters
    
    Args:
        filters: Dictionary of filters
        allowed_filters: List of allowed filter keys
    
    Returns:
        tuple: (cleaned_filters, error_response)
    """
    errors = {}
    cleaned_filters = {}
    invalid_filters = []
    
    # Remove unexpected filters
    for key, value in filters.items():
        if key in allowed_filters:
            if value is not None and value != '':
                cleaned_filters[key] = value
        else:
            invalid_filters.append(key)
    
    if invalid_filters:
        errors['invalid_filters'] = {
            'fields': invalid_filters,
            'message': f'المرشحات التالية غير مدعومة: {", ".join(invalid_filters)}',
            'allowed_filters': allowed_filters
        }
    
    error_response_obj = validation_error_response(errors) if errors else None
    
    return cleaned_filters, error_response_obj

def validate_sort_params(sort_by: str = None, sort_order: str = None, allowed_fields: List[str] = None) -> Tuple[Optional[str], str, Optional[Dict]]:
    """
    Validate sorting parameters
    
    Args:
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        allowed_fields: List of allowed sort fields
    
    Returns:
        tuple: (sort_field, sort_direction, error_response)
    """
    errors = {}
    
    # Validate sort field
    if sort_by and allowed_fields and sort_by not in allowed_fields:
        errors['sort_by'] = f'الترتيب بـ {sort_by} غير مدعوم. الحقول المدعومة: {", ".join(allowed_fields)}'
        sort_by = None
    
    # Validate sort order
    sort_direction = 'asc'  # default
    if sort_order:
        if sort_order.lower() in ['asc', 'ascending']:
            sort_direction = 'asc'
        elif sort_order.lower() in ['desc', 'descending']:
            sort_direction = 'desc'
        else:
            errors['sort_order'] = 'اتجاه الترتيب يجب أن يكون asc أو desc'
    
    error_response_obj = validation_error_response(errors) if errors else None
    
    return sort_by, sort_direction, error_response_obj

def validate_bulk_operation_limit(items: List[Any], max_items: int = 100) -> Optional[Dict]:
    """
    Validate bulk operation size limits
    
    Args:
        items: List of items to process
        max_items: Maximum allowed items
    
    Returns:
        dict: Error response if limit exceeded, None if valid
    """
    if len(items) > max_items:
        return error_response(
            code='BULK_LIMIT_EXCEEDED',
            message=f'تجاوز الحد الأقصى للعملية الجماعية ({max_items} عنصر)',
            details={'items_count': len(items), 'max_allowed': max_items}
        )
    
    return None

def validate_ids_list(ids: List[Any], field_name: str = 'ids') -> Tuple[List[int], Optional[Dict]]:
    """
    Validate list of IDs
    
    Args:
        ids: List of ID values
        field_name: Name of the field for error messages
    
    Returns:
        tuple: (validated_ids, error_response)
    """
    if not ids:
        return [], validation_error_response({
            field_name: f'{field_name} قائمة مطلوبة وغير فارغة'
        })
    
    validated_ids = []
    invalid_ids = []
    
    for id_value in ids:
        try:
            validated_id = int(id_value)
            if validated_id <= 0:
                invalid_ids.append(str(id_value))
            else:
                validated_ids.append(validated_id)
        except (ValueError, TypeError):
            invalid_ids.append(str(id_value))
    
    if invalid_ids:
        return [], validation_error_response({
            field_name: f'قيم غير صحيحة في {field_name}: {", ".join(invalid_ids)}'
        })
    
    return validated_ids, None

# ============================================================================
# INPUT SANITIZATION - تنظيف المدخلات
# ============================================================================

class InputValidator:
    """Input validation and sanitization utilities"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """Clean and sanitize string input"""
        if not input_str:
            return ""
        
        # Remove HTML tags and dangerous characters
        cleaned = bleach.clean(input_str.strip(), tags=[], strip=True)
        return cleaned[:max_length]
    
    @staticmethod
    def validate_university_id(university_id: str) -> Tuple[bool, Optional[str]]:
        """Validate university ID format (e.g., CS2021001)"""
        if not university_id:
            return False, 'الرقم الجامعي مطلوب'
        
        pattern = r'^[A-Z]{2}\d{7}$'
        if not re.match(pattern, university_id):
            return False, 'تنسيق الرقم الجامعي غير صحيح (مثال: CS2021001)'
        
        return True, None
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email format"""
        if not email:
            return False, 'البريد الإلكتروني مطلوب'
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, 'تنسيق البريد الإلكتروني غير صحيح'
        
        return True, None
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
        """Validate phone number format"""
        if not phone:
            return True, None  # Phone is optional
        
        # Remove spaces and dashes
        clean_phone = re.sub(r'[\s-]', '', phone)
        
        # Check for valid international format
        pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(pattern, clean_phone):
            return False, 'تنسيق رقم الهاتف غير صحيح'
        
        return True, None
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append('كلمة المرور قصيرة جداً (أقل من 8 أحرف)')
        
        if not re.search(r'[A-Z]', password):
            errors.append('كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل')
        
        if not re.search(r'[a-z]', password):
            errors.append('كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل')
        
        if not re.search(r'\d', password):
            errors.append('كلمة المرور يجب أن تحتوي على رقم واحد على الأقل')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل')
        
        return len(errors) == 0, errors

# ============================================================================
# VALIDATION DECORATORS - مُزيِّنات التحقق
# ============================================================================

def validate_json_input(required_fields: List[str] = None):
    """Decorator to validate JSON input"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify(error_response('INVALID_INPUT', 'JSON body is required')), 400
            
            if required_fields:
                validation_error = validate_required_fields(data, required_fields)
                if validation_error:
                    return jsonify(validation_error), 400
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_query_params(**param_validators):
    """Decorator to validate query parameters"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            errors = {}
            
            for param_name, validator in param_validators.items():
                param_value = request.args.get(param_name)
                if param_value is not None:
                    is_valid, error_msg = validator(param_value)
                    if not is_valid:
                        errors[param_name] = error_msg
            
            if errors:
                return jsonify(validation_error_response(errors)), 400
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Response decorator for common patterns
def api_response(func):
    """Decorator to wrap function with standardized response handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # If function returns tuple, assume (data, status_code)
            if isinstance(result, tuple):
                data, status_code = result
                return success_response(data), status_code
            
            # If function returns dict with 'success' key, return as is
            if isinstance(result, dict) and 'success' in result:
                return result
            
            # Otherwise wrap in success response
            return success_response(result)
            
        except ValueError as e:
            return error_response('VALIDATION_ERROR', str(e)), 400
        except PermissionError as e:
            return forbidden_response(str(e)), 403
        except FileNotFoundError as e:
            return not_found_response('Resource', str(e)), 404
        except Exception as e:
            import logging
            logging.error(f'API error in {func.__name__}: {str(e)}', exc_info=True)
            return server_error_response(), 500
    
    return wrapper