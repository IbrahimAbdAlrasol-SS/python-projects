"""
Security Package Initialization
"""
from .jwt_manager import JWTManager, jwt_required, get_current_user
from .password_manager import PasswordManager
from .rbac import require_permission, check_permission
from .rate_limiter import setup_rate_limiting
from .input_validator import InputValidator
from .security_headers import setup_security_headers
from .account_lockout import AccountLockoutManager
from .setup_security import setup_complete_security

# Create alias for compatibility
init_security = setup_complete_security

__all__ = [
    'JWTManager', 'jwt_required', 'get_current_user',
    'PasswordManager', 'require_permission', 'check_permission',
    'setup_rate_limiting', 'InputValidator',
    'setup_security_headers', 'AccountLockoutManager',
    'init_security', 'setup_complete_security'
]