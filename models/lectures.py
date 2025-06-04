"""
LECTURES Model - نموذج المحاضرات
نموذج كامل للمحاضرات مع جميع العلاقات وإدارة الحالات
"""

from config.database import db
from .base import BaseModel
from enum import Enum
from datetime import datetime, date, time, timedelta
from sqlalchemy import CheckConstraint, Index
import uuid

class LectureStatusEnum(Enum):
    """حالات المحاضرة"""
    SCHEDULED = 'scheduled'    # مجدولة
    ACTIVE = 'active'         # جارية حالياً
    COMPLETED = 'completed'   # مكتملة
    CANCELLED = 'cancelled'   # ملغاة
    POSTPONED = 'postponed'   # مؤجلة

class Lecture(BaseModel):
    """Lecture model for individual lecture sessions"""
    
    __tablename__ = 'lectures'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False, index=True)
    
    # Lecture Information
    lecture_date = db.Column(db.Date, nullable=False, index=True)
    actual_start_time = db.Column(db.DateTime, nullable=True)
    actual_end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum(LectureStatusEnum), default=LectureStatusEnum.SCHEDULED, nullable=False, index=True)
    
    # QR Code Settings
    qr_enabled = db.Column(db.Boolean, default=True, nullable=False)
    qr_generation_allowed = db.Column(db.Boolean, default=True, nullable=False)
    qr_auto_disable_minutes = db.Column(db.Integer, default=15)  # Auto-disable QR after X minutes
    
    # Lecture Content
    topic = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Attendance Settings
    attendance_window_minutes = db.Column(db.Integer, default=10)  # Allow attendance X minutes after start
    late_threshold_minutes = db.Column(db.Integer, default=5)      # Mark as late after X minutes
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    # Statistics (will be updated via triggers or background jobs)
    total_expected_students = db.Column(db.Integer, default=0)
    total_attended_students = db.Column(db.Integer, default=0)
    total_late_students = db.Column(db.Integer, default=0)
    total_exceptional_attendance = db.Column(db.Integer, default=0)
    
    # Relationships
    # schedule relationship is defined in schedules.py
    qr_sessions = db.relationship('QRSession', backref='lecture', lazy='dynamic', cascade='all, delete-orphan')
    attendance_records = db.relationship('AttendanceRecord', backref='lecture', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('actual_start_time <= actual_end_time', name='check_lecture_time_order'),
        CheckConstraint('attendance_window_minutes >= 0', name='check_attendance_window'),
        CheckConstraint('late_threshold_minutes >= 0', name='check_late_threshold'),
        CheckConstraint('qr_auto_disable_minutes >= 1', name='check_qr_auto_disable'),
        Index('idx_lecture_date_status', 'lecture_date', 'status'),
        Index('idx_lecture_schedule_date', 'schedule_id', 'lecture_date'),
    )
    
    def get_scheduled_start_time(self):
        """Get scheduled start time based on schedule"""
        if self.schedule and self.schedule.start_time:
            return datetime.combine(self.lecture_date, self.schedule.start_time)
        return None
    
    def get_scheduled_end_time(self):
        """Get scheduled end time based on schedule"""
        if self.schedule and self.schedule.end_time:
            return datetime.combine(self.lecture_date, self.schedule.end_time)
        return None
    
    def get_duration_minutes(self):
        """Calculate actual duration in minutes"""
        if self.actual_start_time and self.actual_end_time:
            return int((self.actual_end_time - self.actual_start_time).total_seconds() / 60)
        elif self.schedule:
            scheduled_start = self.get_scheduled_start_time()
            scheduled_end = self.get_scheduled_end_time()
            if scheduled_start and scheduled_end:
                return int((scheduled_end - scheduled_start).total_seconds() / 60)
        return 0
    
    def is_attendance_open(self):
        """Check if attendance is still open"""
        if self.status != LectureStatusEnum.ACTIVE:
            return False
        
        if not self.actual_start_time:
            return False
        
        # Check if within attendance window
        attendance_deadline = self.actual_start_time + timedelta(minutes=self.attendance_window_minutes)
        return datetime.utcnow() <= attendance_deadline
    
    def is_late_attendance(self, attendance_time=None):
        """Check if attendance time is considered late"""
        if not attendance_time:
            attendance_time = datetime.utcnow()
        
        if not self.actual_start_time:
            scheduled_start = self.get_scheduled_start_time()
            if not scheduled_start:
                return False
            late_threshold = scheduled_start + timedelta(minutes=self.late_threshold_minutes)
        else:
            late_threshold = self.actual_start_time + timedelta(minutes=self.late_threshold_minutes)
        
        return attendance_time > late_threshold
    
    def can_generate_qr(self):
        """Check if QR code can be generated"""
        return (self.qr_enabled and 
                self.qr_generation_allowed and 
                self.status in [LectureStatusEnum.SCHEDULED, LectureStatusEnum.ACTIVE])
    
    def start_lecture(self, started_by_user_id=None):
        """Start the lecture"""
        if self.status != LectureStatusEnum.SCHEDULED:
            raise ValueError(f"Cannot start lecture with status: {self.status.value}")
        
        self.status = LectureStatusEnum.ACTIVE
        self.actual_start_time = datetime.utcnow()
        
        if started_by_user_id:
            self.created_by = started_by_user_id
        
        self.save()
        return self
    
    def end_lecture(self, ended_by_user_id=None):
        """End the lecture"""
        if self.status != LectureStatusEnum.ACTIVE:
            raise ValueError(f"Cannot end lecture with status: {self.status.value}")
        
        self.status = LectureStatusEnum.COMPLETED
        self.actual_end_time = datetime.utcnow()
        
        # Disable QR generation
        self.qr_generation_allowed = False
        
        # Update statistics
        self.update_attendance_statistics()
        
        self.save()
        return self
    
    def cancel_lecture(self, cancelled_by_user_id, reason=None):
        """Cancel the lecture"""
        if self.status in [LectureStatusEnum.COMPLETED, LectureStatusEnum.CANCELLED]:
            raise ValueError(f"Cannot cancel lecture with status: {self.status.value}")
        
        self.status = LectureStatusEnum.CANCELLED
        self.cancelled_by = cancelled_by_user_id
        self.cancellation_reason = reason
        self.cancelled_at = datetime.utcnow()
        
        # Disable QR generation
        self.qr_generation_allowed = False
        
        self.save()
        return self
    
    def postpone_lecture(self, new_date, postponed_by_user_id, reason=None):
        """Postpone the lecture to a new date"""
        if self.status != LectureStatusEnum.SCHEDULED:
            raise ValueError(f"Cannot postpone lecture with status: {self.status.value}")
        
        # Create new lecture for new date
        new_lecture = Lecture(
            schedule_id=self.schedule_id,
            lecture_date=new_date,
            topic=self.topic,
            description=self.description,
            qr_enabled=self.qr_enabled,
            attendance_window_minutes=self.attendance_window_minutes,
            late_threshold_minutes=self.late_threshold_minutes,
            created_by=postponed_by_user_id
        )
        new_lecture.save()
        
        # Mark current lecture as postponed
        self.status = LectureStatusEnum.POSTPONED
        self.cancellation_reason = reason or "Postponed to new date"
        self.cancelled_by = postponed_by_user_id
        self.cancelled_at = datetime.utcnow()
        
        self.save()
        return new_lecture
    
    def update_attendance_statistics(self):
        """Update attendance statistics"""
        # Get expected students count
        if self.schedule and self.schedule.section:
            from .students import Student
            expected_students = Student.query.filter_by(
                section=self.schedule.section,
                study_year=self.schedule.subject.study_year if self.schedule.subject else None,
                academic_status='active'
            ).count()
            self.total_expected_students = expected_students
        
        # Count attendance records
        attended = self.attendance_records.filter_by(verification_completed=True).count()
        late = self.attendance_records.filter_by(
            verification_completed=True,
            attendance_type='late'
        ).count()
        exceptional = self.attendance_records.filter_by(
            verification_completed=True,
            is_exceptional=True
        ).count()
        
        self.total_attended_students = attended
        self.total_late_students = late
        self.total_exceptional_attendance = exceptional
    
    def get_attendance_rate(self):
        """Calculate attendance rate percentage"""
        if self.total_expected_students > 0:
            return round((self.total_attended_students / self.total_expected_students) * 100, 2)
        return 0.0
    
    def get_late_rate(self):
        """Calculate late attendance rate percentage"""
        if self.total_attended_students > 0:
            return round((self.total_late_students / self.total_attended_students) * 100, 2)
        return 0.0
    
    def to_dict(self, include_relations=False, include_statistics=True):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Add enum values
        data['status'] = self.status.value if self.status else None
        
        # Format dates and times
        if self.lecture_date:
            data['lecture_date'] = self.lecture_date.isoformat()
        
        if self.actual_start_time:
            data['actual_start_time'] = self.actual_start_time.isoformat()
        
        if self.actual_end_time:
            data['actual_end_time'] = self.actual_end_time.isoformat()
        
        if self.cancelled_at:
            data['cancelled_at'] = self.cancelled_at.isoformat()
        
        # Add computed fields
        data['scheduled_start_time'] = self.get_scheduled_start_time().isoformat() if self.get_scheduled_start_time() else None
        data['scheduled_end_time'] = self.get_scheduled_end_time().isoformat() if self.get_scheduled_end_time() else None
        data['duration_minutes'] = self.get_duration_minutes()
        data['is_attendance_open'] = self.is_attendance_open()
        data['can_generate_qr'] = self.can_generate_qr()
        
        # Include statistics
        if include_statistics:
            data['attendance_rate'] = self.get_attendance_rate()
            data['late_rate'] = self.get_late_rate()
        
        # Include related data if requested
        if include_relations and self.schedule:
            data['schedule'] = {
                'id': self.schedule.id,
                'section': self.schedule.section.value if self.schedule.section else None,
                'day_of_week': self.schedule.day_of_week,
                'day_name': self.schedule.get_day_name('ar'),
                'start_time': self.schedule.start_time.strftime('%H:%M') if self.schedule.start_time else None,
                'end_time': self.schedule.end_time.strftime('%H:%M') if self.schedule.end_time else None,
                'academic_year': self.schedule.academic_year,
                'semester': self.schedule.semester.value if self.schedule.semester else None
            }
            
            if self.schedule.subject:
                data['subject'] = {
                    'id': self.schedule.subject.id,
                    'code': self.schedule.subject.code,
                    'name': self.schedule.subject.name,
                    'credit_hours': self.schedule.subject.credit_hours
                }
            
            if self.schedule.teacher and self.schedule.teacher.user:
                data['teacher'] = {
                    'id': self.schedule.teacher.id,
                    'employee_id': self.schedule.teacher.employee_id,
                    'full_name': self.schedule.teacher.user.full_name,
                    'department': self.schedule.teacher.department
                }
            
            if self.schedule.room:
                data['room'] = {
                    'id': self.schedule.room.id,
                    'name': self.schedule.room.name,
                    'building': self.schedule.room.building,
                    'floor': self.schedule.room.floor
                }
        
        return data
    
    @classmethod
    def get_lectures_by_date_range(cls, start_date, end_date, status=None):
        """Get lectures within date range"""
        query = cls.query.filter(
            cls.lecture_date >= start_date,
            cls.lecture_date <= end_date
        )
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(cls.lecture_date, cls.actual_start_time).all()
    
    @classmethod
    def get_today_lectures(cls, status=None):
        """Get today's lectures"""
        today = date.today()
        return cls.get_lectures_by_date_range(today, today, status)
    
    @classmethod
    def get_active_lectures(cls):
        """Get currently active lectures"""
        return cls.query.filter_by(status=LectureStatusEnum.ACTIVE).all()
    
    @classmethod
    def get_teacher_lectures(cls, teacher_id, start_date=None, end_date=None):
        """Get lectures for a specific teacher"""
        query = cls.query.join(cls.schedule).filter(
            cls.schedule.has(teacher_id=teacher_id)
        )
        
        if start_date:
            query = query.filter(cls.lecture_date >= start_date)
        
        if end_date:
            query = query.filter(cls.lecture_date <= end_date)
        
        return query.order_by(cls.lecture_date.desc()).all()
    
    @classmethod
    def get_section_lectures(cls, section, academic_year, semester, start_date=None, end_date=None):
        """Get lectures for a specific section"""
        query = cls.query.join(cls.schedule).filter(
            cls.schedule.has(section=section, academic_year=academic_year, semester=semester)
        )
        
        if start_date:
            query = query.filter(cls.lecture_date >= start_date)
        
        if end_date:
            query = query.filter(cls.lecture_date <= end_date)
        
        return query.order_by(cls.lecture_date, cls.actual_start_time).all()
    
    @classmethod
    def create_from_schedule(cls, schedule, lecture_date, **kwargs):
        """Create a lecture from a schedule"""
        lecture = cls(
            schedule_id=schedule.id,
            lecture_date=lecture_date,
            **kwargs
        )
        
        # Set expected students count
        if schedule.section:
            from .students import Student
            expected_count = Student.query.filter_by(
                section=schedule.section,
                study_year=schedule.subject.study_year if schedule.subject else None,
                academic_status='active'
            ).count()
            lecture.total_expected_students = expected_count
        
        return lecture
    
    def validate_lecture(self):
        """Validate lecture data"""
        errors = []
        
        # Check if lecture date is not in the past (for new lectures)
        if not self.id and self.lecture_date < date.today():
            errors.append("Cannot create lecture for past date")
        
        # Validate time order
        if self.actual_start_time and self.actual_end_time:
            if self.actual_start_time >= self.actual_end_time:
                errors.append("Actual start time must be before end time")
        
        # Validate attendance settings
        if self.attendance_window_minutes < 0:
            errors.append("Attendance window cannot be negative")
        
        if self.late_threshold_minutes < 0:
            errors.append("Late threshold cannot be negative")
        
        return errors
    
    def save(self):
        """Save with validation"""
        errors = self.validate_lecture()
        if errors:
            raise ValueError(f"Lecture validation failed: {', '.join(errors)}")
        
        return super().save()
    
    def __repr__(self):
        return (f'<Lecture {self.id} - {self.lecture_date} - '
                f'{self.status.value if self.status else "Unknown"}>')