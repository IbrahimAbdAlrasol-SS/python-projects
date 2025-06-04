"""
Models Package Initialization - COMPLETE VERSION
استيراد جميع النماذج بالترتيب الصحيح مع جميع العلاقات
"""

# Import base models first
from .base import BaseModel

# Import enums and basic models (no dependencies)
from .users import User, UserRole
from .subjects import Subject, SemesterEnum
from .rooms import Room, RoomTypeEnum

# Import models with foreign keys to basic models
from .students import Student, SectionEnum, StudyTypeEnum, AcademicStatusEnum
from .teachers import Teacher, AcademicDegreeEnum

# Import complex models with multiple dependencies
from .schedules import Schedule, DayOfWeekEnum
from .lectures import Lecture, LectureStatusEnum
from .qr_sessions import QRSession, QRStatusEnum
from .attendance_records import AttendanceRecord, AttendanceTypeEnum, VerificationStepEnum, AttendanceStatusEnum

# Import assignment-related models
from .assignments import Assignment, AssignmentStatusEnum, AssignmentTypeEnum
from .submissions import Submission, SubmissionStatusEnum, SubmissionTypeEnum

# Import system models
from .notifications import Notification, NotificationTypeEnum, NotificationPriorityEnum, NotificationStatusEnum, NotificationChannelEnum
from .student_counters import StudentCounter, CounterActionEnum, CounterStatusEnum
from .system_settings import SystemSetting, SettingTypeEnum, SettingCategoryEnum

# Export all models and enums
__all__ = [
    # Base
    'BaseModel',
    
    # Core Models
    'User', 'Student', 'Teacher', 'Subject', 'Room',
    
    # Academic Models  
    'Schedule', 'Lecture', 'QRSession', 'AttendanceRecord',
    
    # Assignment Models
    'Assignment', 'Submission',
    
    # System Models
    'Notification', 'StudentCounter', 'SystemSetting',
    
    # User Enums
    'UserRole',
    
    # Student Enums
    'SectionEnum', 'StudyTypeEnum', 'AcademicStatusEnum',
    
    # Teacher Enums
    'AcademicDegreeEnum',
    
    # Subject Enums
    'SemesterEnum',
    
    # Room Enums
    'RoomTypeEnum',
    
    # Schedule Enums
    'DayOfWeekEnum',
    
    # Lecture Enums
    'LectureStatusEnum',
    
    # QR Session Enums
    'QRStatusEnum',
    
    # Attendance Enums
    'AttendanceTypeEnum', 'VerificationStepEnum', 'AttendanceStatusEnum',
    
    # Assignment Enums
    'AssignmentStatusEnum', 'AssignmentTypeEnum',
    
    # Submission Enums
    'SubmissionStatusEnum', 'SubmissionTypeEnum',
    
    # Notification Enums
    'NotificationTypeEnum', 'NotificationPriorityEnum', 'NotificationStatusEnum', 'NotificationChannelEnum',
    
    # Counter Enums
    'CounterActionEnum', 'CounterStatusEnum',
    
    # System Setting Enums
    'SettingTypeEnum', 'SettingCategoryEnum'
]

# Post-import setup for relationships and foreign keys
def setup_model_relationships():
    """Setup additional relationships after all models are imported"""
    
    # Add any additional relationships that couldn't be defined in the models directly
    # due to circular import issues
    
    # User relationships
    User.student_profile = db.relationship('Student', uselist=False, back_populates='user')
    User.teacher_profile = db.relationship('Teacher', uselist=False, back_populates='user')
    
    # Student relationships
    Student.user = db.relationship('User', back_populates='student_profile')
    
    # Teacher relationships  
    Teacher.user = db.relationship('User', back_populates='teacher_profile')
    
    print("✅ Model relationships setup completed")

# Auto-setup relationships when module is imported
try:
    from config.database import db
    # Note: Actual relationship setup should be done after app context is available
    # This is just a placeholder for the setup function
except ImportError:
    # Database not available during import
    pass

