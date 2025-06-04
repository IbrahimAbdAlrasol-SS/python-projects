"""
NOTIFICATIONS Model - نموذج الإشعارات
نموذج كامل لإدارة الإشعارات متعددة القنوات
"""

from config.database import db
from .base import BaseModel
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import CheckConstraint, Index
import json

class NotificationTypeEnum(Enum):
    """نوع الإشعار"""
    SYSTEM = 'system'                    # إشعار نظام
    ATTENDANCE = 'attendance'            # إشعار حضور
    ASSIGNMENT = 'assignment'            # إشعار واجب
    GRADE = 'grade'                     # إشعار درجة
    SCHEDULE = 'schedule'               # إشعار جدول
    ANNOUNCEMENT = 'announcement'        # إعلان
    REMINDER = 'reminder'               # تذكير
    WARNING = 'warning'                 # تحذير
    ERROR = 'error'                     # خطأ

class NotificationPriorityEnum(Enum):
    """أولوية الإشعار"""
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'
    CRITICAL = 'critical'

class NotificationStatusEnum(Enum):
    """حالة الإشعار"""
    PENDING = 'pending'      # في الانتظار
    SENT = 'sent'           # تم الإرسال
    DELIVERED = 'delivered'  # تم التسليم
    READ = 'read'           # تم القراءة
    FAILED = 'failed'       # فشل في الإرسال
    CANCELLED = 'cancelled'  # ملغى

class NotificationChannelEnum(Enum):
    """قناة الإشعار"""
    IN_APP = 'in_app'           # داخل التطبيق
    EMAIL = 'email'             # بريد إلكتروني
    SMS = 'sms'                 # رسائل نصية
    TELEGRAM = 'telegram'       # تيليجرام
    PUSH = 'push'              # إشعارات الدفع
    WEB_PUSH = 'web_push'      # إشعارات الويب

