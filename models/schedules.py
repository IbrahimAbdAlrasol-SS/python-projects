"""
SCHEDULES Model - نموذج الجداول الدراسية
نموذج كامل للجداول الدراسية مع جميع العلاقات والتحققات
"""

from config.database import db
from .base import BaseModel
from .subjects import SemesterEnum
from .students import SectionEnum
from enum import Enum
from datetime import datetime, time
from sqlalchemy import CheckConstraint, UniqueConstraint

class DayOfWeekEnum(Enum):
    """أيام الأسبوع"""
    SUNDAY = 1
    MONDAY = 2
    TUESDAY = 3
    WEDNESDAY = 4
    THURSDAY = 5
    FRIDAY = 6
    SATURDAY = 7

class Schedule(BaseModel):
    """Schedule model for academic timetables"""
    
    __tablename__ = 'schedules'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False, index=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False, index=True)
    
    # Schedule Information
    section = db.Column(db.Enum(SectionEnum), nullable=False, index=True)
    day_of_week = db.Column(db.Integer, nullable=False, index=True)  # 1=Sunday, 7=Saturday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Academic Period
    academic_year = db.Column(db.String(9), nullable=False, index=True)  # 2023-2024
    semester = db.Column(db.Enum(SemesterEnum), nullable=False, index=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Relationships
    subject = db.relationship('Subject', backref='schedules', lazy='select')
    teacher = db.relationship('Teacher', backref='schedules', lazy='select')
    room = db.relationship('Room', backref='schedules', lazy='select')
    lectures = db.relationship('Lecture', backref='schedule', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('day_of_week >= 1 AND day_of_week <= 7', name='check_day_of_week'),
        CheckConstraint('start_time < end_time', name='check_time_order'),
        UniqueConstraint('teacher_id', 'day_of_week', 'start_time', 'academic_year', 'semester', 
                        name='unique_teacher_schedule'),
        UniqueConstraint('room_id', 'day_of_week', 'start_time', 'academic_year', 'semester',
                        name='unique_room_schedule'),
        UniqueConstraint('subject_id', 'section', 'day_of_week', 'start_time', 'academic_year', 'semester',
                        name='unique_section_schedule'),
    )
    
    def get_day_name(self, lang='ar'):
        """Get day name in Arabic or English"""
        day_names = {
            'ar': {
                1: 'الأحد', 2: 'الإثنين', 3: 'الثلاثاء', 4: 'الأربعاء',
                5: 'الخميس', 6: 'الجمعة', 7: 'السبت'
            },
            'en': {
                1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday',
                5: 'Thursday', 6: 'Friday', 7: 'Saturday'
            }
        }
        return day_names.get(lang, {}).get(self.day_of_week, 'Unknown')
    
    def get_duration_minutes(self):
        """Calculate duration in minutes"""
        if self.start_time and self.end_time:
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            return int((end - start).total_seconds() / 60)
        return 0
    
    def is_time_conflict(self, other_schedule):
        """Check if this schedule conflicts with another"""
        if (self.day_of_week == other_schedule.day_of_week and
            self.academic_year == other_schedule.academic_year and
            self.semester == other_schedule.semester):
            
            # Check time overlap
            return not (self.end_time <= other_schedule.start_time or 
                       self.start_time >= other_schedule.end_time)
        return False
    
    def validate_schedule(self):
        """Validate schedule constraints"""
        errors = []
        
        # Check academic year format
        if self.academic_year:
            if not self.academic_year.match(r'^\d{4}-\d{4}$'):
                errors.append("Academic year must be in format YYYY-YYYY")
        
        # Check day of week
        if not (1 <= self.day_of_week <= 7):
            errors.append("Day of week must be between 1 and 7")
        
        # Check time order
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                errors.append("Start time must be before end time")
        
        # Check minimum duration (at least 30 minutes)
        if self.get_duration_minutes() < 30:
            errors.append("Schedule duration must be at least 30 minutes")
        
        # Check maximum duration (no more than 4 hours)
        if self.get_duration_minutes() > 240:
            errors.append("Schedule duration cannot exceed 4 hours")
        
        return errors
    
    def to_dict(self, include_relations=False):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Add enum values
        data['section'] = self.section.value if self.section else None
        data['semester'] = self.semester.value if self.semester else None
        data['day_name_ar'] = self.get_day_name('ar')
        data['day_name_en'] = self.get_day_name('en')
        data['duration_minutes'] = self.get_duration_minutes()
        
        # Format times
        if self.start_time:
            data['start_time'] = self.start_time.strftime('%H:%M')
        if self.end_time:
            data['end_time'] = self.end_time.strftime('%H:%M')
        
        # Include related data if requested
        if include_relations:
            if self.subject:
                data['subject'] = {
                    'id': self.subject.id,
                    'code': self.subject.code,
                    'name': self.subject.name,
                    'credit_hours': self.subject.credit_hours
                }
            
            if self.teacher:
                data['teacher'] = {
                    'id': self.teacher.id,
                    'employee_id': self.teacher.employee_id,
                    'full_name': self.teacher.user.full_name if self.teacher.user else None,
                    'department': self.teacher.department
                }
            
            if self.room:
                data['room'] = {
                    'id': self.room.id,
                    'name': self.room.name,
                    'building': self.room.building,
                    'floor': self.room.floor,
                    'capacity': self.room.capacity
                }
        
        return data
    
    @classmethod
    def get_schedule_by_section_and_semester(cls, section, academic_year, semester):
        """Get schedule for a specific section and semester"""
        return cls.query.filter_by(
            section=section,
            academic_year=academic_year,
            semester=semester,
            is_active=True
        ).order_by(cls.day_of_week, cls.start_time).all()
    
    @classmethod
    def get_teacher_schedule(cls, teacher_id, academic_year, semester):
        """Get teacher's schedule for specific semester"""
        return cls.query.filter_by(
            teacher_id=teacher_id,
            academic_year=academic_year,
            semester=semester,
            is_active=True
        ).order_by(cls.day_of_week, cls.start_time).all()
    
    @classmethod
    def get_room_schedule(cls, room_id, academic_year, semester):
        """Get room's schedule for specific semester"""
        return cls.query.filter_by(
            room_id=room_id,
            academic_year=academic_year,
            semester=semester,
            is_active=True
        ).order_by(cls.day_of_week, cls.start_time).all()
    
    @classmethod
    def check_conflicts(cls, teacher_id, room_id, day_of_week, start_time, end_time, 
                       academic_year, semester, exclude_id=None):
        """Check for scheduling conflicts"""
        conflicts = []
        
        # Check teacher conflicts
        teacher_schedules = cls.query.filter_by(
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            academic_year=academic_year,
            semester=semester,
            is_active=True
        )
        
        if exclude_id:
            teacher_schedules = teacher_schedules.filter(cls.id != exclude_id)
        
        for schedule in teacher_schedules:
            if not (end_time <= schedule.start_time or start_time >= schedule.end_time):
                conflicts.append(f"Teacher conflict with schedule ID {schedule.id}")
        
        # Check room conflicts
        room_schedules = cls.query.filter_by(
            room_id=room_id,
            day_of_week=day_of_week,
            academic_year=academic_year,
            semester=semester,
            is_active=True
        )
        
        if exclude_id:
            room_schedules = room_schedules.filter(cls.id != exclude_id)
        
        for schedule in room_schedules:
            if not (end_time <= schedule.start_time or start_time >= schedule.end_time):
                conflicts.append(f"Room conflict with schedule ID {schedule.id}")
        
        return conflicts
    
    @classmethod
    def get_current_semester_schedules(cls):
        """Get schedules for current semester (you can implement logic for current semester)"""
        # This would need implementation based on your academic calendar logic
        from datetime import datetime
        current_year = datetime.now().year
        academic_year = f"{current_year}-{current_year + 1}"
        
        # Simple logic - can be enhanced
        current_month = datetime.now().month
        if 9 <= current_month <= 12:
            semester = SemesterEnum.FIRST
        elif 2 <= current_month <= 6:
            semester = SemesterEnum.SECOND
        else:
            semester = SemesterEnum.SUMMER
        
        return cls.query.filter_by(
            academic_year=academic_year,
            semester=semester,
            is_active=True
        ).all()
    
    def save(self):
        """Save with validation"""
        # Validate before saving
        errors = self.validate_schedule()
        if errors:
            raise ValueError(f"Schedule validation failed: {', '.join(errors)}")
        
        # Check for conflicts
        conflicts = self.check_conflicts(
            self.teacher_id, self.room_id, self.day_of_week,
            self.start_time, self.end_time, self.academic_year, self.semester,
            exclude_id=self.id if self.id else None
        )
        
        if conflicts:
            raise ValueError(f"Schedule conflicts detected: {', '.join(conflicts)}")
        
        return super().save()
    
    def __repr__(self):
        return (f'<Schedule {self.subject.code if self.subject else "Unknown"} - '
                f'{self.section.value if self.section else "Unknown"} - '
                f'{self.get_day_name("en")} {self.start_time}-{self.end_time}>')