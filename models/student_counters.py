"""
STUDENT_COUNTERS Model - نموذج العداد الذكي للطلاب
نموذج كامل للعداد الذكي مع التكامل مع البوت والإجراءات التلقائية
"""

from config.database import db
from .base import BaseModel
from .subjects import SemesterEnum
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

class CounterActionEnum(Enum):
    """نوع عملية العداد"""
    INCREMENT = 'increment'      # زيادة العداد (+1)
    DECREMENT = 'decrement'      # تقليل العداد (-1)
    RESET = 'reset'             # إعادة تعيين العداد (0)
    MANUAL_SET = 'manual_set'   # تعيين يدوي

class CounterStatusEnum(Enum):
    """حالة العداد"""
    ACTIVE = 'active'           # نشط
    MUTED = 'muted'            # مكتوم
    SUSPENDED = 'suspended'     # معلق
    ARCHIVED = 'archived'       # مؤرشف

class StudentCounter(BaseModel):
    """Student counter model for smart behavior tracking"""
    
    __tablename__ = 'student_counters'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    
    # Academic Period
    academic_year = db.Column(db.String(9), nullable=False, index=True)  # 2023-2024
    semester = db.Column(db.Enum(SemesterEnum), nullable=False, index=True)
    
    # Counter Values
    counter_value = db.Column(db.Integer, default=0, nullable=False, index=True)
    total_increments = db.Column(db.Integer, default=0, nullable=False)
    total_decrements = db.Column(db.Integer, default=0, nullable=False)
    total_resets = db.Column(db.Integer, default=0, nullable=False)
    
    # Status and Muting
    status = db.Column(db.Enum(CounterStatusEnum), default=CounterStatusEnum.ACTIVE, nullable=False, index=True)
    is_muted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    muted_at = db.Column(db.DateTime, nullable=True)
    unmuted_at = db.Column(db.DateTime, nullable=True)
    mute_reason = db.Column(db.Text, nullable=True)
    
    # Last Actions
    last_action = db.Column(db.Enum(CounterActionEnum), nullable=True)
    last_action_at = db.Column(db.DateTime, nullable=True)
    last_action_reason = db.Column(db.Text, nullable=True)
    last_action_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Increment Tracking
    last_increment_at = db.Column(db.DateTime, nullable=True)
    last_increment_reason = db.Column(db.Text, nullable=True)
    consecutive_increments = db.Column(db.Integer, default=0)
    
    # Decrement Tracking
    last_decrement_at = db.Column(db.DateTime, nullable=True)
    last_decrement_reason = db.Column(db.Text, nullable=True)
    consecutive_decrements = db.Column(db.Integer, default=0)
    consecutive_on_time = db.Column(db.Integer, default=0)  # Consecutive on-time submissions/attendance
    
    # Performance Metrics
    total_assignments = db.Column(db.Integer, default=0)
    on_time_assignments = db.Column(db.Integer, default=0)
    late_assignments = db.Column(db.Integer, default=0)
    missed_assignments = db.Column(db.Integer, default=0)
    
    total_lectures = db.Column(db.Integer, default=0)
    attended_lectures = db.Column(db.Integer, default=0)
    late_attendances = db.Column(db.Integer, default=0)
    missed_lectures = db.Column(db.Integer, default=0)
    
    # Telegram Integration
    telegram_user_id = db.Column(db.BigInteger, nullable=True, index=True)
    telegram_username = db.Column(db.String(255), nullable=True)
    telegram_notifications_enabled = db.Column(db.Boolean, default=True)
    last_telegram_notification = db.Column(db.DateTime, nullable=True)
    
    # Automation Settings
    auto_mute_threshold = db.Column(db.Integer, default=1)  # Auto-mute when counter >= this value
    auto_unmute_enabled = db.Column(db.Boolean, default=True)
    warning_threshold = db.Column(db.Integer, default=0)  # Send warning when counter reaches this
    
    # Change History (JSON array of changes)
    change_history = db.Column(db.JSON, nullable=True)
    
    # Relationships
    student = db.relationship('Student', backref='counters', lazy='select')
    subject = db.relationship('Subject', backref='student_counters', lazy='select')
    last_action_user = db.relationship('User', backref='counter_actions', lazy='select')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('student_id', 'subject_id', 'academic_year', 'semester', 
                        name='unique_student_subject_period'),
        CheckConstraint('counter_value >= 0', name='check_counter_non_negative'),
        CheckConstraint('total_increments >= 0', name='check_increments_non_negative'),
        CheckConstraint('total_decrements >= 0', name='check_decrements_non_negative'),
        CheckConstraint('auto_mute_threshold >= 0', name='check_auto_mute_threshold'),
        CheckConstraint('warning_threshold >= 0', name='check_warning_threshold'),
        Index('idx_counter_student_status', 'student_id', 'status'),
        Index('idx_counter_muted', 'is_muted', 'muted_at'),
        Index('idx_counter_telegram', 'telegram_user_id', 'telegram_notifications_enabled'),
    )
    
    def increment_counter(self, reason=None, triggered_by_user_id=None, value=1):
        """Increment the counter"""
        old_value = self.counter_value
        self.counter_value += value
        self.total_increments += value
        self.consecutive_increments += value
        self.consecutive_decrements = 0  # Reset decrement streak
        self.consecutive_on_time = 0     # Reset on-time streak
        
        # Update last action
        self.last_action = CounterActionEnum.INCREMENT
        self.last_action_at = datetime.utcnow()
        self.last_action_reason = reason
        self.last_action_by = triggered_by_user_id
        
        # Update increment tracking
        self.last_increment_at = datetime.utcnow()
        self.last_increment_reason = reason
        
        # Add to history
        self._add_to_history('increment', old_value, self.counter_value, reason, triggered_by_user_id)
        
        # Check auto-mute
        if self.counter_value >= self.auto_mute_threshold and not self.is_muted:
            self._auto_mute(f"العداد وصل إلى {self.counter_value}")
        
        # Check warning threshold
        if self.counter_value == self.warning_threshold and self.warning_threshold > 0:
            self._send_warning_notification()
        
        self.save()
        return self
    
    def decrement_counter(self, reason=None, triggered_by_user_id=None, value=1):
        """Decrement the counter"""
        old_value = self.counter_value
        self.counter_value = max(0, self.counter_value - value)
        self.total_decrements += value
        self.consecutive_decrements += value
        self.consecutive_increments = 0  # Reset increment streak
        self.consecutive_on_time += 1    # Increase on-time streak
        
        # Update last action
        self.last_action = CounterActionEnum.DECREMENT
        self.last_action_at = datetime.utcnow()
        self.last_action_reason = reason
        self.last_action_by = triggered_by_user_id
        
        # Update decrement tracking
        self.last_decrement_at = datetime.utcnow()
        self.last_decrement_reason = reason
        
        # Add to history
        self._add_to_history('decrement', old_value, self.counter_value, reason, triggered_by_user_id)
        
        # Check auto-unmute
        if self.counter_value == 0 and self.is_muted and self.auto_unmute_enabled:
            self._auto_unmute("العداد وصل إلى الصفر")
        
        self.save()
        return self
    
    def reset_counter(self, reason=None, triggered_by_user_id=None):
        """Reset counter to zero"""
        old_value = self.counter_value
        self.counter_value = 0
        self.total_resets += 1
        self.consecutive_increments = 0
        self.consecutive_decrements = 0
        
        # Update last action
        self.last_action = CounterActionEnum.RESET
        self.last_action_at = datetime.utcnow()
        self.last_action_reason = reason
        self.last_action_by = triggered_by_user_id
        
        # Add to history
        self._add_to_history('reset', old_value, 0, reason, triggered_by_user_id)
        
        # Auto-unmute if counter is reset
        if self.is_muted and self.auto_unmute_enabled:
            self._auto_unmute("تم إعادة تعيين العداد")
        
        self.save()
        return self
    
    def set_counter_value(self, new_value, reason=None, triggered_by_user_id=None):
        """Manually set counter value"""
        if new_value < 0:
            raise ValueError("Counter value cannot be negative")
        
        old_value = self.counter_value
        self.counter_value = new_value
        
        # Update last action
        self.last_action = CounterActionEnum.MANUAL_SET
        self.last_action_at = datetime.utcnow()
        self.last_action_reason = reason
        self.last_action_by = triggered_by_user_id
        
        # Add to history
        self._add_to_history('manual_set', old_value, new_value, reason, triggered_by_user_id)
        
        # Check mute/unmute based on new value
        if new_value >= self.auto_mute_threshold and not self.is_muted:
            self._auto_mute(f"تم تعيين العداد إلى {new_value}")
        elif new_value == 0 and self.is_muted and self.auto_unmute_enabled:
            self._auto_unmute("تم تعيين العداد إلى الصفر")
        
        self.save()
        return self
    
    def _auto_mute(self, reason):
        """Automatically mute the student"""
        self.is_muted = True
        self.muted_at = datetime.utcnow()
        self.mute_reason = reason
        self.status = CounterStatusEnum.MUTED
        
        # Send mute notification
        self._send_mute_notification()
    
    def _auto_unmute(self, reason):
        """Automatically unmute the student"""
        self.is_muted = False
        self.unmuted_at = datetime.utcnow()
        self.mute_reason = None
        self.status = CounterStatusEnum.ACTIVE
        
        # Send unmute notification
        self._send_unmute_notification()
    
    def manual_mute(self, reason, muted_by_user_id):
        """Manually mute the student"""
        if self.is_muted:
            raise ValueError("Student is already muted")
        
        self.is_muted = True
        self.muted_at = datetime.utcnow()
        self.mute_reason = reason
        self.status = CounterStatusEnum.MUTED
        self.last_action_by = muted_by_user_id
        
        # Add to history
        self._add_to_history('manual_mute', None, None, reason, muted_by_user_id)
        
        self.save()
        self._send_mute_notification()
    
    def manual_unmute(self, reason, unmuted_by_user_id):
        """Manually unmute the student"""
        if not self.is_muted:
            raise ValueError("Student is not muted")
        
        self.is_muted = False
        self.unmuted_at = datetime.utcnow()
        self.mute_reason = None
        self.status = CounterStatusEnum.ACTIVE
        self.last_action_by = unmuted_by_user_id
        
        # Add to history
        self._add_to_history('manual_unmute', None, None, reason, unmuted_by_user_id)
        
        self.save()
        self._send_unmute_notification()
    
    def update_assignment_stats(self, assignment_status):
        """Update assignment statistics"""
        self.total_assignments += 1
        
        if assignment_status == 'on_time':
            self.on_time_assignments += 1
        elif assignment_status == 'late':
            self.late_assignments += 1
        elif assignment_status == 'missed':
            self.missed_assignments += 1
        
        self.save()
    
    def update_attendance_stats(self, attendance_status):
        """Update attendance statistics"""
        self.total_lectures += 1
        
        if attendance_status == 'attended':
            self.attended_lectures += 1
        elif attendance_status == 'late':
            self.late_attendances += 1
        elif attendance_status == 'missed':
            self.missed_lectures += 1
        
        self.save()
    
    def get_performance_summary(self):
        """Get performance summary statistics"""
        # Assignment performance
        assignment_rate = (self.on_time_assignments / self.total_assignments * 100) if self.total_assignments > 0 else 0
        late_assignment_rate = (self.late_assignments / self.total_assignments * 100) if self.total_assignments > 0 else 0
        
        # Attendance performance
        attendance_rate = (self.attended_lectures / self.total_lectures * 100) if self.total_lectures > 0 else 0
        late_attendance_rate = (self.late_attendances / self.total_lectures * 100) if self.total_lectures > 0 else 0
        
        return {
            'counter_value': self.counter_value,
            'is_muted': self.is_muted,
            'status': self.status.value,
            'consecutive_on_time': self.consecutive_on_time,
            'assignment_performance': {
                'total': self.total_assignments,
                'on_time': self.on_time_assignments,
                'late': self.late_assignments,
                'missed': self.missed_assignments,
                'on_time_rate': round(assignment_rate, 2),
                'late_rate': round(late_assignment_rate, 2)
            },
            'attendance_performance': {
                'total': self.total_lectures,
                'attended': self.attended_lectures,
                'late': self.late_attendances,
                'missed': self.missed_lectures,
                'attendance_rate': round(attendance_rate, 2),
                'late_rate': round(late_attendance_rate, 2)
            }
        }
    
    def _add_to_history(self, action, old_value, new_value, reason, user_id):
        """Add action to change history"""
        if not self.change_history:
            self.change_history = []
        
        change_entry = {
            'action': action,
            'old_value': old_value,
            'new_value': new_value,
            'reason': reason,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.change_history.append(change_entry)
        
        # Keep only last 100 changes
        if len(self.change_history) > 100:
            self.change_history = self.change_history[-100:]
    
    def _send_warning_notification(self):
        """Send warning notification when threshold is reached"""
        if not self.telegram_notifications_enabled or not self.telegram_user_id:
            return
        
        # Create notification (integrate with your notification system)
        from .notifications import Notification, NotificationTypeEnum
        
        notification = Notification.create_notification(
            title="تحذير: العداد الذكي",
            message=f"وصل عدادك في مادة {self.subject.name} إلى {self.counter_value}. يرجى الانتباه لمواعيد التسليم والحضور.",
            notification_type=NotificationTypeEnum.WARNING,
            recipients={'student_id': self.student_id},
            channels=['telegram', 'in_app'],
            related_entity_type='counter',
            related_entity_id=self.id
        )
    
    def _send_mute_notification(self):
        """Send mute notification"""
        if not self.telegram_notifications_enabled or not self.telegram_user_id:
            return
        
        from .notifications import Notification, NotificationTypeEnum
        
        notification = Notification.create_notification(
            title="تم كتم حسابك",
            message=f"تم كتم حسابك في مادة {self.subject.name} بسبب: {self.mute_reason}. لن تتمكن من استلام الواجبات حتى يتم إلغاء الكتم.",
            notification_type=NotificationTypeEnum.WARNING,
            recipients={'student_id': self.student_id},
            channels=['telegram', 'in_app'],
            priority='high',
            related_entity_type='counter',
            related_entity_id=self.id
        )
    
    def _send_unmute_notification(self):
        """Send unmute notification"""
        if not self.telegram_notifications_enabled or not self.telegram_user_id:
            return
        
        from .notifications import Notification, NotificationTypeEnum
        
        notification = Notification.create_notification(
            title="تم إلغاء كتم حسابك",
            message=f"تم إلغاء كتم حسابك في مادة {self.subject.name}. يمكنك الآن استلام الواجبات والمشاركة مرة أخرى.",
            notification_type=NotificationTypeEnum.SYSTEM,
            recipients={'student_id': self.student_id},
            channels=['telegram', 'in_app'],
            priority='normal',
            related_entity_type='counter',
            related_entity_id=self.id
        )
    
    def to_dict(self, include_history=False, include_stats=True):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Add enum values
        data['status'] = self.status.value if self.status else None
        data['last_action'] = self.last_action.value if self.last_action else None
        data['semester'] = self.semester.value if self.semester else None
        
        # Format timestamps
        if self.muted_at:
            data['muted_at'] = self.muted_at.isoformat()
        
        if self.unmuted_at:
            data['unmuted_at'] = self.unmuted_at.isoformat()
        
        if self.last_action_at:
            data['last_action_at'] = self.last_action_at.isoformat()
        
        if self.last_increment_at:
            data['last_increment_at'] = self.last_increment_at.isoformat()
        
        if self.last_decrement_at:
            data['last_decrement_at'] = self.last_decrement_at.isoformat()
        
        # Include performance stats
        if include_stats:
            data['performance_summary'] = self.get_performance_summary()
        
        # Include change history if requested
        if not include_history:
            data.pop('change_history', None)
        
        return data
    
    @classmethod
    def get_or_create_counter(cls, student_id, subject_id, academic_year, semester):
        """Get existing counter or create new one"""
        counter = cls.query.filter_by(
            student_id=student_id,
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester
        ).first()
        
        if not counter:
            counter = cls(
                student_id=student_id,
                subject_id=subject_id,
                academic_year=academic_year,
                semester=semester
            )
            counter.save()
        
        return counter
    
    @classmethod
    def get_muted_students(cls, subject_id=None, academic_year=None, semester=None):
        """Get all muted students"""
        query = cls.query.filter_by(is_muted=True)
        
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        
        if academic_year:
            query = query.filter_by(academic_year=academic_year)
        
        if semester:
            query = query.filter_by(semester=semester)
        
        return query.all()
    
    @classmethod
    def get_high_risk_students(cls, threshold=2):
        """Get students with high counter values"""
        return cls.query.filter(cls.counter_value >= threshold).all()
    
    @classmethod
    def get_student_leaderboard(cls, subject_id, academic_year, semester, limit=10):
        """Get leaderboard of best performing students"""
        return cls.query.filter_by(
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester
        ).order_by(
            cls.counter_value.asc(),  # Lower counter is better
            cls.consecutive_on_time.desc()  # More consecutive on-time is better
        ).limit(limit).all()
    
    def validate_counter(self):
        """Validate counter data"""
        errors = []
        
        # Check counter value
        if self.counter_value < 0:
            errors.append("Counter value cannot be negative")
        
        # Check thresholds
        if self.auto_mute_threshold < 0:
            errors.append("Auto-mute threshold cannot be negative")
        
        if self.warning_threshold < 0:
            errors.append("Warning threshold cannot be negative")
        
        # Check academic year format
        if self.academic_year and not self.academic_year.match(r'^\d{4}-\d{4}$'):
            errors.append("Academic year must be in format YYYY-YYYY")
        
        return errors
    
    def save(self):
        """Save with validation"""
        errors = self.validate_counter()
        if errors:
            raise ValueError(f"Counter validation failed: {', '.join(errors)}")
        
        return super().save()
    
    def __repr__(self):
        return (f'<StudentCounter Student:{self.student_id} Subject:{self.subject_id} '
                f'Value:{self.counter_value} Status:{self.status.value if self.status else "Unknown"}>')