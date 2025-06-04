"""
ASSIGNMENTS Model - نموذج الواجبات
نموذج كامل للواجبات مع العداد الذكي والبوت
"""

from config.database import db
from .base import BaseModel
from .subjects import SemesterEnum
from .students import SectionEnum
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

class AssignmentStatusEnum(Enum):
    """حالة الواجب"""
    DRAFT = 'draft'              # مسودة
    PUBLISHED = 'published'      # منشور
    ACTIVE = 'active'           # نشط (متاح للتسليم)
    CLOSED = 'closed'           # مغلق
    GRADED = 'graded'           # تم التقييم
    ARCHIVED = 'archived'        # مؤرشف

class AssignmentTypeEnum(Enum):
    """نوع الواجب"""
    HOMEWORK = 'homework'        # واجب منزلي
    PROJECT = 'project'          # مشروع
    QUIZ = 'quiz'               # اختبار قصير
    RESEARCH = 'research'        # بحث
    PRESENTATION = 'presentation' # عرض تقديمي
    LAB_WORK = 'lab_work'       # عمل مختبر

class Assignment(BaseModel):
    """Assignment model for homework and projects"""
    
    __tablename__ = 'assignments'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Assignment Information
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    
    # Type and Category
    assignment_type = db.Column(db.Enum(AssignmentTypeEnum), default=AssignmentTypeEnum.HOMEWORK, nullable=False)
    status = db.Column(db.Enum(AssignmentStatusEnum), default=AssignmentStatusEnum.DRAFT, nullable=False, index=True)
    
    # Target Students
    target_sections = db.Column(db.JSON, nullable=False)  # ['A', 'B', 'C']
    target_year = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(9), nullable=False)  # 2023-2024
    semester = db.Column(db.Enum(SemesterEnum), nullable=False)
    
    # Timing
    published_at = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False, index=True)
    late_submission_allowed = db.Column(db.Boolean, default=True)
    late_deadline = db.Column(db.DateTime, nullable=True)
    
    # Grading
    max_score = db.Column(db.Numeric(5, 2), default=100.00)
    weight_percentage = db.Column(db.Numeric(5, 2), default=10.00)  # Weight in final grade
    grading_criteria = db.Column(db.JSON, nullable=True)  # Detailed grading rubric
    
    # Smart Counter Integration
    affects_counter = db.Column(db.Boolean, default=True)  # Affects student counter
    counter_increment_value = db.Column(db.Integer, default=1)  # How much to increment for late/missing
    counter_decrement_value = db.Column(db.Integer, default=1)  # How much to decrement for on-time
    
    # Submission Settings
    allow_file_upload = db.Column(db.Boolean, default=True)
    allowed_file_types = db.Column(db.JSON, nullable=True)  # ['.pdf', '.docx', '.txt']
    max_file_size_mb = db.Column(db.Integer, default=10)
    allow_text_submission = db.Column(db.Boolean, default=True)
    allow_link_submission = db.Column(db.Boolean, default=False)
    
    # Statistics (calculated fields)
    total_submissions = db.Column(db.Integer, default=0)
    on_time_submissions = db.Column(db.Integer, default=0)
    late_submissions = db.Column(db.Integer, default=0)
    pending_submissions = db.Column(db.Integer, default=0)
    graded_submissions = db.Column(db.Integer, default=0)
    
    # Telegram Bot Integration
    telegram_message_id = db.Column(db.BigInteger, nullable=True)
    telegram_channel_id = db.Column(db.BigInteger, nullable=True)
    bot_notifications_enabled = db.Column(db.Boolean, default=True)
    
    # Metadata
    notes = db.Column(db.Text, nullable=True)
    is_visible_to_students = db.Column(db.Boolean, default=True)
    
    # Relationships
    subject = db.relationship('Subject', backref='assignments', lazy='select')
    teacher = db.relationship('Teacher', backref='assignments', lazy='select')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_assignments', lazy='select')
    submissions = db.relationship('Submission', backref='assignment', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('due_date > created_at', name='check_due_date_future'),
        CheckConstraint('late_deadline >= due_date', name='check_late_deadline_order'),
        CheckConstraint('max_score > 0', name='check_max_score_positive'),
        CheckConstraint('weight_percentage >= 0 AND weight_percentage <= 100', name='check_weight_percentage'),
        CheckConstraint('max_file_size_mb > 0', name='check_file_size_positive'),
        CheckConstraint('counter_increment_value >= 0', name='check_counter_increment'),
        CheckConstraint('counter_decrement_value >= 0', name='check_counter_decrement'),
        Index('idx_assignment_due_date', 'due_date', 'status'),
        Index('idx_assignment_target', 'target_year', 'academic_year', 'semester'),
        Index('idx_assignment_teacher_status', 'teacher_id', 'status'),
    )
    
    def publish_assignment(self):
        """Publish the assignment"""
        if self.status != AssignmentStatusEnum.DRAFT:
            raise ValueError("Only draft assignments can be published")
        
        self.status = AssignmentStatusEnum.PUBLISHED
        self.published_at = datetime.utcnow()
        
        # If due date is in future, mark as active
        if self.due_date > datetime.utcnow():
            self.status = AssignmentStatusEnum.ACTIVE
        
        self.save()
        return self
    
    def close_assignment(self):
        """Close the assignment (no more submissions)"""
        if self.status not in [AssignmentStatusEnum.ACTIVE, AssignmentStatusEnum.PUBLISHED]:
            raise ValueError("Only active assignments can be closed")
        
        self.status = AssignmentStatusEnum.CLOSED
        self.save()
        return self
    
    def reopen_assignment(self, new_due_date=None):
        """Reopen closed assignment"""
        if self.status != AssignmentStatusEnum.CLOSED:
            raise ValueError("Only closed assignments can be reopened")
        
        if new_due_date:
            self.due_date = new_due_date
            if new_due_date > datetime.utcnow():
                self.status = AssignmentStatusEnum.ACTIVE
        else:
            self.status = AssignmentStatusEnum.ACTIVE
        
        self.save()
        return self
    
    def is_submission_allowed(self):
        """Check if submissions are still allowed"""
        now = datetime.utcnow()
        
        if self.status != AssignmentStatusEnum.ACTIVE:
            return False
        
        # Check if within deadline
        if now <= self.due_date:
            return True
        
        # Check if late submission is allowed
        if self.late_submission_allowed and self.late_deadline:
            return now <= self.late_deadline
        
        return False
    
    def is_late_submission(self, submission_time=None):
        """Check if submission time is considered late"""
        if not submission_time:
            submission_time = datetime.utcnow()
        
        return submission_time > self.due_date
    
    def get_time_remaining(self):
        """Get time remaining until due date"""
        if self.due_date:
            remaining = (self.due_date - datetime.utcnow()).total_seconds()
            return max(0, remaining)
        return 0
    
    def get_late_time_remaining(self):
        """Get time remaining until late deadline"""
        if self.late_deadline:
            remaining = (self.late_deadline - datetime.utcnow()).total_seconds()
            return max(0, remaining)
        return 0
    
    def get_submission_rate(self):
        """Calculate submission rate percentage"""
        expected_submissions = self.get_expected_submissions_count()
        if expected_submissions > 0:
            return round((self.total_submissions / expected_submissions) * 100, 2)
        return 0.0
    
    def get_on_time_rate(self):
        """Calculate on-time submission rate"""
        if self.total_submissions > 0:
            return round((self.on_time_submissions / self.total_submissions) * 100, 2)
        return 0.0
    
    def get_expected_submissions_count(self):
        """Get expected number of submissions based on target sections"""
        from .students import Student
        
        total_expected = 0
        for section in self.target_sections:
            count = Student.query.filter_by(
                section=section,
                study_year=self.target_year,
                academic_status='active'
            ).count()
            total_expected += count
        
        return total_expected
    
    def update_statistics(self):
        """Update assignment statistics"""
        # Count submissions by status
        from .submissions import Submission, SubmissionStatusEnum
        
        self.total_submissions = self.submissions.count()
        
        # Count on-time submissions
        self.on_time_submissions = self.submissions.filter(
            Submission.submitted_at <= self.due_date
        ).count()
        
        # Count late submissions
        self.late_submissions = self.submissions.filter(
            Submission.submitted_at > self.due_date
        ).count()
        
        # Count pending submissions
        self.pending_submissions = self.submissions.filter_by(
            status=SubmissionStatusEnum.SUBMITTED
        ).count()
        
        # Count graded submissions
        self.graded_submissions = self.submissions.filter_by(
            status=SubmissionStatusEnum.GRADED
        ).count()
        
        self.save()
    
    def get_student_submission(self, student_id):
        """Get submission for specific student"""
        return self.submissions.filter_by(student_id=student_id).first()
    
    def can_student_submit(self, student_id):
        """Check if specific student can submit"""
        # Check if assignment allows submissions
        if not self.is_submission_allowed():
            return False, "Assignment is closed for submissions"
        
        # Check if student is in target sections
        from .students import Student
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found"
        
        if student.section.value not in self.target_sections:
            return False, "Assignment not assigned to your section"
        
        if student.study_year != self.target_year:
            return False, "Assignment not assigned to your year"
        
        # Check if student already submitted
        existing_submission = self.get_student_submission(student_id)
        if existing_submission:
            return False, "You have already submitted this assignment"
        
        return True, "Can submit"
    
    def auto_close_if_expired(self):
        """Auto-close assignment if past deadline"""
        now = datetime.utcnow()
        
        if self.status == AssignmentStatusEnum.ACTIVE:
            deadline = self.late_deadline if self.late_deadline else self.due_date
            
            if now > deadline:
                self.status = AssignmentStatusEnum.CLOSED
                self.save()
                return True
        
        return False
    
    def to_dict(self, include_relations=False, include_statistics=True):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Add enum values
        data['assignment_type'] = self.assignment_type.value if self.assignment_type else None
        data['status'] = self.status.value if self.status else None
        data['semester'] = self.semester.value if self.semester else None
        
        # Format timestamps
        if self.published_at:
            data['published_at'] = self.published_at.isoformat()
        
        if self.due_date:
            data['due_date'] = self.due_date.isoformat()
        
        if self.late_deadline:
            data['late_deadline'] = self.late_deadline.isoformat()
        
        # Add computed fields
        data['is_submission_allowed'] = self.is_submission_allowed()
        data['time_remaining_seconds'] = self.get_time_remaining()
        data['late_time_remaining_seconds'] = self.get_late_time_remaining()
        
        # Include statistics
        if include_statistics:
            data['submission_rate'] = self.get_submission_rate()
            data['on_time_rate'] = self.get_on_time_rate()
            data['expected_submissions'] = self.get_expected_submissions_count()
        
        # Include related data if requested
        if include_relations:
            if self.subject:
                data['subject'] = {
                    'id': self.subject.id,
                    'code': self.subject.code,
                    'name': self.subject.name,
                    'credit_hours': self.subject.credit_hours
                }
            
            if self.teacher and self.teacher.user:
                data['teacher'] = {
                    'id': self.teacher.id,
                    'employee_id': self.teacher.employee_id,
                    'full_name': self.teacher.user.full_name,
                    'department': self.teacher.department
                }
        
        # Format numeric fields
        if self.max_score:
            data['max_score'] = float(self.max_score)
        
        if self.weight_percentage:
            data['weight_percentage'] = float(self.weight_percentage)
        
        return data
    
    @classmethod
    def get_active_assignments(cls, student_id=None, section=None, year=None):
        """Get active assignments"""
        query = cls.query.filter_by(
            status=AssignmentStatusEnum.ACTIVE,
            is_visible_to_students=True
        )
        
        if section:
            query = query.filter(cls.target_sections.contains([section]))
        
        if year:
            query = query.filter_by(target_year=year)
        
        return query.order_by(cls.due_date).all()
    
    @classmethod
    def get_teacher_assignments(cls, teacher_id, status=None):
        """Get assignments by teacher"""
        query = cls.query.filter_by(teacher_id=teacher_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(cls.due_date.desc()).all()
    
    @classmethod
    def get_overdue_assignments(cls):
        """Get overdue assignments that need to be closed"""
        now = datetime.utcnow()
        
        return cls.query.filter(
            cls.status == AssignmentStatusEnum.ACTIVE,
            db.or_(
                db.and_(cls.late_deadline.isnot(None), cls.late_deadline < now),
                db.and_(cls.late_deadline.is_(None), cls.due_date < now)
            )
        ).all()
    
    @classmethod
    def create_assignment(cls, title, description, subject_id, teacher_id, due_date, 
                         target_sections, target_year, created_by_user_id, **kwargs):
        """Create new assignment"""
        assignment = cls(
            title=title,
            description=description,
            subject_id=subject_id,
            teacher_id=teacher_id,
            due_date=due_date,
            target_sections=target_sections,
            target_year=target_year,
            created_by=created_by_user_id,
            **kwargs
        )
        
        # Set academic year and semester based on current date or due date
        from datetime import datetime
        year = due_date.year if due_date else datetime.now().year
        assignment.academic_year = f"{year}-{year + 1}"
        
        # Simple semester logic - can be enhanced
        month = due_date.month if due_date else datetime.now().month
        if 9 <= month <= 12:
            assignment.semester = SemesterEnum.FIRST
        elif 2 <= month <= 6:
            assignment.semester = SemesterEnum.SECOND
        else:
            assignment.semester = SemesterEnum.SUMMER
        
        assignment.save()
        return assignment
    
    def validate_assignment(self):
        """Validate assignment data"""
        errors = []
        
        # Check title
        if not self.title or len(self.title.strip()) < 3:
            errors.append("Title must be at least 3 characters long")
        
        # Check description
        if not self.description or len(self.description.strip()) < 10:
            errors.append("Description must be at least 10 characters long")
        
        # Check target sections
        if not self.target_sections or len(self.target_sections) == 0:
            errors.append("At least one target section must be specified")
        
        # Check due date
        if self.due_date and self.due_date <= datetime.utcnow():
            errors.append("Due date must be in the future")
        
        # Check late deadline
        if self.late_deadline and self.due_date:
            if self.late_deadline <= self.due_date:
                errors.append("Late deadline must be after due date")
        
        # Check score and weight
        if self.max_score <= 0:
            errors.append("Max score must be positive")
        
        if not (0 <= self.weight_percentage <= 100):
            errors.append("Weight percentage must be between 0 and 100")
        
        return errors
    
    def save(self):
        """Save with validation"""
        errors = self.validate_assignment()
        if errors:
            raise ValueError(f"Assignment validation failed: {', '.join(errors)}")
        
        return super().save()
    
    def __repr__(self):
        return (f'<Assignment {self.id}: {self.title[:30]}... - '
                f'{self.status.value if self.status else "Unknown"}>')