class Notification(BaseModel):
    """Notification model for multi-channel notifications"""
    
    __tablename__ = 'notifications'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Recipients
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True, index=True)
    
    # Group Recipients (for broadcast notifications)
    target_role = db.Column(db.String(20), nullable=True)  # admin, teacher, student
    target_sections = db.Column(db.JSON, nullable=True)    # ['A', 'B', 'C']
    target_years = db.Column(db.JSON, nullable=True)       # [1, 2, 3, 4]
    is_broadcast = db.Column(db.Boolean, default=False, index=True)
    
    # Notification Content
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rich_content = db.Column(db.JSON, nullable=True)  # HTML, markdown, structured data
    
    # Classification
    notification_type = db.Column(db.Enum(NotificationTypeEnum), nullable=False, index=True)
    priority = db.Column(db.Enum(NotificationPriorityEnum), default=NotificationPriorityEnum.NORMAL, index=True)
    category = db.Column(db.String(50), nullable=True, index=True)  # Custom category
    
    # Delivery Channels
    channels = db.Column(db.JSON, nullable=False, default=list)  # ['in_app', 'email', 'telegram']
    channel_preferences = db.Column(db.JSON, nullable=True)     # Per-channel settings
    
    # Status and Timing
    status = db.Column(db.Enum(NotificationStatusEnum), default=NotificationStatusEnum.PENDING, index=True)
    scheduled_at = db.Column(db.DateTime, nullable=True, index=True)  # For scheduled notifications
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)
    
    # Interaction
    is_read = db.Column(db.Boolean, default=False, index=True)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    is_pinned = db.Column(db.Boolean, default=False)
    read_receipt_required = db.Column(db.Boolean, default=False)
    
    # Action and Links
    action_url = db.Column(db.String(500), nullable=True)
    action_text = db.Column(db.String(100), nullable=True)
    deep_link = db.Column(db.String(500), nullable=True)  # For mobile app deep links
    
    # Related Entities
    related_entity_type = db.Column(db.String(50), nullable=True)  # assignment, lecture, etc.
    related_entity_id = db.Column(db.Integer, nullable=True)
    
    # Sender Information
    sent_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    sender_name = db.Column(db.String(255), nullable=True)
    sender_type = db.Column(db.String(20), default='system')  # system, user, auto
    
    # Delivery Tracking
    delivery_attempts = db.Column(db.Integer, default=0)
    last_attempt_at = db.Column(db.DateTime, nullable=True)
    failure_reason = db.Column(db.Text, nullable=True)
    delivery_metadata = db.Column(db.JSON, nullable=True)  # Channel-specific delivery data
    
    # Template and Localization
    template_id = db.Column(db.String(100), nullable=True)
    template_variables = db.Column(db.JSON, nullable=True)
    language = db.Column(db.String(10), default='ar')  # ar, en
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications', lazy='select')
    student = db.relationship('Student', backref='notifications', lazy='select')
    teacher = db.relationship('Teacher', backref='notifications', lazy='select')
    sender = db.relationship('User', foreign_keys=[sent_by], backref='sent_notifications', lazy='select')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('delivery_attempts >= 0', name='check_delivery_attempts'),
        CheckConstraint('expires_at IS NULL OR expires_at > created_at', name='check_expiry_time'),
        Index('idx_notification_recipient', 'user_id', 'status', 'created_at'),
        Index('idx_notification_type_priority', 'notification_type', 'priority'),
        Index('idx_notification_scheduled', 'scheduled_at', 'status'),
        Index('idx_notification_broadcast', 'is_broadcast', 'target_role'),
    )
    
    def mark_as_read(self, read_by_user_id=None):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            self.status = NotificationStatusEnum.READ
            self.save()
    
    def mark_as_delivered(self, channel=None, delivery_data=None):
        """Mark notification as delivered"""
        if self.status == NotificationStatusEnum.SENT:
            self.status = NotificationStatusEnum.DELIVERED
            self.delivered_at = datetime.utcnow()
            
            if delivery_data:
                if not self.delivery_metadata:
                    self.delivery_metadata = {}
                self.delivery_metadata[channel or 'unknown'] = delivery_data
            
            self.save()
    
    def mark_as_sent(self, channel=None, sent_data=None):
        """Mark notification as sent"""
        if self.status == NotificationStatusEnum.PENDING:
            self.status = NotificationStatusEnum.SENT
            self.sent_at = datetime.utcnow()
            
            if sent_data:
                if not self.delivery_metadata:
                    self.delivery_metadata = {}
                self.delivery_metadata[channel or 'unknown'] = sent_data
            
            self.save()
    
    def mark_as_failed(self, reason, channel=None):
        """Mark notification as failed"""
        self.status = NotificationStatusEnum.FAILED
        self.failure_reason = reason
        self.last_attempt_at = datetime.utcnow()
        self.delivery_attempts += 1
        
        if channel and not self.delivery_metadata:
            self.delivery_metadata = {}
        if channel:
            self.delivery_metadata[channel] = {'error': reason, 'failed_at': datetime.utcnow().isoformat()}
        
        self.save()
    
    def retry_delivery(self, max_attempts=3):
        """Retry failed notification delivery"""
        if self.status != NotificationStatusEnum.FAILED:
            raise ValueError("Can only retry failed notifications")
        
        if self.delivery_attempts >= max_attempts:
            raise ValueError(f"Maximum retry attempts ({max_attempts}) exceeded")
        
        self.status = NotificationStatusEnum.PENDING
        self.failure_reason = None
        self.save()
    
    def cancel_notification(self, reason=None):
        """Cancel pending notification"""
        if self.status != NotificationStatusEnum.PENDING:
            raise ValueError("Can only cancel pending notifications")
        
        self.status = NotificationStatusEnum.CANCELLED
        if reason:
            self.failure_reason = f"Cancelled: {reason}"
        
        self.save()
    
    def archive_notification(self):
        """Archive the notification"""
        self.is_archived = True
        self.save()
    
    def pin_notification(self):
        """Pin the notification"""
        self.is_pinned = True
        self.save()
    
    def unpin_notification(self):
        """Unpin the notification"""
        self.is_pinned = False
        self.save()
    
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def should_send_now(self):
        """Check if notification should be sent now"""
        if self.status != NotificationStatusEnum.PENDING:
            return False
        
        if self.is_expired():
            return False
        
        if self.scheduled_at:
            return datetime.utcnow() >= self.scheduled_at
        
        return True
    
    def get_delivery_status_summary(self):
        """Get summary of delivery status across channels"""
        summary = {
            'total_channels': len(self.channels) if self.channels else 0,
            'delivered_channels': 0,
            'failed_channels': 0,
            'pending_channels': 0,
            'channel_details': {}
        }
        
        if self.delivery_metadata:
            for channel, data in self.delivery_metadata.items():
                if 'error' in data:
                    summary['failed_channels'] += 1
                    summary['channel_details'][channel] = {'status': 'failed', 'error': data['error']}
                else:
                    summary['delivered_channels'] += 1
                    summary['channel_details'][channel] = {'status': 'delivered', 'delivered_at': data.get('delivered_at')}
        
        summary['pending_channels'] = summary['total_channels'] - summary['delivered_channels'] - summary['failed_channels']
        
        return summary
    
    def render_content(self, user_context=None):
        """Render notification content with template variables"""
        title = self.title
        message = self.message
        
        if self.template_variables and user_context:
            # Replace template variables with actual values
            variables = {**self.template_variables, **user_context}
            
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                title = title.replace(placeholder, str(value))
                message = message.replace(placeholder, str(value))
        
        return {'title': title, 'message': message}
    
    def to_dict(self, include_sensitive=False, include_metadata=False):
        """Convert to dictionary"""
        data = super().to_dict()
        
        # Add enum values
        data['notification_type'] = self.notification_type.value if self.notification_type else None
        data['priority'] = self.priority.value if self.priority else None
        data['status'] = self.status.value if self.status else None
        
        # Format timestamps
        if self.scheduled_at:
            data['scheduled_at'] = self.scheduled_at.isoformat()
        
        if self.sent_at:
            data['sent_at'] = self.sent_at.isoformat()
        
        if self.delivered_at:
            data['delivered_at'] = self.delivered_at.isoformat()
        
        if self.read_at:
            data['read_at'] = self.read_at.isoformat()
        
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        
        # Add computed fields
        data['is_expired'] = self.is_expired()
        data['should_send_now'] = self.should_send_now()
        
        # Include delivery status
        if include_metadata:
            data['delivery_summary'] = self.get_delivery_status_summary()
        
        # Remove sensitive data by default
        if not include_sensitive:
            data.pop('delivery_metadata', None)
            data.pop('template_variables', None)
            data.pop('failure_reason', None)
        
        return data
    
    @classmethod
    def create_notification(cls, title, message, notification_type, recipients=None, 
                          channels=None, priority=None, **kwargs):
        """Create a new notification"""
        notification = cls(
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority or NotificationPriorityEnum.NORMAL,
            channels=channels or ['in_app'],
            **kwargs
        )
        
        # Set recipients
        if recipients:
            if isinstance(recipients, dict):
                for key, value in recipients.items():
                    setattr(notification, key, value)
            elif isinstance(recipients, (list, tuple)):
                # Assume list of user IDs
                if len(recipients) == 1:
                    notification.user_id = recipients[0]
                else:
                    # For multiple recipients, create broadcast
                    notification.is_broadcast = True
        
        notification.save()
        return notification
    
    @classmethod
    def create_system_notification(cls, title, message, user_id=None, **kwargs):
        """Create system notification"""
        return cls.create_notification(
            title=title,
            message=message,
            notification_type=NotificationTypeEnum.SYSTEM,
            recipients={'user_id': user_id} if user_id else None,
            sender_type='system',
            **kwargs
        )
    
    @classmethod
    def create_assignment_notification(cls, assignment, student_ids=None, notification_subtype='new', **kwargs):
        """Create assignment-related notification"""
        if notification_subtype == 'new':
            title = f"واجب جديد: {assignment.title}"
            message = f"تم نشر واجب جديد في مادة {assignment.subject.name}. تاريخ التسليم: {assignment.due_date.strftime('%Y-%m-%d %H:%M')}"
        elif notification_subtype == 'reminder':
            title = f"تذكير: {assignment.title}"
            message = f"تذكير بموعد تسليم الواجب. الوقت المتبقي: {assignment.get_time_remaining() // 3600} ساعة"
        elif notification_subtype == 'graded':
            title = f"تم تقييم الواجب: {assignment.title}"
            message = f"تم تقييم واجبك في مادة {assignment.subject.name}. يمكنك مراجعة النتيجة والملاحظات."
        else:
            title = f"تحديث الواجب: {assignment.title}"
            message = f"تم تحديث الواجب في مادة {assignment.subject.name}"
        
        # Create notification for target students
        notification = cls.create_notification(
            title=title,
            message=message,
            notification_type=NotificationTypeEnum.ASSIGNMENT,
            related_entity_type='assignment',
            related_entity_id=assignment.id,
            target_sections=assignment.target_sections,
            target_years=[assignment.target_year],
            is_broadcast=True,
            **kwargs
        )
        
        return notification
    
    @classmethod
    def create_attendance_notification(cls, lecture, student_id, notification_subtype='reminder'):
        """Create attendance-related notification"""
        if notification_subtype == 'reminder':
            title = f"تذكير بالحضور: {lecture.schedule.subject.name}"
            message = f"محاضرة {lecture.schedule.subject.name} ستبدأ خلال 15 دقيقة في {lecture.schedule.room.name}"
        elif notification_subtype == 'qr_active':
            title = f"QR متاح للحضور: {lecture.schedule.subject.name}"
            message = f"أصبح رمز QR متاحاً لتسجيل الحضور. سينتهي خلال {lecture.qr_sessions.first().get_time_remaining() // 60} دقيقة"
        elif notification_subtype == 'attendance_confirmed':
            title = "تم تأكيد حضورك"
            message = f"تم تسجيل حضورك بنجاح في محاضرة {lecture.schedule.subject.name}"
        else:
            title = f"إشعار حضور: {lecture.schedule.subject.name}"
            message = "تحديث على حالة الحضور"
        
        return cls.create_notification(
            title=title,
            message=message,
            notification_type=NotificationTypeEnum.ATTENDANCE,
            recipients={'user_id': student_id} if student_id else None,
            related_entity_type='lecture',
            related_entity_id=lecture.id,
            channels=['in_app', 'push']
        )
    
    @classmethod
    def get_user_notifications(cls, user_id, unread_only=False, limit=50):
        """Get notifications for a user"""
        query = cls.query.filter_by(user_id=user_id, is_archived=False)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        return query.order_by(cls.is_pinned.desc(), cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_pending_notifications(cls):
        """Get notifications pending delivery"""
        return cls.query.filter_by(status=NotificationStatusEnum.PENDING).all()
    
    @classmethod
    def get_failed_notifications(cls, max_attempts=3):
        """Get failed notifications that can be retried"""
        return cls.query.filter(
            cls.status == NotificationStatusEnum.FAILED,
            cls.delivery_attempts < max_attempts
        ).all()
    
    @classmethod
    def cleanup_expired_notifications(cls):
        """Clean up expired notifications"""
        expired_count = cls.query.filter(
            cls.expires_at <= datetime.utcnow(),
            cls.status.in_([NotificationStatusEnum.PENDING, NotificationStatusEnum.SENT])
        ).update({
            'status': NotificationStatusEnum.CANCELLED,
            'failure_reason': 'Expired'
        })
        
        db.session.commit()
        return expired_count
    
    def validate_notification(self):
        """Validate notification data"""
        errors = []
        
        # Check required fields
        if not self.title or len(self.title.strip()) < 1:
            errors.append("Title is required")
        
        if not self.message or len(self.message.strip()) < 1:
            errors.append("Message is required")
        
        # Check channels
        if not self.channels or len(self.channels) == 0:
            errors.append("At least one delivery channel must be specified")
        
        # Check recipients for non-broadcast notifications
        if not self.is_broadcast and not any([self.user_id, self.student_id, self.teacher_id]):
            errors.append("Recipient must be specified for non-broadcast notifications")
        
        # Check expiry time
        if self.expires_at and self.expires_at <= datetime.utcnow():
            errors.append("Expiry time must be in the future")
        
        return errors
    
    def save(self):
        """Save with validation"""
        errors = self.validate_notification()
        if errors:
            raise ValueError(f"Notification validation failed: {', '.join(errors)}")
        
        return super().save()
    
    def __repr__(self):
        return (f'<Notification {self.id}: {self.title[:30]}... - '
                f'{self.status.value if self.status else "Unknown"}>')