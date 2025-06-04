"""
QR_SESSIONS Model - نموذج جلسات QR
نموذج كامل لإدارة جلسات QR المؤقتة مع التشفير والأمان
"""

from config.database import db
from .base import BaseModel
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import CheckConstraint, Index
import uuid
import secrets
import hashlib
import json
from cryptography.fernet import Fernet
import base64
import os

class QRStatusEnum(Enum):
    """حالات جلسة QR"""
    ACTIVE = 'active'        # نشطة
    EXPIRED = 'expired'      # منتهية الصلاحية
    USED = 'used'           # مستخدمة
    DISABLED = 'disabled'    # معطلة
    REVOKED = 'revoked'     # ملغاة

class QRSession(BaseModel):
    """QR Session model for dynamic QR code generation"""
    
    __tablename__ = 'qr_sessions'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Unique Session Identifier
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False, index=True)
    generated_by = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False, index=True)
    
    # QR Data (Encrypted)
    qr_data_encrypted = db.Column(db.Text, nullable=False)
    encryption_key_hash = db.Column(db.String(255), nullable=False)  # Hash of encryption key for verification
    
    # Timing
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    # Status and Settings
    status = db.Column(db.Enum(QRStatusEnum), default=QRStatusEnum.ACTIVE, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    max_usage_count = db.Column(db.Integer, default=1000)  # Maximum number of scans allowed
    current_usage_count = db.Column(db.Integer, default=0)
    
    # Security Settings
    allow_multiple_scans = db.Column(db.Boolean, default=True)  # Allow same student to scan multiple times
    ip_whitelist = db.Column(db.JSON, nullable=True)  # Allowed IP addresses (optional)
    device_binding = db.Column(db.Boolean, default=False)  # Bind to specific device
    
    # Metadata
    qr_image_path = db.Column(db.String(500), nullable=True)  # Path to generated QR image
    qr_display_text = db.Column(db.String(255), nullable=True)  # Text to display with QR
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    # lecture relationship is defined in lectures.py
    teacher = db.relationship('Teacher', backref='qr_sessions', lazy='select')
    attendance_records = db.relationship('AttendanceRecord', backref='qr_session', lazy='dynamic')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('expires_at > generated_at', name='check_qr_time_order'),
        CheckConstraint('max_usage_count > 0', name='check_max_usage_positive'),
        CheckConstraint('current_usage_count >= 0', name='check_current_usage_non_negative'),
        CheckConstraint('current_usage_count <= max_usage_count', name='check_usage_count_limit'),
        Index('idx_qr_session_active', 'is_active', 'status', 'expires_at'),
        Index('idx_qr_session_lecture', 'lecture_id', 'generated_at'),
    )
    
    def __init__(self, **kwargs):
        """Initialize QR session with auto-generated session ID"""
        if 'session_id' not in kwargs:
            kwargs['session_id'] = self.generate_session_id()
        super().__init__(**kwargs)
    
    @staticmethod
    def generate_session_id():
        """Generate unique session ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        random_part = secrets.token_urlsafe(16)
        return f"QR_{timestamp}_{random_part}"
    
    @staticmethod
    def generate_encryption_key():
        """Generate encryption key for QR data"""
        return Fernet.generate_key()
    
    def encrypt_qr_data(self, data_dict, encryption_key=None):
        """Encrypt QR data"""
        if not encryption_key:
            encryption_key = self.generate_encryption_key()
        
        # Convert data to JSON string
        data_json = json.dumps(data_dict, separators=(',', ':'))
        
        # Encrypt data
        fernet = Fernet(encryption_key)
        encrypted_data = fernet.encrypt(data_json.encode())
        
        # Store encrypted data and key hash
        self.qr_data_encrypted = base64.b64encode(encrypted_data).decode()
        self.encryption_key_hash = hashlib.sha256(encryption_key).hexdigest()
        
        return encryption_key
    
    def decrypt_qr_data(self, encryption_key):
        """Decrypt QR data"""
        # Verify encryption key
        key_hash = hashlib.sha256(encryption_key).hexdigest()
        if key_hash != self.encryption_key_hash:
            raise ValueError("Invalid encryption key")
        
        # Decrypt data
        encrypted_data = base64.b64decode(self.qr_data_encrypted.encode())
        fernet = Fernet(encryption_key)
        
        try:
            decrypted_json = fernet.decrypt(encrypted_data).decode()
            return json.loads(decrypted_json)
        except Exception as e:
            raise ValueError(f"Failed to decrypt QR data: {str(e)}")
    
    def is_valid(self):
        """Check if QR session is valid for use"""
        now = datetime.utcnow()
        
        return (self.is_active and 
                self.status == QRStatusEnum.ACTIVE and
                self.expires_at > now and
                self.current_usage_count < self.max_usage_count)
    
    def is_expired(self):
        """Check if QR session has expired"""
        return datetime.utcnow() > self.expires_at
    
    def mark_as_used(self, student_id=None, ip_address=None):
        """Mark QR as used and increment usage count"""
        if not self.is_valid():
            raise ValueError("Cannot use invalid QR session")
        
        # Check IP whitelist if configured
        if self.ip_whitelist and ip_address:
            if ip_address not in self.ip_whitelist:
                raise ValueError("IP address not in whitelist")
        
        # Increment usage count
        self.current_usage_count += 1
        self.last_used_at = datetime.utcnow()
        
        # Mark as used if single-use or max usage reached
        if not self.allow_multiple_scans or self.current_usage_count >= self.max_usage_count:
            self.status = QRStatusEnum.USED
        
        self.save()
        return True
    
    def expire_session(self):
        """Manually expire the session"""
        self.status = QRStatusEnum.EXPIRED
        self.is_active = False
        self.save()
    
    def revoke_session(self, reason=None):
        """Revoke the session"""
        self.status = QRStatusEnum.REVOKED
        self.is_active = False
        if reason:
            self.notes = f"Revoked: {reason}"
        self.save()
    
    def extend_expiry(self, additional_minutes):
        """Extend expiry time"""
        if self.status != QRStatusEnum.ACTIVE:
            raise ValueError("Cannot extend expired or inactive session")
        
        self.expires_at += timedelta(minutes=additional_minutes)
        self.save()
    
    def get_time_remaining(self):
        """Get remaining time in seconds"""
        if self.expires_at:
            remaining = (self.expires_at - datetime.utcnow()).total_seconds()
            return max(0, remaining)
        return 0
    
    def get_usage_percentage(self):
        """Get usage percentage"""
        if self.max_usage_count > 0:
            return round((self.current_usage_count / self.max_usage_count) * 100, 2)
        return 0.0
    
    def generate_qr_payload(self, include_verification_data=True):
        """Generate QR code payload"""
        payload = {
            'session_id': self.session_id,
            'lecture_id': self.lecture_id,
            'generated_at': self.generated_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'version': '1.0'
        }
        
        if include_verification_data and self.lecture:
            payload.update({
                'subject_code': self.lecture.schedule.subject.code if self.lecture.schedule and self.lecture.schedule.subject else None,
                'section': self.lecture.schedule.section.value if self.lecture.schedule and self.lecture.schedule.section else None,
                'room_id': self.lecture.schedule.room_id if self.lecture.schedule else None,
                'teacher_id': self.lecture.schedule.teacher_id if self.lecture.schedule else None
            })
        
        return payload
    
    def generate_display_text(self):
        """Generate display text for QR code"""
        if self.lecture and self.lecture.schedule:
            schedule = self.lecture.schedule
            subject_name = schedule.subject.name if schedule.subject else "Unknown Subject"
            section = schedule.section.value if schedule.section else "Unknown Section"
            room_name = schedule.room.name if schedule.room else "Unknown Room"
            
            return f"{subject_name} - {section}\n{room_name}\n{self.lecture.lecture_date}"
        
        return f"Lecture QR Code\n{self.session_id}"
    
    def to_dict(self, include_sensitive=False, include_relations=False):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Add enum values
        data['status'] = self.status.value if self.status else None
        
        # Format timestamps
        if self.generated_at:
            data['generated_at'] = self.generated_at.isoformat()
        
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        
        if self.last_used_at:
            data['last_used_at'] = self.last_used_at.isoformat()
        
        # Add computed fields
        data['is_valid'] = self.is_valid()
        data['is_expired'] = self.is_expired()
        data['time_remaining_seconds'] = self.get_time_remaining()
        data['usage_percentage'] = self.get_usage_percentage()
        data['display_text'] = self.generate_display_text()
        
        # Remove sensitive data by default
        if not include_sensitive:
            data.pop('qr_data_encrypted', None)
            data.pop('encryption_key_hash', None)
        
        # Include related data if requested
        if include_relations:
            if self.lecture:
                data['lecture'] = {
                    'id': self.lecture.id,
                    'lecture_date': self.lecture.lecture_date.isoformat(),
                    'status': self.lecture.status.value if self.lecture.status else None,
                    'topic': self.lecture.topic
                }
                
                if self.lecture.schedule:
                    data['schedule'] = {
                        'section': self.lecture.schedule.section.value if self.lecture.schedule.section else None,
                        'day_of_week': self.lecture.schedule.day_of_week,
                        'start_time': self.lecture.schedule.start_time.strftime('%H:%M') if self.lecture.schedule.start_time else None,
                        'end_time': self.lecture.schedule.end_time.strftime('%H:%M') if self.lecture.schedule.end_time else None
                    }
                    
                    if self.lecture.schedule.subject:
                        data['subject'] = {
                            'code': self.lecture.schedule.subject.code,
                            'name': self.lecture.schedule.subject.name
                        }
                    
                    if self.lecture.schedule.room:
                        data['room'] = {
                            'name': self.lecture.schedule.room.name,
                            'building': self.lecture.schedule.room.building
                        }
            
            if self.teacher and self.teacher.user:
                data['teacher'] = {
                    'employee_id': self.teacher.employee_id,
                    'full_name': self.teacher.user.full_name
                }
        
        return data
    
    @classmethod
    def create_for_lecture(cls, lecture_id, generated_by_teacher_id, duration_minutes=30, **kwargs):
        """Create QR session for a lecture"""
        # Check if lecture exists and is valid
        from .lectures import Lecture
        lecture = Lecture.query.get(lecture_id)
        if not lecture:
            raise ValueError("Lecture not found")
        
        if not lecture.can_generate_qr():
            raise ValueError("QR generation not allowed for this lecture")
        
        # Set expiry time
        expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        # Create QR session
        qr_session = cls(
            lecture_id=lecture_id,
            generated_by=generated_by_teacher_id,
            expires_at=expires_at,
            **kwargs
        )
        
        # Generate and encrypt QR data
        qr_payload = qr_session.generate_qr_payload()
        encryption_key = qr_session.encrypt_qr_data(qr_payload)
        
        # Set display text
        qr_session.qr_display_text = qr_session.generate_display_text()
        
        qr_session.save()
        
        return qr_session, encryption_key
    
    @classmethod
    def get_active_sessions(cls, lecture_id=None):
        """Get active QR sessions"""
        query = cls.query.filter(
            cls.is_active == True,
            cls.status == QRStatusEnum.ACTIVE,
            cls.expires_at > datetime.utcnow()
        )
        
        if lecture_id:
            query = query.filter_by(lecture_id=lecture_id)
        
        return query.all()
    
    @classmethod
    def cleanup_expired_sessions(cls):
        """Clean up expired sessions"""
        expired_count = cls.query.filter(
            cls.expires_at <= datetime.utcnow(),
            cls.status.in_([QRStatusEnum.ACTIVE, QRStatusEnum.USED])
        ).update({
            'status': QRStatusEnum.EXPIRED,
            'is_active': False
        })
        
        db.session.commit()
        return expired_count
    
    @classmethod
    def find_by_session_id(cls, session_id):
        """Find QR session by session ID"""
        return cls.query.filter_by(session_id=session_id).first()
    
    @classmethod
    def validate_qr_data(cls, session_id, encrypted_data, encryption_key):
        """Validate QR data"""
        qr_session = cls.find_by_session_id(session_id)
        
        if not qr_session:
            return False, "QR session not found"
        
        if not qr_session.is_valid():
            return False, "QR session is not valid"
        
        try:
            # Decrypt and validate data
            decrypted_data = qr_session.decrypt_qr_data(encryption_key)
            
            # Validate session ID matches
            if decrypted_data.get('session_id') != session_id:
                return False, "Session ID mismatch"
            
            # Validate expiry
            expires_at = datetime.fromisoformat(decrypted_data.get('expires_at'))
            if datetime.utcnow() > expires_at:
                return False, "QR code has expired"
            
            return True, "Valid QR code"
            
        except Exception as e:
            return False, f"QR validation error: {str(e)}"
    
    def validate_qr_session(self):
        """Validate QR session data"""
        errors = []
        
        # Check expiry time
        if self.expires_at <= self.generated_at:
            errors.append("Expiry time must be after generation time")
        
        # Check usage counts
        if self.current_usage_count > self.max_usage_count:
            errors.append("Current usage count cannot exceed maximum")
        
        # Check session ID format
        if not self.session_id or not self.session_id.startswith('QR_'):
            errors.append("Invalid session ID format")
        
        return errors
    
    def save(self):
        """Save with validation"""
        errors = self.validate_qr_session()
        if errors:
            raise ValueError(f"QR session validation failed: {', '.join(errors)}")
        
        return super().save()
    
    def __repr__(self):
        return (f'<QRSession {self.session_id} - '
                f'{self.status.value if self.status else "Unknown"} - '
                f'Expires: {self.expires_at}>')