"""
STUDENTS Model
نموذج الطلاب مع جميع التفاصيل
"""

from config.database import db
from .base import BaseModel
from enum import Enum
from datetime import datetime
import bcrypt

class SectionEnum(Enum):
    """Student sections"""
    A = 'A'
    B = 'B'
    C = 'C'

class StudyTypeEnum(Enum):
    """Study type enumeration"""
    MORNING = 'morning'
    EVENING = 'evening'
    HOSTED = 'hosted'

class AcademicStatusEnum(Enum):
    """Academic status enumeration"""
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    GRADUATED = 'graduated'

class Student(BaseModel):
    """Student model with complete details"""
    
    __tablename__ = 'students'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # University Information
    university_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # CS2021001
    secret_code_hash = db.Column(db.String(255), nullable=False)
    
    # Academic Information
    section = db.Column(db.Enum(SectionEnum), nullable=False, index=True)
    study_year = db.Column(db.Integer, nullable=False, index=True)
    study_type = db.Column(db.Enum(StudyTypeEnum), nullable=False, default=StudyTypeEnum.MORNING)
    is_repeater = db.Column(db.Boolean, default=False)
    failed_subjects = db.Column(db.JSON, nullable=True)
    
    # Biometric Information
    face_registered = db.Column(db.Boolean, default=False)
    face_registered_at = db.Column(db.DateTime, nullable=True)
    
    # Device Security
    device_fingerprint = db.Column(db.String(255), nullable=True)
    
    # External Integration
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=True)
    
    # Status
    academic_status = db.Column(db.Enum(AcademicStatusEnum), default=AcademicStatusEnum.ACTIVE)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('study_year >= 1 AND study_year <= 4', name='check_study_year'),
    )
    
    def set_secret_code(self, secret_code):
        """Set encrypted secret code"""
        if len(secret_code) < 6:
            raise ValueError("Secret code must be at least 6 characters")
        
        salt = bcrypt.gensalt()
        self.secret_code_hash = bcrypt.hashpw(secret_code.encode('utf-8'), salt).decode('utf-8')
    
    def verify_secret_code(self, secret_code):
        """Verify secret code"""
        return bcrypt.checkpw(secret_code.encode('utf-8'), self.secret_code_hash.encode('utf-8'))
    
    def register_face(self):
        """Mark face as registered"""
        self.face_registered = True
        self.face_registered_at = datetime.utcnow()
        self.save()
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Remove sensitive data by default
        if not include_sensitive:
            data.pop('secret_code_hash', None)
            data.pop('device_fingerprint', None)
        
        # Add enum values
        data['section'] = self.section.value if self.section else None
        data['study_type'] = self.study_type.value if self.study_type else None
        data['academic_status'] = self.academic_status.value if self.academic_status else None
        
        return data
    
    @classmethod
    def find_by_university_id(cls, university_id):
        """Find student by university ID"""
        return cls.query.filter_by(university_id=university_id).first()
    
    @classmethod
    def get_by_section_and_year(cls, section, study_year):
        """Get students by section and year"""
        return cls.query.filter_by(section=section, study_year=study_year).all()
    
    def __repr__(self):
        return f'<Student {self.university_id} - {self.section.value if self.section else "No Section"}>'