"""
SUBMISSIONS Model - نموذج تسليم الواجبات
نموذج كامل لتسليم الواجبات مع التقييم والعداد الذكي
"""

from config.database import db
from .base import BaseModel
from enum import Enum
from datetime import datetime
from sqlalchemy import CheckConstraint, Index, UniqueConstraint
import os
import hashlib

class SubmissionStatusEnum(Enum):
    """حالة التسليم"""
    DRAFT = 'draft'              # مسودة
    SUBMITTED = 'submitted'      # مُسلم
    UNDER_REVIEW = 'under_review' # تحت المراجعة
    GRADED = 'graded'           # تم التقييم
    RETURNED = 'returned'       # تم الإرجاع للتعديل
    LATE = 'late'               # تسليم متأخر
    REJECTED = 'rejected'       # مرفوض

class SubmissionTypeEnum(Enum):
    """نوع التسليم"""
    FILE_UPLOAD = 'file_upload'     # رفع ملف
    TEXT_SUBMISSION = 'text_submission' # نص مكتوب
    LINK_SUBMISSION = 'link_submission' # رابط خارجي
    MIXED = 'mixed'                 # مختلط

class Submission(BaseModel):
    """Submission model for assignment submissions"""
    
    __tablename__ = 'submissions'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    graded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Submission Content
    submission_type = db.Column(db.Enum(SubmissionTypeEnum), default=SubmissionTypeEnum.TEXT_SUBMISSION, nullable=False)
    text_content = db.Column(db.Text, nullable=True)
    submission_title = db.Column(db.String(255), nullable=True)
    
    # File Information
    file_path = db.Column(db.String(500), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)
    file_size_bytes = db.Column(db.BigInteger, nullable=True)
    file_type = db.Column(db.String(50), nullable=True)
    file_hash = db.Column(db.String(64), nullable=True)  # SHA-256 hash
    
    # Link Information
    submission_url = db.Column(db.String(500), nullable=True)
    url_title = db.Column(db.String(255), nullable=True)
    url_description = db.Column(db.Text, nullable=True)
    
    # Status and Timing
    status = db.Column(db.Enum(SubmissionStatusEnum), default=SubmissionStatusEnum.DRAFT, nullable=False, index=True)
    submitted_at = db.Column(db.DateTime, nullable=True, index=True)
    last_modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Grading
    score = db.Column(db.Numeric(5, 2), nullable=True)
    max_possible_score = db.Column(db.Numeric(5, 2), nullable=True)
    percentage_score = db.Column(db.Numeric(5, 2), nullable=True)
    grade_letter = db.Column(db.String(5), nullable=True)  # A+, A, B+, etc.
    
    # Feedback
    teacher_feedback = db.Column(db.Text, nullable=True)
    private_notes = db.Column(db.Text, nullable=True)  # Internal notes
    graded_at = db.Column(db.DateTime, nullable=True)
    feedback_at = db.Column(db.DateTime, nullable=True)
    
    # Late Submission
    is_late = db.Column(db.Boolean, default=False, nullable=False, index=True)
    late_penalty_applied = db.Column(db.Boolean, default=False)
    late_penalty_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    original_score = db.Column(db.Numeric(5, 2), nullable=True)  # Score before penalty
    
    # Smart Counter Integration
    counter_updated = db.Column(db.Boolean, default=False)
    counter_action = db.Column(db.String(20), nullable=True)  # 'increment', 'decrement', 'none'
    counter_value = db.Column(db.Integer, default=0)
    
    # Submission Metadata
    submission_ip = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    platform = db.Column(db.String(50), nullable=True)  # web, mobile, telegram
    
    # Plagiarism Detection (placeholder for future)
    plagiarism_checked = db.Column(db.Boolean, default=False)
    plagiarism_score = db.Column(db.Numeric(5, 2), nullable=True)
    plagiarism_details = db.Column(db.JSON, nullable=True)
    
    # Version Control
    version_number = db.Column(db.Integer, default=1)
    previous_submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=True)
    
    # Telegram Bot Integration
    telegram_message_id = db.Column(db.BigInteger, nullable=True)
    telegram_file_id = db.Column(db.String(255), nullable=True)
    
    # Relationships
    # assignment relationship is defined in assignments.py
    student = db.relationship('Student', backref='submissions', lazy='select')
    grader = db.relationship('User', foreign_keys=[graded_by], backref='graded_submissions', lazy='select')
    previous_submission = db.relationship('Submission', remote_side=[id], backref='revisions')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('assignment_id', 'student_id', 'version_number', 
                        name='unique_student_assignment_version'),
        CheckConstraint('score >= 0', name='check_score_non_negative'),
        CheckConstraint('percentage_score >= 0 AND percentage_score <= 100', name='check_percentage_range'),
        CheckConstraint('file_size_bytes >= 0', name='check_file_size_non_negative'),
        CheckConstraint('late_penalty_percentage >= 0 AND late_penalty_percentage <= 100', 
                       name='check_penalty_range'),
        CheckConstraint('version_number >= 1', name='check_version_positive'),
        Index('idx_submission_status_date', 'status', 'submitted_at'),
        Index('idx_submission_late', 'is_late', 'submitted_at'),
        Index('idx_submission_grading', 'graded_by', 'graded_at'),
    )
    
    def submit_submission(self, submitted_by_student=True):
        """Submit the submission"""
        if self.status != SubmissionStatusEnum.DRAFT:
            raise ValueError("Only draft submissions can be submitted")
        
        if not self.assignment:
            raise ValueError("Assignment not found")
        
        # Check if submission is allowed
        can_submit, reason = self.assignment.can_student_submit(self.student_id)
        if not can_submit:
            raise ValueError(f"Cannot submit: {reason}")
        
        # Check if submission is late
        now = datetime.utcnow()
        self.is_late = now > self.assignment.due_date
        
        # Set status
        self.status = SubmissionStatusEnum.LATE if self.is_late else SubmissionStatusEnum.SUBMITTED
        self.submitted_at = now
        
        # Set max possible score from assignment
        self.max_possible_score = self.assignment.max_score
        
        # Update counter if needed
        if self.assignment.affects_counter and not self.counter_updated:
            self._update_student_counter()
        
        self.save()
        
        # Update assignment statistics
        self.assignment.update_statistics()
        
        return self
    
    def save_as_draft(self):
        """Save submission as draft"""
        self.status = SubmissionStatusEnum.DRAFT
        self.last_modified_at = datetime.utcnow()
        self.save()
    
    def grade_submission(self, score, feedback=None, graded_by_user_id=None, apply_late_penalty=True):
        """Grade the submission"""
        if self.status not in [SubmissionStatusEnum.SUBMITTED, SubmissionStatusEnum.LATE, SubmissionStatusEnum.UNDER_REVIEW]:
            raise ValueError("Can only grade submitted submissions")
        
        if not self.max_possible_score:
            self.max_possible_score = self.assignment.max_score if self.assignment else 100
        
        if score < 0 or score > self.max_possible_score:
            raise ValueError(f"Score must be between 0 and {self.max_possible_score}")
        
        # Store original score
        self.original_score = score
        
        # Apply late penalty if applicable
        if self.is_late and apply_late_penalty and not self.late_penalty_applied:
            penalty_percentage = 10.0  # Default 10% penalty - can be configurable
            penalty_amount = score * (penalty_percentage / 100)
            score = max(0, score - penalty_amount)
            
            self.late_penalty_applied = True
            self.late_penalty_percentage = penalty_percentage
        
        # Set grade
        self.score = score
        self.percentage_score = (score / self.max_possible_score) * 100 if self.max_possible_score > 0 else 0
        self.grade_letter = self._calculate_grade_letter(self.percentage_score)
        
        # Set feedback
        if feedback:
            self.teacher_feedback = feedback
            self.feedback_at = datetime.utcnow()
        
        # Set grading info
        self.graded_by = graded_by_user_id
        self.graded_at = datetime.utcnow()
        self.status = SubmissionStatusEnum.GRADED
        
        self.save()
        
        # Update assignment statistics
        if self.assignment:
            self.assignment.update_statistics()
        
        return self
    
    def return_for_revision(self, feedback, returned_by_user_id=None):
        """Return submission for revision"""
        if self.status not in [SubmissionStatusEnum.SUBMITTED, SubmissionStatusEnum.UNDER_REVIEW]:
            raise ValueError("Can only return submitted submissions")
        
        self.status = SubmissionStatusEnum.RETURNED
        self.teacher_feedback = feedback
        self.feedback_at = datetime.utcnow()
        
        if returned_by_user_id:
            self.graded_by = returned_by_user_id
        
        self.save()
        return self
    
    def create_revision(self, student_id):
        """Create a new revision of this submission"""
        if self.status != SubmissionStatusEnum.RETURNED:
            raise ValueError("Can only create revision from returned submission")
        
        # Create new submission as revision
        revision = Submission(
            assignment_id=self.assignment_id,
            student_id=student_id,
            submission_type=self.submission_type,
            text_content=self.text_content,
            submission_title=self.submission_title,
            submission_url=self.submission_url,
            url_title=self.url_title,
            url_description=self.url_description,
            version_number=self.version_number + 1,
            previous_submission_id=self.id,
            status=SubmissionStatusEnum.DRAFT
        )
        
        revision.save()
        return revision
    
    def upload_file(self, file_data, original_filename, file_type=None):
        """Upload file for submission"""
        if not self.assignment:
            raise ValueError("Assignment not found")
        
        if not self.assignment.allow_file_upload:
            raise ValueError("File upload not allowed for this assignment")
        
        # Check file type
        if self.assignment.allowed_file_types:
            file_ext = os.path.splitext(original_filename)[1].lower()
            if file_ext not in self.assignment.allowed_file_types:
                raise ValueError(f"File type {file_ext} not allowed")
        
        # Check file size
        file_size = len(file_data)
        max_size_bytes = self.assignment.max_file_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise ValueError(f"File size exceeds limit of {self.assignment.max_file_size_mb}MB")
        
        # Generate file hash
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Generate file path (implement your file storage logic)
        file_path = self._generate_file_path(original_filename)
        
        # Store file info
        self.file_path = file_path
        self.original_filename = original_filename
        self.file_size_bytes = file_size
        self.file_type = file_type or os.path.splitext(original_filename)[1].lower()
        self.file_hash = file_hash
        
        if self.submission_type == SubmissionTypeEnum.TEXT_SUBMISSION:
            self.submission_type = SubmissionTypeEnum.FILE_UPLOAD
        elif self.submission_type in [SubmissionTypeEnum.LINK_SUBMISSION]:
            self.submission_type = SubmissionTypeEnum.MIXED
        
        self.last_modified_at = datetime.utcnow()
        self.save()
        
        return file_path
    
    def _generate_file_path(self, filename):
        """Generate unique file path"""
        # Implement your file storage logic here
        import uuid
        unique_id = str(uuid.uuid4())
        file_ext = os.path.splitext(filename)[1]
        return f"submissions/{self.assignment_id}/{self.student_id}/{unique_id}{file_ext}"
    
    def _calculate_grade_letter(self, percentage):
        """Calculate letter grade from percentage"""
        if percentage >= 90:
            return 'A+'
        elif percentage >= 85:
            return 'A'
        elif percentage >= 80:
            return 'B+'
        elif percentage >= 75:
            return 'B'
        elif percentage >= 70:
            return 'C+'
        elif percentage >= 65:
            return 'C'
        elif percentage >= 60:
            return 'D+'
        elif percentage >= 55:
            return 'D'
        else:
            return 'F'
    
    def _update_student_counter(self):
        """Update student's smart counter based on submission timing"""
        if not self.assignment or not self.assignment.affects_counter:
            return
        
        from .student_counters import StudentCounter
        
        # Determine counter action
        if self.is_late:
            action = 'increment'
            value = self.assignment.counter_increment_value
        else:
            action = 'decrement'
            value = self.assignment.counter_decrement_value
        
        # Update counter (implement your counter logic)
        # This would integrate with your smart counter system
        
        self.counter_updated = True
        self.counter_action = action
        self.counter_value = value
    
    def get_submission_summary(self):
        """Get summary of submission"""
        summary = {
            'has_text': bool(self.text_content),
            'has_file': bool(self.file_path),
            'has_url': bool(self.submission_url),
            'is_complete': self._is_submission_complete(),
            'word_count': len(self.text_content.split()) if self.text_content else 0,
            'character_count': len(self.text_content) if self.text_content else 0
        }
        
        if self.file_path:
            summary['file_info'] = {
                'filename': self.original_filename,
                'size_mb': round(self.file_size_bytes / (1024 * 1024), 2) if self.file_size_bytes else 0,
                'type': self.file_type
            }
        
        return summary
    
    def _is_submission_complete(self):
        """Check if submission has required content"""
        if self.submission_type == SubmissionTypeEnum.TEXT_SUBMISSION:
            return bool(self.text_content and self.text_content.strip())
        elif self.submission_type == SubmissionTypeEnum.FILE_UPLOAD:
            return bool(self.file_path)
        elif self.submission_type == SubmissionTypeEnum.LINK_SUBMISSION:
            return bool(self.submission_url)
        elif self.submission_type == SubmissionTypeEnum.MIXED:
            return bool(self.text_content or self.file_path or self.submission_url)
        
        return False
    
    def to_dict(self, include_sensitive=False, include_file_content=False):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Add enum values
        data['submission_type'] = self.submission_type.value if self.submission_type else None
        data['status'] = self.status.value if self.status else None
        
        # Format timestamps
        if self.submitted_at:
            data['submitted_at'] = self.submitted_at.isoformat()
        
        if self.last_modified_at:
            data['last_modified_at'] = self.last_modified_at.isoformat()
        
        if self.graded_at:
            data['graded_at'] = self.graded_at.isoformat()
        
        if self.feedback_at:
            data['feedback_at'] = self.feedback_at.isoformat()
        
        # Add computed fields
        data['submission_summary'] = self.get_submission_summary()
        data['is_complete'] = self._is_submission_complete()
        
        # Format numeric fields
        if self.score:
            data['score'] = float(self.score)
        
        if self.max_possible_score:
            data['max_possible_score'] = float(self.max_possible_score)
        
        if self.percentage_score:
            data['percentage_score'] = float(self.percentage_score)
        
        if self.late_penalty_percentage:
            data['late_penalty_percentage'] = float(self.late_penalty_percentage)
        
        if self.original_score:
            data['original_score'] = float(self.original_score)
        
        # Remove sensitive data by default
        if not include_sensitive:
            data.pop('submission_ip', None)
            data.pop('user_agent', None)
            data.pop('private_notes', None)
            data.pop('file_hash', None)
        
        # Remove file content path for security
        if not include_file_content:
            data.pop('file_path', None)
        
        return data
    
    @classmethod
    def get_student_submissions(cls, student_id, assignment_id=None, status=None):
        """Get submissions for a student"""
        query = cls.query.filter_by(student_id=student_id)
        
        if assignment_id:
            query = query.filter_by(assignment_id=assignment_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(cls.submitted_at.desc()).all()
    
    @classmethod
    def get_assignment_submissions(cls, assignment_id, status=None, include_drafts=False):
        """Get submissions for an assignment"""
        query = cls.query.filter_by(assignment_id=assignment_id)
        
        if status:
            query = query.filter_by(status=status)
        elif not include_drafts:
            query = query.filter(cls.status != SubmissionStatusEnum.DRAFT)
        
        return query.order_by(cls.submitted_at).all()
    
    @classmethod
    def get_pending_grading(cls, teacher_id=None):
        """Get submissions pending grading"""
        query = cls.query.filter(
            cls.status.in_([SubmissionStatusEnum.SUBMITTED, SubmissionStatusEnum.LATE])
        )
        
        if teacher_id:
            from .assignments import Assignment
            query = query.join(Assignment).filter(Assignment.teacher_id == teacher_id)
        
        return query.order_by(cls.submitted_at).all()
    
    def validate_submission(self):
        """Validate submission data"""
        errors = []
        
        # Check if submission has content
        if not self._is_submission_complete():
            errors.append("Submission must have content (text, file, or URL)")
        
        # Validate score if graded
        if self.score is not None:
            if self.score < 0:
                errors.append("Score cannot be negative")
            
            if self.max_possible_score and self.score > self.max_possible_score:
                errors.append("Score cannot exceed maximum possible score")
        
        # Validate percentage
        if self.percentage_score is not None:
            if not (0 <= self.percentage_score <= 100):
                errors.append("Percentage score must be between 0 and 100")
        
        return errors
    
    def save(self):
        """Save with validation"""
        errors = self.validate_submission()
        if errors:
            raise ValueError(f"Submission validation failed: {', '.join(errors)}")
        
        return super().save()
    
    def __repr__(self):
        return (f'<Submission {self.id} - Assignment:{self.assignment_id} '
                f'Student:{self.student_id} - {self.status.value if self.status else "Unknown"}>')