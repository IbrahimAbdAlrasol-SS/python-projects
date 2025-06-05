"""
📄 Response Helpers - نظام الاستجابات الموحد
Standardized response format for all API endpoints
نظام موحد لجميع استجابات الـ APIs
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import json

@dataclass
class APIResponse:
    """Standardized API response structure"""
    success: bool
    message: str = ""
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    pagination: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + 'Z'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        result = {
            'success': self.success,
            'timestamp': self.timestamp
        }
        
        if self.message:
            result['message'] = self.message
        
        if self.data is not None:
            result['data'] = self.data
        
        if self.error is not None:
            result['error'] = self.error
        
        if self.pagination is not None:
            result['pagination'] = self.pagination
        
        if self.meta is not None:
            result['meta'] = self.meta
            
        return result

def success_response(
    data: Optional[Any] = None,
    message: str = "تم تنفيذ العملية بنجاح",
    pagination: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate successful response
    
    Args:
        data: Response data (can be dict, list, or primitive)
        message: Success message in Arabic
        pagination: Pagination info for list endpoints
        meta: Additional metadata
    
    Returns:
        Standardized success response dictionary
    """
    response = APIResponse(
        success=True,
        message=message,
        data=data,
        pagination=pagination,
        meta=meta
    )
    return response.to_dict()

def error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate error response
    
    Args:
        code: Error code (e.g., 'INVALID_INPUT', 'USER_NOT_FOUND')
        message: Error message in Arabic
        details: Additional error details
        status_code: HTTP status code for logging
    
    Returns:
        Standardized error response dictionary
    """
    error_data = {
        'code': code,
        'message': message
    }
    
    if details:
        error_data['details'] = details
    
    if status_code:
        error_data['status_code'] = status_code
    
    response = APIResponse(
        success=False,
        error=error_data
    )
    return response.to_dict()

def validation_error_response(
    validation_errors: Dict[str, List[str]],
    message: str = "بيانات غير صحيحة"
) -> Dict[str, Any]:
    """
    Generate validation error response
    
    Args:
        validation_errors: Field-specific validation errors
        message: General validation message
    
    Returns:
        Standardized validation error response
    """
    return error_response(
        code='VALIDATION_ERROR',
        message=message,
        details={
            'validation_errors': validation_errors,
            'fields_with_errors': list(validation_errors.keys())
        }
    )

def not_found_response(
    resource_type: str,
    resource_id: Optional[Union[str, int]] = None
) -> Dict[str, Any]:
    """
    Generate not found error response
    
    Args:
        resource_type: Type of resource (e.g., 'طالب', 'مدرس', 'قاعة')
        resource_id: ID of the resource that wasn't found
    
    Returns:
        Standardized not found response
    """
    message = f"{resource_type} غير موجود"
    if resource_id:
        message += f" (ID: {resource_id})"
    
    return error_response(
        code='NOT_FOUND',
        message=message,
        details={'resource_type': resource_type, 'resource_id': resource_id}
    )

def unauthorized_response(
    message: str = "غير مصرح لك بالوصول لهذا المورد"
) -> Dict[str, Any]:
    """Generate unauthorized access response"""
    return error_response(
        code='UNAUTHORIZED',
        message=message
    )

def forbidden_response(
    message: str = "ليس لديك صلاحية لتنفيذ هذه العملية"
) -> Dict[str, Any]:
    """Generate forbidden access response"""
    return error_response(
        code='FORBIDDEN',
        message=message
    )

def paginated_response(
    items: List[Any],
    page: int,
    limit: int,
    total_count: int,
    message: str = "تم جلب البيانات بنجاح",
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate paginated response
    
    Args:
        items: List of items for current page
        page: Current page number (1-based)
        limit: Items per page
        total_count: Total number of items
        message: Success message
        additional_data: Additional data to include in response
    
    Returns:
        Standardized paginated response
    """
    total_pages = (total_count + limit - 1) // limit  # Ceiling division
    
    pagination = {
        'current_page': page,
        'per_page': limit,
        'total_pages': total_pages,
        'total_count': total_count,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'next_page': page + 1 if page < total_pages else None,
        'prev_page': page - 1 if page > 1 else None
    }
    
    # Prepare response data
    response_data = {
        'items': items,
        'count': len(items)
    }
    
    # Add additional data if provided
    if additional_data:
        response_data.update(additional_data)
    
    return success_response(
        data=response_data,
        message=message,
        pagination=pagination
    )

