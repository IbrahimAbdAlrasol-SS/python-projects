"""
SUBJECTS Model
نموذج المواد الدراسية
"""

from config.database import db
from .base import BaseModel
from enum import Enum

class SemesterEnum(Enum):
    """Semester enumeration"""
    FIRST = 'first'
    SECOND = 'second'
    SUMMER = 'summer'

class Subject(BaseModel):
    """Subject model for academic courses"""
    
    __tablename__ = 'subjects'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Subject Information
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)  # CS101
    name = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    
    # Academic Details
    credit_hours = db.Column(db.Integer, nullable=False)
    study_year = db.Column(db.Integer, nullable=False, index=True)
    semester = db.Column(db.Enum(SemesterEnum), nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('study_year >= 1 AND study_year <= 4', name='check_subject_study_year'),
        db.CheckConstraint('credit_hours >= 1 AND credit_hours <= 6', name='check_credit_hours'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['semester'] = self.semester.value if self.semester else None
        return data
    
    @classmethod
    def find_by_code(cls, code):
        """Find subject by code"""
        return cls.query.filter_by(code=code).first()
    
    @classmethod
    def get_by_year_and_semester(cls, study_year, semester):
        """Get subjects by year and semester"""
        return cls.query.filter_by(study_year=study_year, semester=semester, is_active=True).all()
    
    @classmethod
    def get_by_department(cls, department):
        """Get subjects by department"""
        return cls.query.filter_by(department=department, is_active=True).all()
    
    def __repr__(self):
        return f'<Subject {self.code} - {self.name}>'