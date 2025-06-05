"""
🔧 Validation Helpers - مساعدات التحقق
Input validation utilities for APIs
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
import re

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Optional[Dict[str, Any]]:
    """
    Validate that all required fields are present and not empty
    
    Args:
        data: Input data dictionary
        required_fields: List of required field names
    
    Returns:
        dict: Error response if validation fails, None if success
    """
    from utils.response_helpers import validation_error_response
    
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
    from utils.response_helpers import validation_error_response
    
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
    
    error_response = validation_error_response(errors) if errors else None
    
    return normalized_page, normalized_limit, error_response

def validate_date_range(start_date: str = None, end_date: str = None, date_format: str = '%Y-%m-%d') -> Tuple[Optional[date], Optional[date], Optional[Dict]]:
    """
    Validate date range parameters
    
    Args:
        start_date: Start date string
        end_date: End date string
        date_format: Expected date format
    
    Returns:
        tuple: (start_date_obj, end_date_obj, error_response)
    """
    from utils.response_helpers import validation_error_response
    
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
    
    error_response = validation_error_response(errors) if errors else None
    
    return start_date_obj, end_date_obj, error_response

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
    from utils.response_helpers import validation_error_response
    
    errors = {}
    cleaned_filters = {}
    
    # Remove unexpected filters
    for key, value in filters.items():
        if key in allowed_filters:
            if value is not None and value != '':
                cleaned_filters[key] = value
        else:
            if 'invalid_filters' not in errors:
                errors['invalid_filters'] = []
            errors['invalid_filters'].append(key)
    
    if errors.get('invalid_filters'):
        errors['invalid_filters'] = {
            'fields': errors['invalid_filters'],
            'message': f'المرشحات التالية غير مدعومة: {", ".join(errors["invalid_filters"])}',
            'allowed_filters': allowed_filters
        }
    
    error_response = validation_error_response(errors) if errors else None
    
    return cleaned_filters, error_response

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
    from utils.response_helpers import validation_error_response
    
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
    
    error_response = validation_error_response(errors) if errors else None
    
    return sort_by, sort_direction, error_response

def validate_bulk_operation_limit(items: List[Any], max_items: int = 100) -> Optional[Dict]:
    """
    Validate bulk operation size limits
    
    Args:
        items: List of items to process
        max_items: Maximum allowed items
    
    Returns:
        dict: Error response if limit exceeded, None if valid
    """
    from utils.response_helpers import error_response
    
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
    from utils.response_helpers import validation_error_response
    
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

# Validation decorators
def validate_json_input(required_fields: List[str] = None):
    """Decorator to validate JSON input"""
    def decorator(func):
        from functools import wraps
        from flask import request, jsonify
        
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
        from functools import wraps
        from flask import request, jsonify
        
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
                from utils.response_helpers import validation_error_response
                return jsonify(validation_error_response(errors)), 400
            
            return func(*args, **kwargs)
        return wrapper
    return decorator