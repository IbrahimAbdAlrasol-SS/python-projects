"""
STUDENTS Model
نموذج students
"""

import enum
from config.database import db
from .base import BaseModel
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

# Define enumerations
class SectionEnum(enum.Enum):
    SCIENCE = "science"
    ARTS = "arts"

class StudyTypeEnum(enum.Enum):
    REGULAR = "regular"
    EVENING = "evening"
    PARALLEL = "parallel"

class AcademicStatusEnum(enum.Enum):
    ACTIVE = "active"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"
    TRANSFERRED = "transferred"

# Student model
class Student(BaseModel):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    section = Column(Enum(SectionEnum), nullable=False)
    study_type = Column(Enum(StudyTypeEnum), nullable=False, default=StudyTypeEnum.REGULAR)
    academic_status = Column(Enum(AcademicStatusEnum), nullable=False, default=AcademicStatusEnum.ACTIVE)
    
    # Relationships
    user = relationship("User", back_populates="student")
    
    def __repr__(self):
        return f"<Student {self.student_id}>"
