"""
SYSTEM_SETTINGS Model - نموذج إعدادات النظام
نموذج كامل لإدارة إعدادات النظام والتكوين
"""

from config.database import db
from .base import BaseModel
from enum import Enum
from datetime import datetime
from sqlalchemy import CheckConstraint, Index, UniqueConstraint
import json

class SettingTypeEnum(Enum):
    """نوع الإعداد"""
    STRING = 'string'
    INTEGER = 'integer'
    FLOAT = 'float'
    BOOLEAN = 'boolean'
    JSON = 'json'
    EMAIL = 'email'
    URL = 'url'
    PASSWORD = 'password'
    TIME = 'time'
    DATE = 'date'

class SettingCategoryEnum(Enum):
    """فئة الإعداد"""
    GENERAL = 'general'                 # عام
    ATTENDANCE = 'attendance'           # الحضور
    SECURITY = 'security'              # الأمان
    NOTIFICATIONS = 'notifications'     # الإشعارات
    EMAIL = 'email'                    # البريد الإلكتروني
    SMS = 'sms'                        # الرسائل النصية
    TELEGRAM = 'telegram'              # تيليجرام
    ACADEMIC = 'academic'              # أكاديمي
    GRADING = 'grading'                # التقييم
    BACKUP = 'backup'                  # النسخ الاحتياطية
    PERFORMANCE = 'performance'         # الأداء
    LOGGING = 'logging'                # السجلات

