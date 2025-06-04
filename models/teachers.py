"""
TEACHERS Model
نموذج المدرسين مع جميع التفاصيل
"""

from config.database import db
from .base import BaseModel
from enum import Enum

class AcademicDegreeEnum(Enum):
    """Academic degree enumeration"""
    BACHELOR = 'bachelor'
    MASTER = 'master'
    PHD = 'phd'
    PROFESSOR = 'professor'

class Teacher(BaseModel):
    """Teacher model with complete details"""
    
    __tablename__ = 'teachers'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Employment Information
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    department = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=True)
    
    # Academic Information
    academic_degree = db.Column(db.Enum(AcademicDegreeEnum), nullable=True)
    subjects = db.Column(db.JSON, nullable=True)  # List of subject codes they teach
    
    # Office Information
    office_location = db.Column(db.String(100), nullable=True)
    
    def add_subject(self, subject_code):
        """Add a subject to teacher's teaching list"""
        if self.subjects is None:
            self.subjects = []
        
        if subject_code not in self.subjects:
            self.subjects.append(subject_code)
            self.save()
    
    def remove_subject(self, subject_code):
        """Remove a subject from teacher's teaching list"""
        if self.subjects and subject_code in self.subjects:
            self.subjects.remove(subject_code)
            self.save()
    
    def teaches_subject(self, subject_code):
        """Check if teacher teaches a specific subject"""
        return self.subjects and subject_code in self.subjects
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Add enum values
        data['academic_degree'] = self.academic_degree.value if self.academic_degree else None
        
        return data
    
    @classmethod
    def find_by_employee_id(cls, employee_id):
        """Find teacher by employee ID"""
        return cls.query.filter_by(employee_id=employee_id).first()
    
    @classmethod
    def get_by_department(cls, department):
        """Get teachers by department"""
        return cls.query.filter_by(department=department).all()
    
    @classmethod
    def get_by_subject(cls, subject_code):
        """Get teachers who teach a specific subject"""
        return cls.query.filter(cls.subjects.contains([subject_code])).all()
    
    def __repr__(self):
        return f'<Teacher {self.employee_id} - {self.department}>'