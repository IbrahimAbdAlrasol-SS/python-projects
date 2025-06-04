"""
ATTENDANCE_RECORDS Model - نموذج سجلات الحضور
نموذج كامل لسجلات الحضور مع التحقق الثلاثي والتتبع الدقيق
"""

from config.database import db
from .base import BaseModel
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import CheckConstraint, Index, UniqueConstraint
import json
import uuid

class AttendanceTypeEnum(Enum):
    """نوع الحضور"""
    ON_TIME = 'on_time'        # في الوقت المحدد
    LATE = 'late'              # متأخر
    EXCEPTIONAL = 'exceptional' # استثنائي (بإذن المدرس)

class VerificationStepEnum(Enum):
    """خطوات التحقق"""
    LOCATION = 'location'      # التحقق من الموقع
    QR_CODE = 'qr_code'       # التحقق من QR
    FACE = 'face'             # التحقق من الوجه

class AttendanceStatusEnum(Enum):
    """حالة سجل الحضور"""
    PENDING = 'pending'           # في الانتظار
    VERIFIED = 'verified'         # مُتحقق منه
    REJECTED = 'rejected'         # مرفوض
    UNDER_REVIEW = 'under_review' # تحت المراجعة

class AttendanceRecord(BaseModel):
    """Attendance record model with triple verification"""
    
    __tablename__ = 'attendance_records'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False, index=True)
    qr_session_id = db.Column(db.Integer, db.ForeignKey('qr_sessions.id'), nullable=True, index=True)
    
    # Triple Verification Status
    location_verified = db.Column(db.Boolean, default=False, nullable=False)
    qr_verified = db.Column(db.Boolean, default=False, nullable=False)
    face_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Location Data
    recorded_latitude = db.Column(db.Numeric(10, 8), nullable=True)
    recorded_longitude = db.Column(db.Numeric(11, 8), nullable=True)
    recorded_altitude = db.Column(db.Numeric(8, 3), nullable=True)
    gps_accuracy = db.Column(db.Numeric(5, 2), nullable=True)  # GPS accuracy in meters
    location_verified_at = db.Column(db.DateTime, nullable=True)
    location_verification_data = db.Column(db.JSON, nullable=True)  # Additional location data
    
    # QR Code Data
    qr_verified_at = db.Column(db.DateTime, nullable=True)
    qr_verification_data = db.Column(db.JSON, nullable=True)  # QR verification details
    
    # Face Recognition Data
    face_verified_at = db.Column(db.DateTime, nullable=True)
    face_verification_score = db.Column(db.Numeric(5, 4), nullable=True)  # Confidence score 0-1
    face_verification_data = db.Column(db.JSON, nullable=True)  # Face verification details
    
    # Attendance Information
    attendance_type = db.Column(db.Enum(AttendanceTypeEnum), default=AttendanceTypeEnum.ON_TIME, nullable=False)
    status = db.Column(db.Enum(AttendanceStatusEnum), default=AttendanceStatusEnum.PENDING, nullable=False, index=True)
    
    # Exception Handling
    is_exceptional = db.Column(db.Boolean, default=False, nullable=False, index=True)
    exception_reason = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Timing
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    verification_started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    verification_completed_at = db.Column(db.DateTime, nullable=True)
    
    # Device and Security Information
    device_info = db.Column(db.JSON, nullable=True)  # Device fingerprint, OS, etc.
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)  # App session ID
    
    # Synchronization (for offline mode)
    is_synced = db.Column(db.Boolean, default=True, nullable=False)
    local_id = db.Column(db.String(255), nullable=True)  # Local ID from mobile app
    sync_attempts = db.Column(db.Integer, default=0)
    last_sync_attempt = db.Column(db.DateTime, nullable=True)
    sync_conflicts = db.Column(db.JSON, nullable=True)  # Conflict resolution data
    
    # Metadata
    notes = db.Column(db.Text, nullable=True)
    verification_method = db.Column(db.String(50), default='mobile_app')  # mobile_app, web, manual
    
    # Relationships
    student = db.relationship('Student', backref='attendance_records', lazy='select')
    # lecture relationship is defined in lectures.py
    # qr_session relationship is defined in qr_sessions.py
    approved_by_user = db.relationship('User', foreign_keys=[approved_by], backref='approved_attendance_records', lazy='select')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('student_id', 'lecture_id', name='unique_student_lecture_attendance'),
        CheckConstraint('gps_accuracy >= 0', name='check_gps_accuracy_positive'),
        CheckConstraint('face_verification_score >= 0 AND face_verification_score <= 1', name='check_face_score_range'),
        CheckConstraint('sync_attempts >= 0', name='check_sync_attempts_positive'),
        Index('idx_attendance_verification_status', 'verification_completed', 'status'),
        Index('idx_attendance_student_date', 'student_id', 'check_in_time'),
        Index('idx_attendance_lecture_status', 'lecture_id', 'status'),
        Index('idx_attendance_sync', 'is_synced', 'last_sync_attempt'),
    )
    
    def start_verification_process(self, device_info=None, ip_address=None, user_agent=None):
        """Start the verification process"""
        self.verification_started_at = datetime.utcnow()
        self.device_info = device_info
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.status = AttendanceStatusEnum.PENDING
        
        # Generate session ID for this verification
        self.session_id = str(uuid.uuid4())
        
        self.save()
    
    def verify_location(self, latitude, longitude, altitude=None, accuracy=None, additional_data=None):
        """Verify student location"""
        if not self.lecture or not self.lecture.schedule or not self.lecture.schedule.room:
            raise ValueError("Cannot verify location: missing lecture or room data")
        
        room = self.lecture.schedule.room
        
        # Store location data
        self.recorded_latitude = latitude
        self.recorded_longitude = longitude
        self.recorded_altitude = altitude
        self.gps_accuracy = accuracy
        self.location_verified_at = datetime.utcnow()
        
        # Verify location using room's GPS polygon
        is_inside_polygon = room.is_point_inside_polygon(float(latitude), float(longitude))
        
        # Verify altitude if available
        altitude_match = True
        if altitude and room.floor_altitude:
            altitude_match = room.is_altitude_match(float(altitude))
        
        # Location is verified if inside polygon and altitude matches
        location_verified = is_inside_polygon and altitude_match
        
        # Store verification data
        verification_data = {
            'inside_polygon': is_inside_polygon,
            'altitude_match': altitude_match,
            'distance_from_center': room.distance_from_center(float(latitude), float(longitude)),
            'room_id': room.id,
            'room_name': room.name,
            'verification_time': self.location_verified_at.isoformat()
        }
        
        if additional_data:
            verification_data.update(additional_data)
        
        self.location_verification_data = verification_data
        self.location_verified = location_verified
        
        # Check overall verification status
        self._check_verification_completion()
        
        return location_verified
    
    def verify_qr_code(self, qr_session_id, qr_data=None, additional_data=None):
        """Verify QR code"""
        from .qr_sessions import QRSession
        
        qr_session = QRSession.query.get(qr_session_id)
        if not qr_session:
            raise ValueError("QR session not found")
        
        if not qr_session.is_valid():
            raise ValueError("QR session is not valid")
        
        # Verify QR belongs to the same lecture
        if qr_session.lecture_id != self.lecture_id:
            raise ValueError("QR code does not belong to this lecture")
        
        # Mark QR session as used
        try:
            qr_session.mark_as_used(self.student_id, self.ip_address)
        except ValueError as e:
            raise ValueError(f"QR verification failed: {str(e)}")
        
        # Store verification data
        self.qr_session_id = qr_session_id
        self.qr_verified_at = datetime.utcnow()
        
        verification_data = {
            'qr_session_id': qr_session_id,
            'qr_expires_at': qr_session.expires_at.isoformat(),
            'qr_usage_count': qr_session.current_usage_count,
            'verification_time': self.qr_verified_at.isoformat()
        }
        
        if qr_data:
            verification_data['qr_data'] = qr_data
        
        if additional_data:
            verification_data.update(additional_data)
        
        self.qr_verification_data = verification_data
        self.qr_verified = True
        
        # Check overall verification status
        self._check_verification_completion()
        
        return True
    
    def verify_face(self, verification_score, additional_data=None):
        """Verify face recognition"""
        if not (0 <= verification_score <= 1):
            raise ValueError("Face verification score must be between 0 and 1")
        
        # Minimum threshold for face verification (configurable)
        min_threshold = 0.75  # 75% confidence
        
        face_verified = verification_score >= min_threshold
        
        # Store verification data
        self.face_verified_at = datetime.utcnow()
        self.face_verification_score = verification_score
        
        verification_data = {
            'score': float(verification_score),
            'threshold': min_threshold,
            'verified': face_verified,
            'verification_time': self.face_verified_at.isoformat()
        }
        
        if additional_data:
            verification_data.update(additional_data)
        
        self.face_verification_data = verification_data
        self.face_verified = face_verified
        
        # Check overall verification status
        self._check_verification_completion()
        
        return face_verified
    
    def _check_verification_completion(self):
        """Check if all verification steps are completed"""
        all_verified = (self.location_verified and 
                       self.qr_verified and 
                       self.face_verified)
        
        if all_verified and not self.verification_completed:
            self.verification_completed = True
            self.verification_completed_at = datetime.utcnow()
            self.status = AttendanceStatusEnum.VERIFIED
            
            # Determine attendance type based on timing
            self._determine_attendance_type()
        
        self.save()
    
    def _determine_attendance_type(self):
        """Determine if attendance is on time, late, or exceptional"""
        if self.is_exceptional:
            self.attendance_type = AttendanceTypeEnum.EXCEPTIONAL
            return
        
        if not self.lecture or not self.check_in_time:
            return
        
        # Check if attendance is late
        if self.lecture.is_late_attendance(self.check_in_time):
            self.attendance_type = AttendanceTypeEnum.LATE
        else:
            self.attendance_type = AttendanceTypeEnum.ON_TIME
    
    def mark_as_exceptional(self, reason, approved_by_user_id):
        """Mark attendance as exceptional"""
        self.is_exceptional = True
        self.exception_reason = reason
        self.approved_by = approved_by_user_id
        self.approved_at = datetime.utcnow()
        self.attendance_type = AttendanceTypeEnum.EXCEPTIONAL
        self.status = AttendanceStatusEnum.VERIFIED
        
        # Exceptional attendance bypasses normal verification
        self.verification_completed = True
        self.verification_completed_at = datetime.utcnow()
        
        self.save()
    
    def reject_attendance(self, reason=None):
        """Reject attendance record"""
        self.status = AttendanceStatusEnum.REJECTED
        if reason:
            self.notes = f"Rejected: {reason}"
        
        self.save()
    
    def get_verification_progress(self):
        """Get verification progress as percentage"""
        steps_completed = sum([
            self.location_verified,
            self.qr_verified,
            self.face_verified
        ])
        return round((steps_completed / 3) * 100, 2)
    
    def get_verification_summary(self):
        """Get summary of verification status"""
        return {
            'location': {
                'verified': self.location_verified,
                'verified_at': self.location_verified_at.isoformat() if self.location_verified_at else None,
                'data': self.location_verification_data
            },
            'qr_code': {
                'verified': self.qr_verified,
                'verified_at': self.qr_verified_at.isoformat() if self.qr_verified_at else None,
                'data': self.qr_verification_data
            },
            'face': {
                'verified': self.face_verified,
                'verified_at': self.face_verified_at.isoformat() if self.face_verified_at else None,
                'score': float(self.face_verification_score) if self.face_verification_score else None,
                'data': self.face_verification_data
            },
            'overall': {
                'completed': self.verification_completed,
                'progress': self.get_verification_progress(),
                'status': self.status.value if self.status else None
            }
        }
    
    def handle_sync_conflict(self, server_record_data, resolution='keep_server'):
        """Handle synchronization conflicts"""
        conflict_data = {
            'conflict_detected_at': datetime.utcnow().isoformat(),
            'local_record': self.to_dict(),
            'server_record': server_record_data,
            'resolution': resolution
        }
        
        if resolution == 'keep_server':
            # Update local record with server data
            for key, value in server_record_data.items():
                if hasattr(self, key) and key not in ['id', 'created_at']:
                    setattr(self, key, value)
        elif resolution == 'keep_local':
            # Keep local record, mark conflict for manual review
            self.status = AttendanceStatusEnum.UNDER_REVIEW
        
        self.sync_conflicts = conflict_data
        self.is_synced = True
        self.save()
    
    def to_dict(self, include_sensitive=False, include_verification_details=False):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Add enum values
        data['attendance_type'] = self.attendance_type.value if self.attendance_type else None
        data['status'] = self.status.value if self.status else None
        
        # Format timestamps
        if self.check_in_time:
            data['check_in_time'] = self.check_in_time.isoformat()
        
        if self.verification_started_at:
            data['verification_started_at'] = self.verification_started_at.isoformat()
        
        if self.verification_completed_at:
            data['verification_completed_at'] = self.verification_completed_at.isoformat()
        
        if self.approved_at:
            data['approved_at'] = self.approved_at.isoformat()
        
        # Add computed fields
        data['verification_progress'] = self.get_verification_progress()
        
        # Include verification details if requested
        if include_verification_details:
            data['verification_summary'] = self.get_verification_summary()
        
        # Remove sensitive data by default
        if not include_sensitive:
            data.pop('device_info', None)
            data.pop('ip_address', None)
            data.pop('user_agent', None)
            data.pop('session_id', None)
            data.pop('sync_conflicts', None)
        
        # Format coordinates
        if self.recorded_latitude:
            data['recorded_latitude'] = float(self.recorded_latitude)
        
        if self.recorded_longitude:
            data['recorded_longitude'] = float(self.recorded_longitude)
        
        if self.recorded_altitude:
            data['recorded_altitude'] = float(self.recorded_altitude)
        
        if self.gps_accuracy:
            data['gps_accuracy'] = float(self.gps_accuracy)
        
        if self.face_verification_score:
            data['face_verification_score'] = float(self.face_verification_score)
        
        return data
    
    @classmethod
    def get_student_attendance(cls, student_id, start_date=None, end_date=None):
        """Get attendance records for a student"""
        query = cls.query.filter_by(student_id=student_id)
        
        if start_date:
            query = query.join(cls.lecture).filter(cls.lecture.has(lecture_date__gte=start_date))
        
        if end_date:
            query = query.join(cls.lecture).filter(cls.lecture.has(lecture_date__lte=end_date))
        
        return query.order_by(cls.check_in_time.desc()).all()
    
    @classmethod
    def get_lecture_attendance(cls, lecture_id, status=None):
        """Get attendance records for a lecture"""
        query = cls.query.filter_by(lecture_id=lecture_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(cls.check_in_time).all()
    
    @classmethod
    def get_pending_verifications(cls):
        """Get records pending verification"""
        return cls.query.filter_by(
            verification_completed=False,
            status=AttendanceStatusEnum.PENDING
        ).order_by(cls.verification_started_at).all()
    
    @classmethod
    def get_sync_conflicts(cls):
        """Get records with sync conflicts"""
        return cls.query.filter(
            cls.sync_conflicts.isnot(None)
        ).order_by(cls.last_sync_attempt.desc()).all()
    
    @classmethod
    def create_attendance_record(cls, student_id, lecture_id, **kwargs):
        """Create new attendance record"""
        # Check if record already exists
        existing = cls.query.filter_by(
            student_id=student_id,
            lecture_id=lecture_id
        ).first()
        
        if existing:
            raise ValueError("Attendance record already exists for this student and lecture")
        
        # Verify lecture exists and is valid
        from .lectures import Lecture
        lecture = Lecture.query.get(lecture_id)
        if not lecture:
            raise ValueError("Lecture not found")
        
        if not lecture.is_attendance_open():
            raise ValueError("Attendance is not open for this lecture")
        
        # Create record
        record = cls(
            student_id=student_id,
            lecture_id=lecture_id,
            **kwargs
        )
        
        record.save()
        return record
    
    def validate_attendance_record(self):
        """Validate attendance record data"""
        errors = []
        
        # Check required fields
        if not self.student_id:
            errors.append("Student ID is required")
        
        if not self.lecture_id:
            errors.append("Lecture ID is required")
        
        # Validate GPS accuracy
        if self.gps_accuracy is not None and self.gps_accuracy < 0:
            errors.append("GPS accuracy cannot be negative")
        
        # Validate face verification score
        if self.face_verification_score is not None:
            if not (0 <= self.face_verification_score <= 1):
                errors.append("Face verification score must be between 0 and 1")
        
        return errors
    
    def save(self):
        """Save with validation"""
        errors = self.validate_attendance_record()
        if errors:
            raise ValueError(f"Attendance record validation failed: {', '.join(errors)}")
        
        return super().save()
    
    def __repr__(self):
        return (f'<AttendanceRecord Student:{self.student_id} '
                f'Lecture:{self.lecture_id} '
                f'Status:{self.status.value if self.status else "Unknown"}>')