class SystemSetting(BaseModel):
    """System settings model for application configuration"""
    
    __tablename__ = 'system_settings'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Setting Identification
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Setting Value
    value = db.Column(db.Text, nullable=True)
    default_value = db.Column(db.Text, nullable=True)
    
    # Setting Type and Validation
    setting_type = db.Column(db.Enum(SettingTypeEnum), default=SettingTypeEnum.STRING, nullable=False)
    category = db.Column(db.Enum(SettingCategoryEnum), default=SettingCategoryEnum.GENERAL, nullable=False, index=True)
    
    # Validation Rules
    validation_rules = db.Column(db.JSON, nullable=True)  # min_length, max_length, min_value, max_value, etc.
    allowed_values = db.Column(db.JSON, nullable=True)    # List of allowed values for enum-like settings
    
    # Access Control
    is_public = db.Column(db.Boolean, default=False, index=True)  # Can be read by non-admin users
    is_readonly = db.Column(db.Boolean, default=False)           # Cannot be modified through UI
    requires_restart = db.Column(db.Boolean, default=False)      # Requires system restart to take effect
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_system_setting = db.Column(db.Boolean, default=False)     # Core system setting
    
    # Change Tracking
    last_modified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    change_history = db.Column(db.JSON, nullable=True)  # History of changes
    
    # UI Configuration
    ui_order = db.Column(db.Integer, default=0)  # Display order in admin interface
    ui_group = db.Column(db.String(100), nullable=True)  # Group in admin interface
    ui_widget = db.Column(db.String(50), nullable=True)  # text, textarea, select, checkbox, etc.
    ui_help_text = db.Column(db.Text, nullable=True)
    
    # Relationships
    last_modifier = db.relationship('User', backref='modified_settings', lazy='select')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('ui_order >= 0', name='check_ui_order_non_negative'),
        Index('idx_setting_category_active', 'category', 'is_active'),
        Index('idx_setting_public', 'is_public', 'is_active'),
        Index('idx_setting_ui_order', 'ui_group', 'ui_order'),
    )
    
    def get_typed_value(self):
        """Get value converted to appropriate Python type"""
        if self.value is None:
            return self.get_typed_default_value()
        
        try:
            if self.setting_type == SettingTypeEnum.STRING:
                return str(self.value)
            elif self.setting_type == SettingTypeEnum.INTEGER:
                return int(self.value)
            elif self.setting_type == SettingTypeEnum.FLOAT:
                return float(self.value)
            elif self.setting_type == SettingTypeEnum.BOOLEAN:
                return str(self.value).lower() in ('true', '1', 'yes', 'on')
            elif self.setting_type == SettingTypeEnum.JSON:
                return json.loads(self.value) if self.value else {}
            elif self.setting_type in [SettingTypeEnum.EMAIL, SettingTypeEnum.URL, SettingTypeEnum.PASSWORD]:
                return str(self.value)
            elif self.setting_type == SettingTypeEnum.TIME:
                from datetime import time
                return datetime.strptime(self.value, '%H:%M:%S').time()
            elif self.setting_type == SettingTypeEnum.DATE:
                return datetime.strptime(self.value, '%Y-%m-%d').date()
            else:
                return str(self.value)
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.get_typed_default_value()
    
    def get_typed_default_value(self):
        """Get default value converted to appropriate Python type"""
        if self.default_value is None:
            # Return type-appropriate defaults
            if self.setting_type == SettingTypeEnum.STRING:
                return ""
            elif self.setting_type == SettingTypeEnum.INTEGER:
                return 0
            elif self.setting_type == SettingTypeEnum.FLOAT:
                return 0.0
            elif self.setting_type == SettingTypeEnum.BOOLEAN:
                return False
            elif self.setting_type == SettingTypeEnum.JSON:
                return {}
            else:
                return ""
        
        # Convert default value using the same logic as get_typed_value
        old_value = self.value
        self.value = self.default_value
        result = self.get_typed_value()
        self.value = old_value
        return result
    
    def set_value(self, new_value, modified_by_user_id=None):
        """Set value with validation and change tracking"""
        # Validate the new value
        is_valid, error_message = self.validate_value(new_value)
        if not is_valid:
            raise ValueError(f"Invalid value for setting '{self.key}': {error_message}")
        
        # Store old value for history
        old_value = self.value
        
        # Convert value to string for storage
        if self.setting_type == SettingTypeEnum.JSON:
            new_value_str = json.dumps(new_value) if new_value is not None else None
        elif self.setting_type == SettingTypeEnum.BOOLEAN:
            new_value_str = 'true' if new_value else 'false'
        else:
            new_value_str = str(new_value) if new_value is not None else None
        
        # Update value
        self.value = new_value_str
        self.last_modified_by = modified_by_user_id
        self.last_modified_at = datetime.utcnow()
        
        # Add to change history
        self._add_to_history(old_value, new_value_str, modified_by_user_id)
        
        self.save()
    
    def validate_value(self, value):
        """Validate setting value"""
        if value is None:
            return True, None
        
        # Type validation
        try:
            if self.setting_type == SettingTypeEnum.INTEGER:
                int_value = int(value)
                value = int_value
            elif self.setting_type == SettingTypeEnum.FLOAT:
                float_value = float(value)
                value = float_value
            elif self.setting_type == SettingTypeEnum.BOOLEAN:
                if not isinstance(value, bool):
                    if str(value).lower() not in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
                        return False, "Invalid boolean value"
            elif self.setting_type == SettingTypeEnum.JSON:
                if isinstance(value, str):
                    json.loads(value)
                elif not isinstance(value, (dict, list)):
                    return False, "Value must be valid JSON"
            elif self.setting_type == SettingTypeEnum.EMAIL:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, str(value)):
                    return False, "Invalid email format"
            elif self.setting_type == SettingTypeEnum.URL:
                import re
                url_pattern = r'^https?://.+\..+'
                if not re.match(url_pattern, str(value)):
                    return False, "Invalid URL format"
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return False, f"Type conversion error: {str(e)}"
        
        # Allowed values validation
        if self.allowed_values and value not in self.allowed_values:
            return False, f"Value must be one of: {', '.join(map(str, self.allowed_values))}"
        
        # Validation rules
        if self.validation_rules:
            rules = self.validation_rules
            
            # String length validation
            if 'min_length' in rules and len(str(value)) < rules['min_length']:
                return False, f"Value must be at least {rules['min_length']} characters long"
            
            if 'max_length' in rules and len(str(value)) > rules['max_length']:
                return False, f"Value must be no more than {rules['max_length']} characters long"
            
            # Numeric range validation
            if self.setting_type in [SettingTypeEnum.INTEGER, SettingTypeEnum.FLOAT]:
                if 'min_value' in rules and value < rules['min_value']:
                    return False, f"Value must be at least {rules['min_value']}"
                
                if 'max_value' in rules and value > rules['max_value']:
                    return False, f"Value must be no more than {rules['max_value']}"
            
            # Pattern validation
            if 'pattern' in rules:
                import re
                if not re.match(rules['pattern'], str(value)):
                    return False, f"Value does not match required pattern"
        
        return True, None
    
    def _add_to_history(self, old_value, new_value, modified_by_user_id):
        """Add change to history"""
        if not self.change_history:
            self.change_history = []
        
        change_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'old_value': old_value,
            'new_value': new_value,
            'modified_by': modified_by_user_id
        }
        
        self.change_history.append(change_entry)
        
        # Keep only last 50 changes
        if len(self.change_history) > 50:
            self.change_history = self.change_history[-50:]
    
    def reset_to_default(self, modified_by_user_id=None):
        """Reset setting to default value"""
        self.set_value(self.get_typed_default_value(), modified_by_user_id)
    
    def to_dict(self, include_sensitive=False, include_history=False):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Add enum values
        data['setting_type'] = self.setting_type.value if self.setting_type else None
        data['category'] = self.category.value if self.category else None
        
        # Add typed value
        data['typed_value'] = self.get_typed_value()
        data['typed_default_value'] = self.get_typed_default_value()
        
        # Format timestamps
        if self.last_modified_at:
            data['last_modified_at'] = self.last_modified_at.isoformat()
        
        # Remove sensitive data by default
        if not include_sensitive and self.setting_type == SettingTypeEnum.PASSWORD:
            data['value'] = '*' * 8 if self.value else None
            data['typed_value'] = '*' * 8 if self.value else None
        
        # Include change history if requested
        if not include_history:
            data.pop('change_history', None)
        
        return data
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get setting value by key"""
        setting = cls.query.filter_by(key=key, is_active=True).first()
        if setting:
            return setting.get_typed_value()
        return default
    
    @classmethod
    def set_setting(cls, key, value, modified_by_user_id=None):
        """Set setting value by key"""
        setting = cls.query.filter_by(key=key).first()
        if not setting:
            raise ValueError(f"Setting '{key}' not found")
        
        setting.set_value(value, modified_by_user_id)
        return setting
    
    @classmethod
    def get_settings_by_category(cls, category, public_only=False):
        """Get all settings in a category"""
        query = cls.query.filter_by(category=category, is_active=True)
        
        if public_only:
            query = query.filter_by(is_public=True)
        
        return query.order_by(cls.ui_order, cls.name).all()
    
    @classmethod
    def get_public_settings(cls):
        """Get all public settings"""
        return cls.query.filter_by(is_public=True, is_active=True).all()
    
    @classmethod
    def create_setting(cls, key, name, setting_type, category, default_value=None, **kwargs):
        """Create a new setting"""
        setting = cls(
            key=key,
            name=name,
            setting_type=setting_type,
            category=category,
            default_value=str(default_value) if default_value is not None else None,
            value=str(default_value) if default_value is not None else None,
            **kwargs
        )
        
        setting.save()
        return setting
    
    @classmethod
    def initialize_default_settings(cls):
        """Initialize default system settings"""
        default_settings = [
            # General Settings
            {
                'key': 'system_name',
                'name': 'اسم النظام',
                'setting_type': SettingTypeEnum.STRING,
                'category': SettingCategoryEnum.GENERAL,
                'default_value': 'نظام الحضور الذكي',
                'description': 'اسم النظام الذي يظهر في واجهة المستخدم',
                'is_public': True
            },
            {
                'key': 'system_version',
                'name': 'إصدار النظام',
                'setting_type': SettingTypeEnum.STRING,
                'category': SettingCategoryEnum.GENERAL,
                'default_value': '1.0.0',
                'description': 'رقم إصدار النظام',
                'is_public': True,
                'is_readonly': True
            },
            {
                'key': 'university_name',
                'name': 'اسم الجامعة',
                'setting_type': SettingTypeEnum.STRING,
                'category': SettingCategoryEnum.GENERAL,
                'default_value': 'الجامعة العراقية',
                'description': 'اسم الجامعة أو المؤسسة التعليمية',
                'is_public': True
            },
            
            # Attendance Settings
            {
                'key': 'attendance_window_minutes',
                'name': 'نافذة الحضور (دقائق)',
                'setting_type': SettingTypeEnum.INTEGER,
                'category': SettingCategoryEnum.ATTENDANCE,
                'default_value': '15',
                'description': 'المدة المسموحة لتسجيل الحضور بعد بداية المحاضرة',
                'validation_rules': {'min_value': 1, 'max_value': 60}
            },
            {
                'key': 'late_threshold_minutes',
                'name': 'حد التأخير (دقائق)',
                'setting_type': SettingTypeEnum.INTEGER,
                'category': SettingCategoryEnum.ATTENDANCE,
                'default_value': '5',
                'description': 'المدة التي بعدها يعتبر الطالب متأخراً',
                'validation_rules': {'min_value': 0, 'max_value': 30}
            },
            {
                'key': 'qr_code_duration_seconds',
                'name': 'مدة صلاحية QR (ثواني)',
                'setting_type': SettingTypeEnum.INTEGER,
                'category': SettingCategoryEnum.ATTENDANCE,
                'default_value': '300',
                'description': 'مدة صلاحية رمز QR للحضور',
                'validation_rules': {'min_value': 30, 'max_value': 1800}
            },
            
            # Security Settings
            {
                'key': 'max_login_attempts',
                'name': 'محاولات تسجيل الدخول القصوى',
                'setting_type': SettingTypeEnum.INTEGER,
                'category': SettingCategoryEnum.SECURITY,
                'default_value': '5',
                'description': 'عدد محاولات تسجيل الدخول الفاشلة قبل قفل الحساب',
                'validation_rules': {'min_value': 3, 'max_value': 10}
            },
            {
                'key': 'account_lockout_duration_minutes',
                'name': 'مدة قفل الحساب (دقائق)',
                'setting_type': SettingTypeEnum.INTEGER,
                'category': SettingCategoryEnum.SECURITY,
                'default_value': '15',
                'description': 'مدة قفل الحساب بعد المحاولات الفاشلة',
                'validation_rules': {'min_value': 5, 'max_value': 60}
            },
            {
                'key': 'jwt_expiry_hours',
                'name': 'انتهاء صلاحية JWT (ساعات)',
                'setting_type': SettingTypeEnum.INTEGER,
                'category': SettingCategoryEnum.SECURITY,
                'default_value': '2',
                'description': 'مدة صلاحية رموز JWT',
                'validation_rules': {'min_value': 1, 'max_value': 24}
            },
            
            # Email Settings
            {
                'key': 'smtp_server',
                'name': 'خادم SMTP',
                'setting_type': SettingTypeEnum.STRING,
                'category': SettingCategoryEnum.EMAIL,
                'default_value': 'smtp.gmail.com',
                'description': 'عنوان خادم البريد الإلكتروني'
            },
            {
                'key': 'smtp_port',
                'name': 'منفذ SMTP',
                'setting_type': SettingTypeEnum.INTEGER,
                'category': SettingCategoryEnum.EMAIL,
                'default_value': '587',
                'description': 'منفذ خادم البريد الإلكتروني',
                'validation_rules': {'min_value': 1, 'max_value': 65535}
            },
            
            # Grading Settings
            {
                'key': 'grade_scale',
                'name': 'سلم الدرجات',
                'setting_type': SettingTypeEnum.JSON,
                'category': SettingCategoryEnum.GRADING,
                'default_value': '{"A+": 90, "A": 85, "B+": 80, "B": 75, "C+": 70, "C": 65, "D+": 60, "D": 55, "F": 0}',
                'description': 'سلم تحويل الدرجات إلى حروف'
            }
        ]
        
        created_count = 0
        for setting_data in default_settings:
            existing = cls.query.filter_by(key=setting_data['key']).first()
            if not existing:
                setting = cls(**setting_data)
                setting.save()
                created_count += 1
        
        return created_count
    
    def validate_system_setting(self):
        """Validate system setting data"""
        errors = []
        
        # Check required fields
        if not self.key or len(self.key.strip()) < 1:
            errors.append("Setting key is required")
        
        if not self.name or len(self.name.strip()) < 1:
            errors.append("Setting name is required")
        
        # Check key format (alphanumeric and underscores only)
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', self.key):
            errors.append("Setting key must start with letter and contain only letters, numbers, and underscores")
        
        # Validate current value
        if self.value is not None:
            is_valid, error_message = self.validate_value(self.get_typed_value())
            if not is_valid:
                errors.append(f"Current value is invalid: {error_message}")
        
        return errors
    
    def save(self):
        """Save with validation"""
        errors = self.validate_system_setting()
        if errors:
            raise ValueError(f"System setting validation failed: {', '.join(errors)}")
        
        return super().save()
    
    def __repr__(self):
        return f'<SystemSetting {self.key}: {self.name}>'