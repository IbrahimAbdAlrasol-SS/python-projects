"""
Models Package Initialization
تهيئة جميع النماذج وتصديرها - FIXED VERSION
"""

# Import all models in correct order to avoid circular imports
from .users import User, UserRole
from .students import Student, SectionEnum, StudyTypeEnum, AcademicStatusEnum
from .teachers import Teacher, AcademicDegreeEnum
from .subjects import Subject, SemesterEnum
from .rooms import Room, RoomTypeEnum

# Import remaining models (placeholders for now)
# These will be implemented in subsequent iterations

# Export all models and enums
__all__ = [
    # Core Models
    'User',
    'Student', 
    'Teacher',
    'Subject',
    'Room',
    
    # Enums
    'UserRole',
    'SectionEnum',
    'StudyTypeEnum', 
    'AcademicStatusEnum',
    'AcademicDegreeEnum',
    'SemesterEnum',
    'RoomTypeEnum'
]

# Configure relationships after all models are imported
def configure_relationships():
    """Configure database relationships between models"""
    
    # User relationships
    User.student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    User.teacher_profile = db.relationship('Teacher', backref='user', uselist=False, cascade='all, delete-orphan')

# Import database instance
from config.database import db

# Configure relationships
configure_relationships()