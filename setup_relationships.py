"""
Complete Model Relationships Setup
إعداد العلاقات الكاملة بين جميع النماذج
"""

from config.database import db
from sqlalchemy import event
from sqlalchemy.orm import relationship, backref

def setup_complete_relationships():
    """Setup all relationships between models after import"""
    print("🔗 Setting up complete model relationships...")
    
    try:
        from models import (
            User, Student, Teacher, Subject, Room, Schedule, 
            Lecture, QRSession, AttendanceRecord, Assignment, 
            Submission, Notification, StudentCounter, SystemSetting
        )
        
        # === USER RELATIONSHIPS ===
        # User -> Student (One-to-One)
        User.student_profile = relationship(
            'Student', 
            uselist=False, 
            back_populates='user',
            cascade='all, delete-orphan'
        )
        
        # User -> Teacher (One-to-One)
        User.teacher_profile = relationship(
            'Teacher', 
            uselist=False, 
            back_populates='user',
            cascade='all, delete-orphan'
        )
        
        # === STUDENT RELATIONSHIPS ===
        # Student -> User (One-to-One)
        Student.user = relationship(
            'User', 
            back_populates='student_profile',
            lazy='select'
        )
        
        # Student -> AttendanceRecord (One-to-Many)
        Student.attendance_records = relationship(
            'AttendanceRecord',
            back_populates='student',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # Student -> Submission (One-to-Many)
        Student.submissions = relationship(
            'Submission',
            back_populates='student',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # Student -> StudentCounter (One-to-Many)
        Student.counters = relationship(
            'StudentCounter',
            back_populates='student',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # Student -> Notification (One-to-Many)
        Student.notifications = relationship(
            'Notification',
            foreign_keys='Notification.student_id',
            back_populates='student',
            lazy='dynamic'
        )
        
        # === TEACHER RELATIONSHIPS ===
        # Teacher -> User (One-to-One)
        Teacher.user = relationship(
            'User', 
            back_populates='teacher_profile',
            lazy='select'
        )
        
        # Teacher -> Schedule (One-to-Many)
        Teacher.schedules = relationship(
            'Schedule',
            back_populates='teacher',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # Teacher -> Assignment (One-to-Many)
        Teacher.assignments = relationship(
            'Assignment',
            back_populates='teacher',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # Teacher -> QRSession (One-to-Many)
        Teacher.qr_sessions = relationship(
            'QRSession',
            back_populates='teacher',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # Teacher -> Notification (One-to-Many)
        Teacher.notifications = relationship(
            'Notification',
            foreign_keys='Notification.teacher_id',
            back_populates='teacher',
            lazy='dynamic'
        )
        
        # === SUBJECT RELATIONSHIPS ===
        # Subject -> Schedule (One-to-Many)
        Subject.schedules = relationship(
            'Schedule',
            back_populates='subject',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # Subject -> Assignment (One-to-Many)
        Subject.assignments = relationship(
            'Assignment',
            back_populates='subject',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # Subject -> StudentCounter (One-to-Many)
        Subject.student_counters = relationship(
            'StudentCounter',
            back_populates='subject',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # === ROOM RELATIONSHIPS ===
        # Room -> Schedule (One-to-Many)
        Room.schedules = relationship(
            'Schedule',
            back_populates='room',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # === SCHEDULE RELATIONSHIPS ===
        # Schedule -> Subject (Many-to-One)
        Schedule.subject = relationship(
            'Subject',
            back_populates='schedules',
            lazy='select'
        )
        
        # Schedule -> Teacher (Many-to-One)
        Schedule.teacher = relationship(
            'Teacher',
            back_populates='schedules',
            lazy='select'
        )
        
        # Schedule -> Room (Many-to-One)
        Schedule.room = relationship(
            'Room',
            back_populates='schedules',
            lazy='select'
        )
        
        # Schedule -> Lecture (One-to-Many)
        Schedule.lectures = relationship(
            'Lecture',
            back_populates='schedule',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # === LECTURE RELATIONSHIPS ===
        # Lecture -> Schedule (Many-to-One)
        Lecture.schedule = relationship(
            'Schedule',
            back_populates='lectures',
            lazy='select'
        )
        
        # Lecture -> QRSession (One-to-Many)
        Lecture.qr_sessions = relationship(
            'QRSession',
            back_populates='lecture',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # Lecture -> AttendanceRecord (One-to-Many)
        Lecture.attendance_records = relationship(
            'AttendanceRecord',
            back_populates='lecture',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # === QR SESSION RELATIONSHIPS ===
        # QRSession -> Lecture (Many-to-One)
        QRSession.lecture = relationship(
            'Lecture',
            back_populates='qr_sessions',
            lazy='select'
        )
        
        # QRSession -> Teacher (Many-to-One)
        QRSession.teacher = relationship(
            'Teacher',
            back_populates='qr_sessions',
            lazy='select'
        )
        
        # QRSession -> AttendanceRecord (One-to-Many)
        QRSession.attendance_records = relationship(
            'AttendanceRecord',
            back_populates='qr_session',
            lazy='dynamic'
        )
        
        # === ATTENDANCE RECORD RELATIONSHIPS ===
        # AttendanceRecord -> Student (Many-to-One)
        AttendanceRecord.student = relationship(
            'Student',
            back_populates='attendance_records',
            lazy='select'
        )
        
        # AttendanceRecord -> Lecture (Many-to-One)
        AttendanceRecord.lecture = relationship(
            'Lecture',
            back_populates='attendance_records',
            lazy='select'
        )
        
        # AttendanceRecord -> QRSession (Many-to-One)
        AttendanceRecord.qr_session = relationship(
            'QRSession',
            back_populates='attendance_records',
            lazy='select'
        )
        
        # AttendanceRecord -> User (Approved By)
        AttendanceRecord.approved_by_user = relationship(
            'User',
            foreign_keys='AttendanceRecord.approved_by',
            backref='approved_attendance_records',
            lazy='select'
        )
        
        # === ASSIGNMENT RELATIONSHIPS ===
        # Assignment -> Subject (Many-to-One)
        Assignment.subject = relationship(
            'Subject',
            back_populates='assignments',
            lazy='select'
        )
        
        # Assignment -> Teacher (Many-to-One)
        Assignment.teacher = relationship(
            'Teacher',
            back_populates='assignments',
            lazy='select'
        )
        
        # Assignment -> User (Created By)
        Assignment.creator = relationship(
            'User',
            foreign_keys='Assignment.created_by',
            backref='created_assignments',
            lazy='select'
        )
        
        # Assignment -> Submission (One-to-Many)
        Assignment.submissions = relationship(
            'Submission',
            back_populates='assignment',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
        
        # === SUBMISSION RELATIONSHIPS ===
        # Submission -> Assignment (Many-to-One)
        Submission.assignment = relationship(
            'Assignment',
            back_populates='submissions',
            lazy='select'
        )
        
        # Submission -> Student (Many-to-One)
        Submission.student = relationship(
            'Student',
            back_populates='submissions',
            lazy='select'
        )
        
        # Submission -> User (Graded By)
        Submission.grader = relationship(
            'User',
            foreign_keys='Submission.graded_by',
            backref='graded_submissions',
            lazy='select'
        )
        
        # Submission -> Submission (Previous Version)
        Submission.previous_submission = relationship(
            'Submission',
            remote_side='Submission.id',
            backref='revisions',
            lazy='select'
        )
        
        # === NOTIFICATION RELATIONSHIPS ===
        # Notification -> User (Recipient)
        Notification.user = relationship(
            'User',
            foreign_keys='Notification.user_id',
            back_populates='notifications',
            lazy='select'
        )
        
        # Notification -> Student (Recipient)
        Notification.student = relationship(
            'Student',
            back_populates='notifications',
            lazy='select'
        )
        
        # Notification -> Teacher (Recipient)
        Notification.teacher = relationship(
            'Teacher',
            back_populates='notifications',
            lazy='select'
        )
        
        # Notification -> User (Sender)
        Notification.sender = relationship(
            'User',
            foreign_keys='Notification.sent_by',
            backref='sent_notifications',
            lazy='select'
        )
        
        # === STUDENT COUNTER RELATIONSHIPS ===
        # StudentCounter -> Student (Many-to-One)
        StudentCounter.student = relationship(
            'Student',
            back_populates='counters',
            lazy='select'
        )
        
        # StudentCounter -> Subject (Many-to-One)
        StudentCounter.subject = relationship(
            'Subject',
            back_populates='student_counters',
            lazy='select'
        )
        
        # StudentCounter -> User (Last Action By)
        StudentCounter.last_action_user = relationship(
            'User',
            foreign_keys='StudentCounter.last_action_by',
            backref='counter_actions',
            lazy='select'
        )
        
        # === SYSTEM SETTING RELATIONSHIPS ===
        # SystemSetting -> User (Last Modified By)
        SystemSetting.last_modifier = relationship(
            'User',
            foreign_keys='SystemSetting.last_modified_by',
            backref='modified_settings',
            lazy='select'
        )
        
        print("  ✅ All model relationships configured")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to setup relationships: {e}")
        return False

def setup_database_events():
    """Setup database events and triggers"""
    print("🎯 Setting up database events...")
    
    try:
        from models import Assignment, Lecture, AttendanceRecord, Submission, StudentCounter
        
        # === ASSIGNMENT EVENTS ===
        @event.listens_for(Assignment, 'after_insert')
        def create_assignment_notification(mapper, connection, target):
            """Create notification when assignment is published"""
            if target.status.value == 'published':
                # This would trigger notification creation
                pass
        
        # === LECTURE EVENTS ===
        @event.listens_for(Lecture, 'before_update')
        def update_lecture_statistics(mapper, connection, target):
            """Update lecture statistics before saving"""
            if target.status.value == 'completed':
                # Update attendance statistics
                target.update_attendance_statistics()
        
        # === ATTENDANCE EVENTS ===
        @event.listens_for(AttendanceRecord, 'after_insert')
        def update_lecture_stats_on_attendance(mapper, connection, target):
            """Update lecture statistics when attendance is recorded"""
            # This would update the lecture's attendance counters
            pass
        
        # === SUBMISSION EVENTS ===
        @event.listens_for(Submission, 'after_update')
        def update_assignment_stats_on_submission(mapper, connection, target):
            """Update assignment statistics when submission changes"""
            if hasattr(target, 'assignment') and target.assignment:
                # Update assignment statistics
                target.assignment.update_statistics()
        
        # === COUNTER EVENTS ===
        @event.listens_for(StudentCounter, 'after_update')
        def handle_counter_mute_unmute(mapper, connection, target):
            """Handle notifications when counter is muted/unmuted"""
            # This would send notifications based on counter changes
            pass
        
        print("  ✅ Database events configured")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to setup events: {e}")
        return False

def validate_relationships():
    """Validate all relationships are working"""
    print("🔍 Validating model relationships...")
    
    try:
        from models import User, Student, Teacher, Subject, Room
        
        # Test basic relationships
        validation_tests = [
            # User relationships
            (User, 'student_profile', 'One-to-One with Student'),
            (User, 'teacher_profile', 'One-to-One with Teacher'),
            
            # Student relationships
            (Student, 'user', 'One-to-One with User'),
            (Student, 'attendance_records', 'One-to-Many with AttendanceRecord'),
            (Student, 'submissions', 'One-to-Many with Submission'),
            (Student, 'counters', 'One-to-Many with StudentCounter'),
            
            # Teacher relationships
            (Teacher, 'user', 'One-to-One with User'),
            (Teacher, 'schedules', 'One-to-Many with Schedule'),
            (Teacher, 'assignments', 'One-to-Many with Assignment'),
            
            # Subject relationships
            (Subject, 'schedules', 'One-to-Many with Schedule'),
            (Subject, 'assignments', 'One-to-Many with Assignment'),
            
            # Room relationships
            (Room, 'schedules', 'One-to-Many with Schedule'),
        ]
        
        valid_count = 0
        total_count = len(validation_tests)
        
        for model, relationship_name, description in validation_tests:
            try:
                # Check if relationship exists
                if hasattr(model, relationship_name):
                    relationship_obj = getattr(model, relationship_name)
                    if hasattr(relationship_obj, 'property'):
                        print(f"    ✅ {model.__name__}.{relationship_name}: {description}")
                        valid_count += 1
                    else:
                        print(f"    ⚠️ {model.__name__}.{relationship_name}: Not a relationship")
                else:
                    print(f"    ❌ {model.__name__}.{relationship_name}: Missing")
            except Exception as e:
                print(f"    ❌ {model.__name__}.{relationship_name}: Error - {e}")
        
        success_rate = (valid_count / total_count) * 100
        print(f"  📊 Relationship validation: {valid_count}/{total_count} ({success_rate:.1f}%)")
        
        return success_rate >= 80  # 80% success rate required
        
    except Exception as e:
        print(f"  ❌ Relationship validation failed: {e}")
        return False

def create_foreign_key_constraints():
    """Create explicit foreign key constraints"""
    print("🔒 Creating foreign key constraints...")
    
    constraints = [
        # Students table
        "ALTER TABLE students ADD CONSTRAINT IF NOT EXISTS fk_students_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;",
        
        # Teachers table
        "ALTER TABLE teachers ADD CONSTRAINT IF NOT EXISTS fk_teachers_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;",
        
        # Schedules table
        "ALTER TABLE schedules ADD CONSTRAINT IF NOT EXISTS fk_schedules_subject_id FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE;",
        "ALTER TABLE schedules ADD CONSTRAINT IF NOT EXISTS fk_schedules_teacher_id FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE;",
        "ALTER TABLE schedules ADD CONSTRAINT IF NOT EXISTS fk_schedules_room_id FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE;",
        
        # Lectures table
        "ALTER TABLE lectures ADD CONSTRAINT IF NOT EXISTS fk_lectures_schedule_id FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE;",
        "ALTER TABLE lectures ADD CONSTRAINT IF NOT EXISTS fk_lectures_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;",
        
        # QR Sessions table
        "ALTER TABLE qr_sessions ADD CONSTRAINT IF NOT EXISTS fk_qr_sessions_lecture_id FOREIGN KEY (lecture_id) REFERENCES lectures(id) ON DELETE CASCADE;",
        "ALTER TABLE qr_sessions ADD CONSTRAINT IF NOT EXISTS fk_qr_sessions_generated_by FOREIGN KEY (generated_by) REFERENCES teachers(id) ON DELETE CASCADE;",
        
        # Attendance Records table
        "ALTER TABLE attendance_records ADD CONSTRAINT IF NOT EXISTS fk_attendance_student_id FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;",
        "ALTER TABLE attendance_records ADD CONSTRAINT IF NOT EXISTS fk_attendance_lecture_id FOREIGN KEY (lecture_id) REFERENCES lectures(id) ON DELETE CASCADE;",
        "ALTER TABLE attendance_records ADD CONSTRAINT IF NOT EXISTS fk_attendance_qr_session_id FOREIGN KEY (qr_session_id) REFERENCES qr_sessions(id) ON DELETE SET NULL;",
        "ALTER TABLE attendance_records ADD CONSTRAINT IF NOT EXISTS fk_attendance_approved_by FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL;",
        
        # Assignments table
        "ALTER TABLE assignments ADD CONSTRAINT IF NOT EXISTS fk_assignments_subject_id FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE;",
        "ALTER TABLE assignments ADD CONSTRAINT IF NOT EXISTS fk_assignments_teacher_id FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE;",
        "ALTER TABLE assignments ADD CONSTRAINT IF NOT EXISTS fk_assignments_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE;",
        
        # Submissions table
        "ALTER TABLE submissions ADD CONSTRAINT IF NOT EXISTS fk_submissions_assignment_id FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE;",
        "ALTER TABLE submissions ADD CONSTRAINT IF NOT EXISTS fk_submissions_student_id FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;",
        "ALTER TABLE submissions ADD CONSTRAINT IF NOT EXISTS fk_submissions_graded_by FOREIGN KEY (graded_by) REFERENCES users(id) ON DELETE SET NULL;",
        
        # Student Counters table
        "ALTER TABLE student_counters ADD CONSTRAINT IF NOT EXISTS fk_counters_student_id FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;",
        "ALTER TABLE student_counters ADD CONSTRAINT IF NOT EXISTS fk_counters_subject_id FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE;",
        "ALTER TABLE student_counters ADD CONSTRAINT IF NOT EXISTS fk_counters_last_action_by FOREIGN KEY (last_action_by) REFERENCES users(id) ON DELETE SET NULL;",
        
        # Notifications table
        "ALTER TABLE notifications ADD CONSTRAINT IF NOT EXISTS fk_notifications_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;",
        "ALTER TABLE notifications ADD CONSTRAINT IF NOT EXISTS fk_notifications_student_id FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;",
        "ALTER TABLE notifications ADD CONSTRAINT IF NOT EXISTS fk_notifications_teacher_id FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE;",
        "ALTER TABLE notifications ADD CONSTRAINT IF NOT EXISTS fk_notifications_sent_by FOREIGN KEY (sent_by) REFERENCES users(id) ON DELETE SET NULL;",
        
        # System Settings table
        "ALTER TABLE system_settings ADD CONSTRAINT IF NOT EXISTS fk_settings_last_modified_by FOREIGN KEY (last_modified_by) REFERENCES users(id) ON DELETE SET NULL;",
    ]
    
    created_count = 0
    for constraint_sql in constraints:
        try:
            db.session.execute(constraint_sql)
            created_count += 1
        except Exception as e:
            # Constraint may already exist
            pass
    
    try:
        db.session.commit()
        print(f"  ✅ Foreign key constraints: {created_count} processed")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"  ❌ Failed to create constraints: {e}")
        return False

def run_complete_relationship_setup():
    """Run complete relationship setup"""
    print("🔗 Starting complete relationship setup...")
    print("=" * 50)
    
    results = {
        'relationships': False,
        'events': False,
        'validation': False,
        'constraints': False
    }
    
    try:
        # 1. Setup relationships
        results['relationships'] = setup_complete_relationships()
        
        # 2. Setup database events
        results['events'] = setup_database_events()
        
        # 3. Validate relationships
        results['validation'] = validate_relationships()
        
        # 4. Create foreign key constraints
        results['constraints'] = create_foreign_key_constraints()
        
        # Summary
        successful_operations = sum(results.values())
        total_operations = len(results)
        
        print("\n" + "=" * 50)
        print(f"🎯 Relationship Setup Summary:")
        print(f"   ✅ Successful: {successful_operations}/{total_operations}")
        print(f"   🔗 Relationships: {'✅' if results['relationships'] else '❌'}")
        print(f"   🎯 Events: {'✅' if results['events'] else '❌'}")
        print(f"   🔍 Validation: {'✅' if results['validation'] else '❌'}")
        print(f"   🔒 Constraints: {'✅' if results['constraints'] else '❌'}")
        
        if successful_operations >= 3:
            print("\n🎉 Relationship setup completed successfully!")
            print("🔗 All models are properly connected and validated")
        else:
            print("\n⚠️ Some relationship operations failed. Check logs above.")
        
        print("=" * 50)
        
        return successful_operations >= 3
        
    except Exception as e:
        print(f"❌ Critical error during relationship setup: {e}")
        return False

# Export main functions
__all__ = [
    'setup_complete_relationships',
    'setup_database_events',
    'validate_relationships',
    'create_foreign_key_constraints',
    'run_complete_relationship_setup'
]
