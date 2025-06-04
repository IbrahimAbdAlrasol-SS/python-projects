"""
Database Indexes and Optimizations - COMPLETE VERSION
تحسينات قاعدة البيانات والفهارس الكاملة لجميع النماذج
"""

from config.database import db
from sqlalchemy import text, Index

def create_performance_indexes():
    """Create comprehensive performance indexes for all models"""
    
    print("🔍 Creating comprehensive performance indexes...")
    
    # Core Models Indexes
    core_indexes = [
        # Users indexes - Enhanced
        "CREATE INDEX IF NOT EXISTS idx_users_username_active ON users(username) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_users_role_active ON users(role, is_active);",
        "CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login DESC);",
        "CREATE INDEX IF NOT EXISTS idx_users_failed_attempts ON users(failed_login_attempts) WHERE failed_login_attempts > 0;",
        
        # Students indexes - Enhanced
        "CREATE INDEX IF NOT EXISTS idx_students_university_id ON students(university_id);",
        "CREATE INDEX IF NOT EXISTS idx_students_section_year ON students(section, study_year);",
        "CREATE INDEX IF NOT EXISTS idx_students_study_type_status ON students(study_type, academic_status);",
        "CREATE INDEX IF NOT EXISTS idx_students_face_registered ON students(face_registered, face_registered_at);",
        "CREATE INDEX IF NOT EXISTS idx_students_telegram ON students(telegram_id) WHERE telegram_id IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_students_active ON students(academic_status) WHERE academic_status = 'active';",
        
        # Teachers indexes - Enhanced
        "CREATE INDEX IF NOT EXISTS idx_teachers_employee_id ON teachers(employee_id);",
        "CREATE INDEX IF NOT EXISTS idx_teachers_department ON teachers(department);",
        "CREATE INDEX IF NOT EXISTS idx_teachers_specialization ON teachers(specialization);",
        "CREATE INDEX IF NOT EXISTS idx_teachers_degree ON teachers(academic_degree);",
        
        # Subjects indexes - Enhanced
        "CREATE INDEX IF NOT EXISTS idx_subjects_code ON subjects(code);",
        "CREATE INDEX IF NOT EXISTS idx_subjects_department ON subjects(department);",
        "CREATE INDEX IF NOT EXISTS idx_subjects_year_semester ON subjects(study_year, semester);",
        "CREATE INDEX IF NOT EXISTS idx_subjects_active ON subjects(is_active) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_subjects_credit_hours ON subjects(credit_hours);",
        
        # Rooms indexes - Enhanced
        "CREATE INDEX IF NOT EXISTS idx_rooms_name ON rooms(name);",
        "CREATE INDEX IF NOT EXISTS idx_rooms_building_floor ON rooms(building, floor);",
        "CREATE INDEX IF NOT EXISTS idx_rooms_type_capacity ON rooms(room_type, capacity);",
        "CREATE INDEX IF NOT EXISTS idx_rooms_active ON rooms(is_active) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_rooms_location ON rooms(center_latitude, center_longitude);",
    ]
    
    # Academic Models Indexes
    academic_indexes = [
        # Schedules indexes - Comprehensive
        "CREATE INDEX IF NOT EXISTS idx_schedules_subject_teacher ON schedules(subject_id, teacher_id);",
        "CREATE INDEX IF NOT EXISTS idx_schedules_room_time ON schedules(room_id, day_of_week, start_time);",
        "CREATE INDEX IF NOT EXISTS idx_schedules_section_period ON schedules(section, academic_year, semester);",
        "CREATE INDEX IF NOT EXISTS idx_schedules_teacher_day ON schedules(teacher_id, day_of_week, academic_year, semester);",
        "CREATE INDEX IF NOT EXISTS idx_schedules_active_period ON schedules(is_active, academic_year, semester) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_schedules_time_range ON schedules(day_of_week, start_time, end_time);",
        
        # Lectures indexes - Comprehensive
        "CREATE INDEX IF NOT EXISTS idx_lectures_schedule_date ON lectures(schedule_id, lecture_date);",
        "CREATE INDEX IF NOT EXISTS idx_lectures_date_status ON lectures(lecture_date, status);",
        "CREATE INDEX IF NOT EXISTS idx_lectures_status_active ON lectures(status) WHERE status = 'active';",
        "CREATE INDEX IF NOT EXISTS idx_lectures_date_range ON lectures(lecture_date DESC);",
        "CREATE INDEX IF NOT EXISTS idx_lectures_qr_enabled ON lectures(qr_enabled, qr_generation_allowed) WHERE qr_enabled = true;",
        "CREATE INDEX IF NOT EXISTS idx_lectures_teacher_date ON lectures(schedule_id, lecture_date) INCLUDE (status, topic);",
        "CREATE INDEX IF NOT EXISTS idx_lectures_attendance_stats ON lectures(total_expected_students, total_attended_students);",
        
        # QR Sessions indexes - Comprehensive
        "CREATE INDEX IF NOT EXISTS idx_qr_sessions_session_id ON qr_sessions(session_id);",
        "CREATE INDEX IF NOT EXISTS idx_qr_sessions_lecture_active ON qr_sessions(lecture_id, is_active, status);",
        "CREATE INDEX IF NOT EXISTS idx_qr_sessions_teacher_generated ON qr_sessions(generated_by, generated_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_qr_sessions_expiry ON qr_sessions(expires_at) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_qr_sessions_active_valid ON qr_sessions(is_active, status, expires_at) WHERE is_active = true AND status = 'active';",
        "CREATE INDEX IF NOT EXISTS idx_qr_sessions_usage ON qr_sessions(current_usage_count, max_usage_count);",
        
        # Attendance Records indexes - Comprehensive
        "CREATE INDEX IF NOT EXISTS idx_attendance_student_lecture ON attendance_records(student_id, lecture_id);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_lecture_status ON attendance_records(lecture_id, status, verification_completed);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance_records(student_id, check_in_time DESC);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_verification_steps ON attendance_records(location_verified, qr_verified, face_verified);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_completed ON attendance_records(verification_completed, check_in_time) WHERE verification_completed = true;",
        "CREATE INDEX IF NOT EXISTS idx_attendance_pending ON attendance_records(status, verification_started_at) WHERE status = 'pending';",
        "CREATE INDEX IF NOT EXISTS idx_attendance_exceptional ON attendance_records(is_exceptional, approved_by) WHERE is_exceptional = true;",
        "CREATE INDEX IF NOT EXISTS idx_attendance_sync ON attendance_records(is_synced, last_sync_attempt) WHERE is_synced = false;",
        "CREATE INDEX IF NOT EXISTS idx_attendance_type_date ON attendance_records(attendance_type, check_in_time);",
    ]
    
    # Assignment Models Indexes
    assignment_indexes = [
        # Assignments indexes - Comprehensive
        "CREATE INDEX IF NOT EXISTS idx_assignments_subject_teacher ON assignments(subject_id, teacher_id);",
        "CREATE INDEX IF NOT EXISTS idx_assignments_due_date ON assignments(due_date) WHERE status = 'active';",
        "CREATE INDEX IF NOT EXISTS idx_assignments_status_visible ON assignments(status, is_visible_to_students);",
        "CREATE INDEX IF NOT EXISTS idx_assignments_target_students ON assignments(target_year, academic_year, semester);",
        "CREATE INDEX IF NOT EXISTS idx_assignments_teacher_status ON assignments(teacher_id, status, due_date DESC);",
        "CREATE INDEX IF NOT EXISTS idx_assignments_active_period ON assignments(status, academic_year, semester) WHERE status = 'active';",
        "CREATE INDEX IF NOT EXISTS idx_assignments_statistics ON assignments(total_submissions, on_time_submissions);",
        "CREATE INDEX IF NOT EXISTS idx_assignments_telegram ON assignments(telegram_message_id) WHERE telegram_message_id IS NOT NULL;",
        
        # Submissions indexes - Comprehensive
        "CREATE INDEX IF NOT EXISTS idx_submissions_assignment_student ON submissions(assignment_id, student_id);",
        "CREATE INDEX IF NOT EXISTS idx_submissions_student_status ON submissions(student_id, status, submitted_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_submissions_assignment_status ON submissions(assignment_id, status, submitted_at);",
        "CREATE INDEX IF NOT EXISTS idx_submissions_grading ON submissions(graded_by, graded_at) WHERE graded_by IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_submissions_late ON submissions(is_late, submitted_at) WHERE is_late = true;",
        "CREATE INDEX IF NOT EXISTS idx_submissions_pending_grade ON submissions(status, submitted_at) WHERE status IN ('submitted', 'late');",
        "CREATE INDEX IF NOT EXISTS idx_submissions_score ON submissions(score, percentage_score) WHERE score IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_submissions_version ON submissions(assignment_id, student_id, version_number);",
        "CREATE INDEX IF NOT EXISTS idx_submissions_counter ON submissions(counter_updated, counter_action) WHERE counter_updated = true;",
    ]
    
    # System Models Indexes
    system_indexes = [
        # Notifications indexes - Comprehensive
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_status ON notifications(user_id, status, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_notifications_student_unread ON notifications(student_id, is_read, created_at DESC) WHERE is_read = false;",
        "CREATE INDEX IF NOT EXISTS idx_notifications_broadcast ON notifications(is_broadcast, target_role, status);",
        "CREATE INDEX IF NOT EXISTS idx_notifications_type_priority ON notifications(notification_type, priority, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_notifications_scheduled ON notifications(scheduled_at, status) WHERE scheduled_at IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_notifications_delivery ON notifications(status, delivery_attempts) WHERE status = 'failed';",
        "CREATE INDEX IF NOT EXISTS idx_notifications_expiry ON notifications(expires_at) WHERE expires_at IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_notifications_related_entity ON notifications(related_entity_type, related_entity_id);",
        
        # Student Counters indexes - Comprehensive
        "CREATE INDEX IF NOT EXISTS idx_counters_student_subject ON student_counters(student_id, subject_id);",
        "CREATE INDEX IF NOT EXISTS idx_counters_period ON student_counters(academic_year, semester, status);",
        "CREATE INDEX IF NOT EXISTS idx_counters_muted ON student_counters(is_muted, muted_at) WHERE is_muted = true;",
        "CREATE INDEX IF NOT EXISTS idx_counters_high_risk ON student_counters(counter_value DESC) WHERE counter_value > 0;",
        "CREATE INDEX IF NOT EXISTS idx_counters_telegram ON student_counters(telegram_user_id, telegram_notifications_enabled) WHERE telegram_user_id IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_counters_performance ON student_counters(consecutive_on_time DESC, counter_value ASC);",
        "CREATE INDEX IF NOT EXISTS idx_counters_subject_leaderboard ON student_counters(subject_id, academic_year, semester, counter_value ASC);",
        
        # System Settings indexes - Comprehensive
        "CREATE INDEX IF NOT EXISTS idx_settings_key ON system_settings(key) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_settings_category ON system_settings(category, ui_order);",
        "CREATE INDEX IF NOT EXISTS idx_settings_public ON system_settings(is_public, category) WHERE is_public = true;",
        "CREATE INDEX IF NOT EXISTS idx_settings_modified ON system_settings(last_modified_at DESC, last_modified_by);",
        "CREATE INDEX IF NOT EXISTS idx_settings_readonly ON system_settings(is_readonly, category) WHERE is_readonly = false;",
    ]
    
    # Composite Indexes for Complex Queries
    composite_indexes = [
        # Student performance tracking
        "CREATE INDEX IF NOT EXISTS idx_student_performance ON attendance_records(student_id, lecture_id, verification_completed, attendance_type);",
        
        # Teacher workload analysis
        "CREATE INDEX IF NOT EXISTS idx_teacher_workload ON schedules(teacher_id, academic_year, semester, day_of_week) WHERE is_active = true;",
        
        # Room utilization
        "CREATE INDEX IF NOT EXISTS idx_room_utilization ON schedules(room_id, academic_year, semester, day_of_week, start_time) WHERE is_active = true;",
        
        # Assignment workflow
        "CREATE INDEX IF NOT EXISTS idx_assignment_workflow ON submissions(assignment_id, status, submitted_at, is_late);",
        
        # Counter analytics
        "CREATE INDEX IF NOT EXISTS idx_counter_analytics ON student_counters(subject_id, academic_year, semester, counter_value, status);",
        
        # Notification delivery tracking
        "CREATE INDEX IF NOT EXISTS idx_notification_delivery ON notifications(status, scheduled_at, delivery_attempts, created_at);",
        
        # Lecture analytics
        "CREATE INDEX IF NOT EXISTS idx_lecture_analytics ON lectures(lecture_date, status, total_expected_students, total_attended_students);",
        
        # Security and audit
        "CREATE INDEX IF NOT EXISTS idx_audit_trail ON attendance_records(student_id, check_in_time, ip_address, device_info);",
    ]
    
    # Full-text search indexes (PostgreSQL specific)
    fulltext_indexes = [
        # Subject search
        "CREATE INDEX IF NOT EXISTS idx_subjects_search ON subjects USING gin(to_tsvector('arabic', name || ' ' || COALESCE(department, '')));",
        
        # Assignment search
        "CREATE INDEX IF NOT EXISTS idx_assignments_search ON assignments USING gin(to_tsvector('arabic', title || ' ' || description));",
        
        # Notification search
        "CREATE INDEX IF NOT EXISTS idx_notifications_search ON notifications USING gin(to_tsvector('arabic', title || ' ' || message));",
        
        # User search
        "CREATE INDEX IF NOT EXISTS idx_users_search ON users USING gin(to_tsvector('arabic', full_name || ' ' || COALESCE(email, '')));",
    ]
    
    # Execute all indexes
    all_indexes = core_indexes + academic_indexes + assignment_indexes + system_indexes + composite_indexes
    
    created_count = 0
    failed_count = 0
    
    for index_sql in all_indexes:
        try:
            db.session.execute(text(index_sql))
            index_name = index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unknown'
            print(f"  ✅ Created index: {index_name}")
            created_count += 1
        except Exception as e:
            print(f"  ❌ Failed to create index: {e}")
            failed_count += 1
    
    # Execute full-text indexes (PostgreSQL only)
    try:
        db.session.execute(text("SELECT version();"))
        result = db.session.fetchone()
        if result and 'postgresql' in str(result).lower():
            for index_sql in fulltext_indexes:
                try:
                    db.session.execute(text(index_sql))
                    index_name = index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'fulltext'
                    print(f"  ✅ Created full-text index: {index_name}")
                    created_count += 1
                except Exception as e:
                    print(f"  ⚠️ Full-text index failed (PostgreSQL required): {e}")
                    failed_count += 1
    except:
        print("  ℹ️ Skipping full-text indexes (PostgreSQL not detected)")
    
    try:
        db.session.commit()
        print(f"\n✅ Index creation completed: {created_count} created, {failed_count} failed")
        return created_count > 0
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to commit indexes: {e}")
        return False

def create_database_constraints():
    """Create additional database constraints for data integrity"""
    print("🔒 Creating database constraints...")
    
    constraints = [
        # User constraints
        "ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS check_username_length CHECK (length(username) >= 3);",
        "ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS check_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$');",
        
        # Student constraints
        "ALTER TABLE students ADD CONSTRAINT IF NOT EXISTS check_university_id_format CHECK (university_id ~* '^[A-Z]{2}[0-9]{7}$');",
        
        # Schedule constraints  
        "ALTER TABLE schedules ADD CONSTRAINT IF NOT EXISTS check_schedule_duration CHECK (end_time > start_time);",
        "ALTER TABLE schedules ADD CONSTRAINT IF NOT EXISTS check_academic_year_format CHECK (academic_year ~* '^[0-9]{4}-[0-9]{4}$');",
        
        # Assignment constraints
        "ALTER TABLE assignments ADD CONSTRAINT IF NOT EXISTS check_assignment_scores CHECK (max_score > 0 AND weight_percentage >= 0 AND weight_percentage <= 100);",
        "ALTER TABLE assignments ADD CONSTRAINT IF NOT EXISTS check_assignment_dates CHECK (due_date > created_at);",
        
        # Submission constraints
        "ALTER TABLE submissions ADD CONSTRAINT IF NOT EXISTS check_submission_score CHECK (score >= 0);",
        "ALTER TABLE submissions ADD CONSTRAINT IF NOT EXISTS check_percentage_range CHECK (percentage_score >= 0 AND percentage_score <= 100);",
        
        # Counter constraints
        "ALTER TABLE student_counters ADD CONSTRAINT IF NOT EXISTS check_counter_thresholds CHECK (auto_mute_threshold >= 0 AND warning_threshold >= 0);",
    ]
    
    created_count = 0
    for constraint_sql in constraints:
        try:
            db.session.execute(text(constraint_sql))
            constraint_name = constraint_sql.split('ADD CONSTRAINT IF NOT EXISTS ')[1].split(' ')[0] if 'ADD CONSTRAINT' in constraint_sql else 'unknown'
            print(f"  ✅ Created constraint: {constraint_name}")
            created_count += 1
        except Exception as e:
            print(f"  ⚠️ Constraint may already exist or failed: {e}")
    
    try:
        db.session.commit()
        print(f"✅ Database constraints completed: {created_count} processed")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to commit constraints: {e}")
        return False

def analyze_database_performance():
    """Analyze database performance and suggest optimizations"""
    print("📊 Analyzing database performance...")
    
    analysis_queries = [
        # Table sizes
        """
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation
        FROM pg_stats 
        WHERE schemaname = 'public'
        ORDER BY tablename, attname;
        """,
        
        # Index usage
        """
        SELECT 
            indexrelname as index_name,
            idx_tup_read,
            idx_tup_fetch,
            idx_scan
        FROM pg_stat_user_indexes 
        ORDER BY idx_scan DESC;
        """,
        
        # Slow queries (if enabled)
        """
        SELECT 
            query,
            calls,
            total_time,
            mean_time
        FROM pg_stat_statements 
        ORDER BY mean_time DESC 
        LIMIT 10;
        """
    ]
    
    for i, query in enumerate(analysis_queries, 1):
        try:
            result = db.session.execute(text(query))
            rows = result.fetchall()
            print(f"  📈 Analysis {i}: Found {len(rows)} results")
        except Exception as e:
            print(f"  ⚠️ Analysis {i} failed (may require PostgreSQL extensions): {e}")
    
    print("✅ Performance analysis completed")

def create_optimized_views():
    """Create optimized views for common queries"""
    print("👁️ Creating optimized database views...")
    
    views = [
        # Student performance view
        """
        CREATE OR REPLACE VIEW student_performance_view AS
        SELECT 
            s.id as student_id,
            s.university_id,
            u.full_name,
            s.section,
            s.study_year,
            COUNT(ar.id) as total_attendances,
            COUNT(CASE WHEN ar.verification_completed = true THEN 1 END) as verified_attendances,
            COUNT(CASE WHEN ar.is_late = true THEN 1 END) as late_attendances,
            ROUND(
                COUNT(CASE WHEN ar.verification_completed = true THEN 1 END)::numeric / 
                NULLIF(COUNT(ar.id), 0) * 100, 2
            ) as attendance_rate
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        LEFT JOIN attendance_records ar ON s.id = ar.student_id
        WHERE s.academic_status = 'active'
        GROUP BY s.id, s.university_id, u.full_name, s.section, s.study_year;
        """,
        
        # Teacher workload view
        """
        CREATE OR REPLACE VIEW teacher_workload_view AS
        SELECT 
            t.id as teacher_id,
            t.employee_id,
            u.full_name,
            t.department,
            COUNT(DISTINCT sch.id) as total_schedules,
            COUNT(DISTINCT sch.subject_id) as unique_subjects,
            COUNT(DISTINCT l.id) as total_lectures,
            COUNT(DISTINCT CASE WHEN l.status = 'completed' THEN l.id END) as completed_lectures
        FROM teachers t
        LEFT JOIN users u ON t.user_id = u.id
        LEFT JOIN schedules sch ON t.id = sch.teacher_id AND sch.is_active = true
        LEFT JOIN lectures l ON sch.id = l.schedule_id
        GROUP BY t.id, t.employee_id, u.full_name, t.department;
        """,
        
        # Assignment statistics view
        """
        CREATE OR REPLACE VIEW assignment_statistics_view AS
        SELECT 
            a.id as assignment_id,
            a.title,
            a.due_date,
            a.status,
            sub.name as subject_name,
            a.total_submissions,
            a.on_time_submissions,
            a.late_submissions,
            ROUND(
                a.on_time_submissions::numeric / NULLIF(a.total_submissions, 0) * 100, 2
            ) as on_time_rate,
            (
                SELECT COUNT(*) 
                FROM students s 
                WHERE s.section = ANY(a.target_sections) 
                AND s.study_year = a.target_year
                AND s.academic_status = 'active'
            ) as expected_submissions
        FROM assignments a
        LEFT JOIN subjects sub ON a.subject_id = sub.id
        WHERE a.is_visible_to_students = true;
        """
    ]
    
    created_count = 0
    for view_sql in views:
        try:
            db.session.execute(text(view_sql))
            view_name = view_sql.split('VIEW ')[1].split(' AS')[0] if 'VIEW ' in view_sql else 'unknown'
            print(f"  ✅ Created view: {view_name}")
            created_count += 1
        except Exception as e:
            print(f"  ❌ Failed to create view: {e}")
    
    try:
        db.session.commit()
        print(f"✅ Database views completed: {created_count} created")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to commit views: {e}")
        return False

def run_complete_database_optimization():
    """Run complete database optimization process"""
    print("🚀 Starting complete database optimization...")
    print("=" * 60)
    
    results = {
        'indexes': False,
        'constraints': False,
        'views': False,
        'performance_analysis': False
    }
    
    try:
        # 1. Create performance indexes
        results['indexes'] = create_performance_indexes()
        
        # 2. Create database constraints
        results['constraints'] = create_database_constraints()
        
        # 3. Create optimized views
        results['views'] = create_optimized_views()
        
        # 4. Analyze performance
        try:
            analyze_database_performance()
            results['performance_analysis'] = True
        except:
            print("⚠️ Performance analysis skipped (requires PostgreSQL extensions)")
        
        # Summary
        successful_operations = sum(results.values())
        total_operations = len(results)
        
        print("\n" + "=" * 60)
        print(f"🎯 Database Optimization Summary:")
        print(f"   ✅ Successful: {successful_operations}/{total_operations}")
        print(f"   📊 Indexes: {'✅' if results['indexes'] else '❌'}")
        print(f"   🔒 Constraints: {'✅' if results['constraints'] else '❌'}")
        print(f"   👁️ Views: {'✅' if results['views'] else '❌'}")
        print(f"   📈 Analysis: {'✅' if results['performance_analysis'] else '❌'}")
        
        if successful_operations >= 3:
            print("\n🎉 Database optimization completed successfully!")
            print("🚀 Database is ready for high-performance operations")
        else:
            print("\n⚠️ Some optimizations failed. Check logs above.")
        
        print("=" * 60)
        
        return successful_operations >= 2  # At least indexes and constraints should succeed
        
    except Exception as e:
        print(f"❌ Critical error during optimization: {e}")
        return False

# Export main functions
__all__ = [
    'create_performance_indexes',
    'create_database_constraints', 
    'create_optimized_views',
    'analyze_database_performance',
    'run_complete_database_optimization'
]