def batch_response(
    results: List[Dict[str, Any]],
    summary: Dict[str, Any],
    message: str = "تم معالجة العملية الجماعية"
) -> Dict[str, Any]:
    """
    Generate batch operation response
    
    Args:
        results: List of individual operation results
        summary: Summary statistics
        message: Success message
    
    Returns:
        Standardized batch response
    """
    return success_response(
        data={
            'results': results,
            'summary': summary
        },
        message=message,
        meta={
            'batch_size': len(results),
            'operation_type': 'batch',
            'success_rate': summary.get('success_rate', 0)
        }
    )

def health_response(
    status: str,
    services: Dict[str, Any],
    overall_health: float = 100.0
) -> Dict[str, Any]:
    """
    Generate health check response
    
    Args:
        status: Overall status ('healthy', 'degraded', 'unhealthy')
        services: Individual service statuses
        overall_health: Overall health percentage
    
    Returns:
        Standardized health response
    """
    return success_response(
        data={
            'status': status,
            'health_score': overall_health,
            'services': services
        },
        message=f"حالة النظام: {status}",
        meta={
            'check_type': 'health',
            'services_count': len(services),
            'healthy_services': sum(1 for s in services.values() if s.get('status') == 'healthy')
        }
    )

class ResponseHelper:
    """Helper class for common response patterns"""
    
    @staticmethod
    def created_response(
        resource_data: Dict[str, Any],
        resource_type: str = "المورد",
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Response for successful resource creation"""
        if not message:
            message = f"تم إنشاء {resource_type} بنجاح"
        
        return success_response(
            data=resource_data,
            message=message,
            meta={'operation': 'create', 'resource_type': resource_type}
        )
    
    @staticmethod
    def updated_response(
        resource_data: Dict[str, Any],
        resource_type: str = "المورد",
        changes_count: int = 0,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Response for successful resource update"""
        if not message:
            message = f"تم تحديث {resource_type} بنجاح"
            if changes_count > 0:
                message += f" ({changes_count} تغيير)"
        
        return success_response(
            data=resource_data,
            message=message,
            meta={
                'operation': 'update',
                'resource_type': resource_type,
                'changes_count': changes_count
            }
        )
    
    @staticmethod
    def deleted_response(
        resource_id: Union[str, int],
        resource_type: str = "المورد",
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Response for successful resource deletion"""
        if not message:
            message = f"تم حذف {resource_type} بنجاح"
        
        return success_response(
            data={'deleted_id': resource_id},
            message=message,
            meta={'operation': 'delete', 'resource_type': resource_type}
        )
    
    @staticmethod
    def conflict_response(
        message: str = "تعارض في البيانات",
        conflicts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Response for data conflicts"""
        details = {}
        if conflicts:
            details['conflicts'] = conflicts
            details['conflicts_count'] = len(conflicts)
        
        return error_response(
            code='CONFLICT',
            message=message,
            details=details
        )
    
    @staticmethod
    def rate_limit_response(
        retry_after: int = 60,
        message: str = "تم تجاوز الحد المسموح من الطلبات"
    ) -> Dict[str, Any]:
        """Response for rate limit exceeded"""
        return error_response(
            code='RATE_LIMIT_EXCEEDED',
            message=message,
            details={
                'retry_after_seconds': retry_after,
                'retry_after_formatted': f"{retry_after} ثانية"
            }
        )

# Export commonly used functions
__all__ = [
    'success_response',
    'error_response', 
    'validation_error_response',
    'not_found_response',
    'unauthorized_response',
    'forbidden_response',
    'paginated_response',
    'batch_response',
    'health_response',
    'ResponseHelper'
]