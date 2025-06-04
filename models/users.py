"""
Users Model
نموذج المستخدمين الأساسي
"""

from config.database import db
from .base import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
from datetime import datetime

class UserRole(Enum):
    """User roles enumeration"""
    ADMIN = 'admin'
    TEACHER = 'teacher'
    STUDENT = 'student'

class User(BaseModel):
    """User model for all system users"""
    
    __tablename__ = 'users'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Information
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal Information
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Account Status
    role = db.Column(db.Enum(UserRole), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    student = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    teacher = db.relationship('Teacher', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        self.save()
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary with optional sensitive data"""
        data = super().to_dict()
        
        # Remove sensitive data by default
        if not include_sensitive:
            data.pop('password_hash', None)
            
        # Add computed fields
        data['role'] = self.role.value if self.role else None
        
        return data
    
    def __repr__(self):
        return f'<User {self.username} ({self.role.value if self.role else "No Role"})>'
