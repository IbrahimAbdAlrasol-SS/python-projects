"""
🔧 Response Helpers - مساعدات الاستجابات
Standardized API response helpers
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

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
        'timestamp': datetime.utcnow().isoformat()
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
        'previous_page': page - 1 if page > 1 else None
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
            'total_errors': len(field_errors)
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
        message=message
    )

def forbidden_response(message='صلاحيات غير كافية'):
    """Create forbidden error response"""
    return error_response(
        code='FORBIDDEN',
        message=message
    )

def rate_limit_response(retry_after=None):
    """Create rate limit exceeded error response"""
    details = {}
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
        message=message
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
            'success_rate': round((successful / len(results)) * 100, 2) if results else 0
        }
    
    return success_response(
        data={'results': results},
        meta={'batch_summary': summary}
    )

# Response decorators for common patterns
def api_response(func):
    """Decorator to wrap function with standardized response handling"""
    from functools import wraps
    
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