"""
Models Package Initialization - ULTIMATE FIX
"""

# Import models in correct order
from .users import User, UserRole
from .students import Student, SectionEnum, StudyTypeEnum, AcademicStatusEnum
from .teachers import Teacher, AcademicDegreeEnum
from .subjects import Subject, SemesterEnum
from .rooms import Room, RoomTypeEnum

# Export all models
__all__ = [
    'User', 'Student', 'Teacher', 'Subject', 'Room',
    'UserRole', 'SectionEnum', 'StudyTypeEnum', 'AcademicStatusEnum',
    'AcademicDegreeEnum', 'SemesterEnum', 'RoomTypeEnum'
]