def validate_all_models():
    """Validate all model definitions"""
    validation_results = {}
    
    models_to_validate = [
        User, Student, Teacher, Subject, Room, Schedule, 
        Lecture, QRSession, AttendanceRecord, Assignment, 
        Submission, Notification, StudentCounter, SystemSetting
    ]
    
    for model in models_to_validate:
        try:
            # Check if model has required attributes
            required_attrs = ['__tablename__', 'id']
            missing_attrs = [attr for attr in required_attrs if not hasattr(model, attr)]
            
            if missing_attrs:
                validation_results[model.__name__] = {
                    'valid': False,
                    'errors': [f'Missing required attributes: {missing_attrs}']
                }
            else:
                validation_results[model.__name__] = {
                    'valid': True,
                    'table_name': model.__tablename__,
                    'columns': len([attr for attr in dir(model) if hasattr(getattr(model, attr), 'type')]),
                    'relationships': len([attr for attr in dir(model) if hasattr(getattr(model, attr), 'mapper')])
                }
        except Exception as e:
            validation_results[model.__name__] = {
                'valid': False,
                'errors': [str(e)]
            }
    
    return validation_results

def get_model_statistics():
    """Get statistics about all models"""
    stats = {
        'total_models': len(__all__),
        'core_models': 5,  # User, Student, Teacher, Subject, Room
        'academic_models': 4,  # Schedule, Lecture, QRSession, AttendanceRecord
        'assignment_models': 2,  # Assignment, Submission
        'system_models': 3,  # Notification, StudentCounter, SystemSetting
        'total_enums': len([item for item in __all__ if 'Enum' in item]),
        'model_dependencies': {
            'User': [],  # No dependencies
            'Subject': [],  # No dependencies
            'Room': [],  # No dependencies
            'Student': ['User'],
            'Teacher': ['User'],
            'Schedule': ['Subject', 'Teacher', 'Room'],
            'Lecture': ['Schedule'],
            'QRSession': ['Lecture', 'Teacher'],
            'AttendanceRecord': ['Student', 'Lecture', 'QRSession'],
            'Assignment': ['Subject', 'Teacher'],
            'Submission': ['Assignment', 'Student'],
            'Notification': ['User', 'Student', 'Teacher'],
            'StudentCounter': ['Student', 'Subject'],
            'SystemSetting': ['User']
        }
    }
    
    return stats

# Model creation order for database migrations
MODEL_CREATION_ORDER = [
    # Level 1: No dependencies
    'User',
    'Subject', 
    'Room',
    
    # Level 2: Depend on Level 1
    'Student',
    'Teacher',
    'SystemSetting',
    
    # Level 3: Depend on Level 2
    'Schedule',
    'Assignment',
    'StudentCounter',
    
    # Level 4: Depend on Level 3
    'Lecture',
    'Notification',
    
    # Level 5: Depend on Level 4
    'QRSession',
    'Submission',
    
    # Level 6: Depend on Level 5
    'AttendanceRecord'
]

def create_all_tables_in_order(db):
    """Create all tables in the correct dependency order"""
    print("🗄️ Creating database tables in dependency order...")
    
    try:
        # Create all tables (SQLAlchemy handles dependencies automatically)
        db.create_all()
        print("✅ All tables created successfully")
        
        # Validate creation
        validation_results = validate_all_models()
        valid_models = sum(1 for result in validation_results.values() if result.get('valid', False))
        total_models = len(validation_results)
        
        print(f"📊 Model validation: {valid_models}/{total_models} models valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def print_model_summary():
    """Print summary of all models"""
    stats = get_model_statistics()
    
    print("\n📋 Smart Attendance System - Model Summary")
    print("=" * 50)
    print(f"📊 Total Models: {stats['total_models']}")
    print(f"🏗️ Core Models: {stats['core_models']}")
    print(f"🎓 Academic Models: {stats['academic_models']}")
    print(f"📝 Assignment Models: {stats['assignment_models']}")
    print(f"⚙️ System Models: {stats['system_models']}")
    print(f"🔧 Total Enums: {stats['total_enums']}")
    print("\n✅ All models imported successfully!")
    print("🚀 Ready for database creation and migration")
    print("=" * 50)

# Auto-print summary when in development mode
import os
if os.getenv('FLASK_ENV') == 'development':
    try:
        print_model_summary()
    except:
        pass  # Silently fail if there are issues during import