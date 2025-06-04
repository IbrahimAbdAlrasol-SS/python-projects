"""
Complete Sample Data Generator
مولد البيانات التجريبية الكامل لجميع النماذج
"""

from datetime import datetime, date, time, timedelta
from config.database import db
from models import *
import random
import secrets

class CompleteSampleDataGenerator:
    """Generate comprehensive sample data for all models"""
    
    def __init__(self):
        self.created_data = {
            'users': [],
            'students': [],
            'teachers': [],
            'subjects': [],
            'rooms': [],
            'schedules': [],
            'lectures': [],
            'qr_sessions': [],
            'attendance_records': [],
            'assignments': [],
            'submissions': [],
            'notifications': [],
            'student_counters': [],
            'system_settings': []
        }
    
    def generate_all_sample_data(self):
        """Generate complete sample data"""
        print("🎯 Generating comprehensive sample data...")
        print("=" * 50)
        
        try:
            # Level 1: Core entities (no dependencies)
            self._create_system_settings()
            self._create_users()
            self._create_subjects()
            self._create_rooms()
            
            # Level 2: Entities with basic dependencies
            self._create_students()
            self._create_teachers()
            
            # Level 3: Complex entities
            self._create_schedules()
            self._create_student_counters()
            
            # Level 4: Operational entities
            self._create_lectures()
            self._create_assignments()
            
            # Level 5: Activity entities
            self._create_qr_sessions()
            self._create_submissions()
            self._create_attendance_records()
            
            # Level 6: Communication entities
            self._create_notifications()
            
            # Commit all changes
            db.session.commit()
            
            # Print summary
            self._print_summary()
            
            print("🎉 Complete sample data generated successfully!")
            return self.created_data
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to generate sample data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_system_settings(self):
        """Create system settings"""
        print("⚙️ Creating system settings...")
        
        # Initialize default settings
        created_count = SystemSetting.initialize_default_settings()
        
        # Add some custom settings for testing
        custom_settings = [
            {
                'key': 'test_mode_enabled',
                'name': 'وضع الاختبار',
                'setting_type': SettingTypeEnum.BOOLEAN,
                'category': SettingCategoryEnum.GENERAL,
                'default_value': 'true',
                'description': 'تمكين وضع الاختبار للنظام',
                'is_public': True
            },
            {
                'key': 'sample_data_version',
                'name': 'إصدار البيانات التجريبية',
                'setting_type': SettingTypeEnum.STRING,
                'category': SettingCategoryEnum.GENERAL,
                'default_value': '1.0.0',
                'description': 'إصدار البيانات التجريبية المحملة',
                'is_readonly': True
            }
        ]
        
        for setting_data in custom_settings:
            setting = SystemSetting.create_setting(**setting_data)
            self.created_data['system_settings'].append(setting)
        
        print(f"  ✅ Created {created_count + len(custom_settings)} system settings")
    
    def _create_users(self):
        """Create users (admins, base users for students/teachers)"""
        print("👥 Creating users...")
        
        # Admin users
        admin_users = [
            {
                'username': 'admin',
                'email': 'admin@university.edu',
                'full_name': 'مدير النظام الرئيسي',
                'role': UserRole.ADMIN,
                'phone': '+964771234567'
            },
            {
                'username': 'admin2',
                'email': 'admin2@university.edu', 
                'full_name': 'مدير النظام المساعد',
                'role': UserRole.ADMIN,
                'phone': '+964771234568'
            }
        ]
        
        # Teacher users
        teacher_users = [
            {
                'username': 'dr_ahmed',
                'email': 'ahmed.ali@university.edu',
                'full_name': 'د. أحمد علي محمد',
                'role': UserRole.TEACHER,
                'phone': '+964771234001'
            },
            {
                'username': 'dr_fatima',
                'email': 'fatima.hassan@university.edu',
                'full_name': 'د. فاطمة حسن إبراهيم',
                'role': UserRole.TEACHER,
                'phone': '+964771234002'
            },
            {
                'username': 'dr_omar',
                'email': 'omar.khalil@university.edu',
                'full_name': 'د. عمر خليل محمود',
                'role': UserRole.TEACHER,
                'phone': '+964771234003'
            },
            {
                'username': 'dr_sara',
                'email': 'sara.ahmad@university.edu',
                'full_name': 'د. سارة أحمد صالح',
                'role': UserRole.TEACHER,
                'phone': '+964771234004'
            },
            {
                'username': 'dr_mohammed',
                'email': 'mohammed.jawad@university.edu',
                'full_name': 'د. محمد جواد حسين',
                'role': UserRole.TEACHER,
                'phone': '+964771234005'
            }
        ]
        
        # Student users (20 students)
        student_names = [
            'أحمد محمد علي', 'فاطمة حسن إبراهيم', 'علي أحمد صالح', 'زينب عبد الله محمد',
            'محمد علي حسن', 'مريم صالح أحمد', 'حسن محمد علي', 'نور فاطمة حسين',
            'عبد الله أحمد محمد', 'ريم علي صالح', 'يوسف محمد حسن', 'هدى أحمد علي',
            'صالح عبد الله محمد', 'آية حسن صالح', 'كرار محمد علي', 'دعاء أحمد حسين',
            'حيدر علي محمد', 'زهراء صالح أحمد', 'مصطفى محمد حسن', 'رقية علي أحمد'
        ]
        
        student_users = []
        for i, name in enumerate(student_names, 1):
            username = f'student{i:02d}'
            email = f'student{i:02d}@university.edu'
            student_users.append({
                'username': username,
                'email': email,
                'full_name': name,
                'role': UserRole.STUDENT,
                'phone': f'+96477123{1000 + i}'
            })
        
        # Create all users
        all_users = admin_users + teacher_users + student_users
        for user_data in all_users:
            user = User(**user_data)
            user.set_password('Password123!')  # Default password for all
            user.save()
            self.created_data['users'].append(user)
        
        print(f"  ✅ Created {len(all_users)} users (2 admins, 5 teachers, 20 students)")
    
    def _create_subjects(self):
        """Create academic subjects"""
        print("📚 Creating subjects...")
        
        subjects_data = [
            # First Year Subjects
            {
                'code': 'CS101',
                'name': 'مقدمة في علوم الحاسوب',
                'department': 'علوم الحاسوب',
                'credit_hours': 3,
                'study_year': 1,
                'semester': SemesterEnum.FIRST
            },
            {
                'code': 'MATH101',
                'name': 'الرياضيات المتقطعة',
                'department': 'الرياضيات',
                'credit_hours': 3,
                'study_year': 1,
                'semester': SemesterEnum.FIRST
            },
            {
                'code': 'ENG101',
                'name': 'اللغة الإنجليزية',
                'department': 'اللغات',
                'credit_hours': 2,
                'study_year': 1,
                'semester': SemesterEnum.FIRST
            },
            
            # Second Year Subjects
            {
                'code': 'CS201',
                'name': 'البرمجة الكائنية',
                'department': 'علوم الحاسوب',
                'credit_hours': 4,
                'study_year': 2,
                'semester': SemesterEnum.FIRST
            },
            {
                'code': 'CS202',
                'name': 'هياكل البيانات',
                'department': 'علوم الحاسوب',
                'credit_hours': 4,
                'study_year': 2,
                'semester': SemesterEnum.SECOND
            },
            {
                'code': 'MATH201',
                'name': 'التفاضل والتكامل',
                'department': 'الرياضيات',
                'credit_hours': 3,
                'study_year': 2,
                'semester': SemesterEnum.FIRST
            },
            
            # Third Year Subjects
            {
                'code': 'CS301',
                'name': 'قواعد البيانات',
                'department': 'علوم الحاسوب',
                'credit_hours': 4,
                'study_year': 3,
                'semester': SemesterEnum.FIRST
            },
            {
                'code': 'CS302',
                'name': 'هندسة البرمجيات',
                'department': 'علوم الحاسوب',
                'credit_hours': 3,
                'study_year': 3,
                'semester': SemesterEnum.SECOND
            },
            {
                'code': 'CS303',
                'name': 'الخوارزميات',
                'department': 'علوم الحاسوب',
                'credit_hours': 4,
                'study_year': 3,
                'semester': SemesterEnum.FIRST
            },
            
            # Fourth Year Subjects
            {
                'code': 'CS401',
                'name': 'الذكاء الاصطناعي',
                'department': 'علوم الحاسوب',
                'credit_hours': 4,
                'study_year': 4,
                'semester': SemesterEnum.FIRST
            },
            {
                'code': 'CS402',
                'name': 'أمن المعلومات',
                'department': 'علوم الحاسوب',
                'credit_hours': 3,
                'study_year': 4,
                'semester': SemesterEnum.SECOND
            },
            {
                'code': 'CS403',
                'name': 'مشروع التخرج',
                'department': 'علوم الحاسوب',
                'credit_hours': 6,
                'study_year': 4,
                'semester': SemesterEnum.SECOND
            }
        ]
        
        for subject_data in subjects_data:
            subject = Subject(**subject_data)
            subject.save()
            self.created_data['subjects'].append(subject)
        
        print(f"  ✅ Created {len(subjects_data)} subjects")
    
    def _create_rooms(self):
        """Create rooms with GPS coordinates"""
        print("🏢 Creating rooms...")
        
        # Base coordinates for university (Baghdad example)
        base_lat = 33.3152
        base_lng = 44.3661
        base_altitude = 50.0
        
        rooms_data = [
            # Building A - Ground Floor
            {
                'name': 'A101',
                'building': 'مبنى A',
                'floor': 1,
                'room_type': RoomTypeEnum.CLASSROOM,
                'capacity': 30,
                'center_latitude': base_lat + 0.0001,
                'center_longitude': base_lng + 0.0001,
                'ground_reference_altitude': base_altitude,
                'floor_altitude': base_altitude + 0.5,
                'ceiling_height': 3.0,
                'wifi_ssid': 'University_A101'
            },
            {
                'name': 'A102',
                'building': 'مبنى A',
                'floor': 1,
                'room_type': RoomTypeEnum.LAB,
                'capacity': 25,
                'center_latitude': base_lat + 0.0002,
                'center_longitude': base_lng + 0.0001,
                'ground_reference_altitude': base_altitude,
                'floor_altitude': base_altitude + 0.5,
                'ceiling_height': 3.0,
                'wifi_ssid': 'University_A102'
            },
            
            # Building A - Second Floor
            {
                'name': 'A201',
                'building': 'مبنى A',
                'floor': 2,
                'room_type': RoomTypeEnum.CLASSROOM,
                'capacity': 35,
                'center_latitude': base_lat + 0.0001,
                'center_longitude': base_lng + 0.0001,
                'ground_reference_altitude': base_altitude,
                'floor_altitude': base_altitude + 3.5,
                'ceiling_height': 3.0,
                'wifi_ssid': 'University_A201'
            },
            {
                'name': 'A202',
                'building': 'مبنى A',
                'floor': 2,
                'room_type': RoomTypeEnum.CLASSROOM,
                'capacity': 40,
                'center_latitude': base_lat + 0.0002,
                'center_longitude': base_lng + 0.0001,
                'ground_reference_altitude': base_altitude,
                'floor_altitude': base_altitude + 3.5,
                'ceiling_height': 3.0,
                'wifi_ssid': 'University_A202'
            },
            
            # Building B
            {
                'name': 'B101',
                'building': 'مبنى B',
                'floor': 1,
                'room_type': RoomTypeEnum.AUDITORIUM,
                'capacity': 100,
                'center_latitude': base_lat + 0.0003,
                'center_longitude': base_lng + 0.0002,
                'ground_reference_altitude': base_altitude,
                'floor_altitude': base_altitude + 0.5,
                'ceiling_height': 4.0,
                'wifi_ssid': 'University_B101'
            },
            {
                'name': 'B201',
                'building': 'مبنى B',
                'floor': 2,
                'room_type': RoomTypeEnum.LAB,
                'capacity': 20,
                'center_latitude': base_lat + 0.0003,
                'center_longitude': base_lng + 0.0002,
                'ground_reference_altitude': base_altitude,
                'floor_altitude': base_altitude + 3.5,
                'ceiling_height': 3.0,
                'wifi_ssid': 'University_B201'
            },
            
            # Building C
            {
                'name': 'C101',
                'building': 'مبنى C',
                'floor': 1,
                'room_type': RoomTypeEnum.CLASSROOM,
                'capacity': 45,
                'center_latitude': base_lat + 0.0004,
                'center_longitude': base_lng + 0.0003,
                'ground_reference_altitude': base_altitude,
                'floor_altitude': base_altitude + 0.5,
                'ceiling_height': 3.0,
                'wifi_ssid': 'University_C101'
            },
            {
                'name': 'C102',
                'building': 'مبنى C',
                'floor': 1,
                'room_type': RoomTypeEnum.CLASSROOM,
                'capacity': 35,
                'center_latitude': base_lat + 0.0005,
                'center_longitude': base_lng + 0.0003,
                'ground_reference_altitude': base_altitude,
                'floor_altitude': base_altitude + 0.5,
                'ceiling_height': 3.0,
                'wifi_ssid': 'University_C102'
            }
        ]
        
        for room_data in rooms_data:
            room = Room(**room_data)
            # Set GPS polygon for each room
            room.set_rectangular_polygon(
                room_data['center_latitude'],
                room_data['center_longitude'],
                width_meters=8,
                height_meters=6
            )
            room.save()
            self.created_data['rooms'].append(room)
        
        print(f"  ✅ Created {len(rooms_data)} rooms with GPS coordinates")
    
    def _create_students(self):
        """Create student profiles"""
        print("🎓 Creating students...")
        
        # Get student users
        student_users = [u for u in self.created_data['users'] if u.role == UserRole.STUDENT]
        
        sections = [SectionEnum.A, SectionEnum.B, SectionEnum.C]
        study_years = [1, 2, 3, 4]
        
        for i, user in enumerate(student_users):
            student = Student(
                user_id=user.id,
                university_id=f'CS{2021000 + i + 1:03d}',  # CS2021001, CS2021002, etc.
                section=random.choice(sections),
                study_year=random.choice(study_years),
                study_type=StudyTypeEnum.MORNING,
                academic_status=AcademicStatusEnum.ACTIVE,
                face_registered=random.choice([True, False])
            )
            
            # Set secret code
            secret_code = secrets.token_urlsafe(6).upper()[:8]
            student.set_secret_code(secret_code)
            
            # Some students have Telegram IDs
            if random.random() < 0.7:  # 70% have Telegram
                student.telegram_id = 1000000000 + i
            
            student.save()
            self.created_data['students'].append(student)
        
        print(f"  ✅ Created {len(student_users)} students")
    
    def _create_teachers(self):
        """Create teacher profiles"""
        print("👨‍🏫 Creating teachers...")
        
        # Get teacher users
        teacher_users = [u for u in self.created_data['users'] if u.role == UserRole.TEACHER]
        
        departments = ['علوم الحاسوب', 'الرياضيات', 'اللغات', 'الفيزياء', 'الكيمياء']
        degrees = [AcademicDegreeEnum.PHD, AcademicDegreeEnum.MASTER, AcademicDegreeEnum.PROFESSOR]
        
        for i, user in enumerate(teacher_users):
            teacher = Teacher(
                user_id=user.id,
                employee_id=f'EMP{20001 + i:03d}',  # EMP20001, EMP20002, etc.
                department=random.choice(departments),
                specialization=f'تخصص {i+1}',
                academic_degree=random.choice(degrees),
                office_location=f'مكتب {random.randint(101, 205)}'
            )
            
            # Assign subjects
            teacher_subjects = random.sample([s.code for s in self.created_data['subjects']], 
                                           k=random.randint(2, 4))
            teacher.subjects = teacher_subjects
            
            teacher.save()
            self.created_data['teachers'].append(teacher)
        
        print(f"  ✅ Created {len(teacher_users)} teachers")
    
    def _create_schedules(self):
        """Create class schedules"""
        print("📅 Creating schedules...")
        
        current_year = datetime.now().year
        academic_year = f"{current_year}-{current_year + 1}"
        
        # Create schedules for each subject
        for subject in self.created_data['subjects']:
            # Assign teacher
            teacher = random.choice(self.created_data['teachers'])
            
            # Assign room
            room = random.choice(self.created_data['rooms'])
            
            # Create schedule for each section that has students of this year
            student_years = {s.study_year for s in self.created_data['students']}
            if subject.study_year in student_years:
                student_sections = {s.section for s in self.created_data['students'] 
                                  if s.study_year == subject.study_year}
                
                for section in student_sections:
                    # Random day and time
                    day_of_week = random.randint(1, 5)  # Sunday to Thursday
                    start_hour = random.randint(8, 14)  # 8 AM to 2 PM
                    start_time = time(start_hour, 0)
                    end_time = time(start_hour + 2, 0)  # 2-hour classes
                    
                    schedule = Schedule(
                        subject_id=subject.id,
                        teacher_id=teacher.id,
                        room_id=room.id,
                        section=section,
                        day_of_week=day_of_week,
                        start_time=start_time,
                        end_time=end_time,
                        academic_year=academic_year,
                        semester=subject.semester
                    )
                    
                    try:
                        schedule.save()
                        self.created_data['schedules'].append(schedule)
                    except ValueError as e:
                        # Skip conflicting schedules
                        print(f"    ⚠️ Skipped conflicting schedule: {e}")
                        continue
        
        print(f"  ✅ Created {len(self.created_data['schedules'])} schedules")
    
    def _create_student_counters(self):
        """Create student counters"""
        print("🔢 Creating student counters...")
        
        current_year = datetime.now().year
        academic_year = f"{current_year}-{current_year + 1}"
        
        for student in self.created_data['students']:
            # Get subjects for this student's year
            student_subjects = [s for s in self.created_data['subjects'] 
                             if s.study_year == student.study_year]
            
            for subject in student_subjects[:3]:  # Limit to 3 subjects per student
                counter = StudentCounter.get_or_create_counter(
                    student_id=student.id,
                    subject_id=subject.id,
                    academic_year=academic_year,
                    semester=subject.semester
                )
                
                # Randomize counter values for testing
                counter.counter_value = random.randint(0, 3)
                counter.consecutive_on_time = random.randint(0, 5)
                
                # Some students are muted
                if counter.counter_value >= 1 and random.random() < 0.3:
                    counter.is_muted = True
                    counter.muted_at = datetime.utcnow() - timedelta(days=random.randint(1, 10))
                    counter.status = CounterStatusEnum.MUTED
                    counter.mute_reason = "تأخير متكرر في التسليم"
                
                # Add Telegram info
                if student.telegram_id:
                    counter.telegram_user_id = student.telegram_id
                    counter.telegram_username = f"student_{student.university_id.lower()}"
                
                counter.save()
                self.created_data['student_counters'].append(counter)
        
        print(f"  ✅ Created {len(self.created_data['student_counters'])} student counters")
    
    def _create_lectures(self):
        """Create lectures from schedules"""
        print("🎤 Creating lectures...")
        
        # Create lectures for the past week and next week
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() + timedelta(days=7)
        
        for schedule in self.created_data['schedules']:
            current_date = start_date
            
            while current_date <= end_date:
                # Check if this date matches the schedule's day
                weekday = current_date.weekday()
                schedule_day = (schedule.day_of_week % 7)  # Convert to Python weekday
                
                if weekday == schedule_day:
                    lecture = Lecture.create_from_schedule(
                        schedule=schedule,
                        lecture_date=current_date,
                        topic=f"محاضرة {schedule.subject.name} - {current_date}",
                        qr_enabled=True
                    )
                    
                    # Set status based on date
                    if current_date < date.today():
                        lecture.status = LectureStatusEnum.COMPLETED
                        lecture.actual_start_time = datetime.combine(current_date, schedule.start_time)
                        lecture.actual_end_time = datetime.combine(current_date, schedule.end_time)
                    elif current_date == date.today():
                        lecture.status = LectureStatusEnum.ACTIVE
                        lecture.actual_start_time = datetime.combine(current_date, schedule.start_time)
                    else:
                        lecture.status = LectureStatusEnum.SCHEDULED
                    
                    lecture.save()
                    self.created_data['lectures'].append(lecture)
                
                current_date += timedelta(days=1)
        
        print(f"  ✅ Created {len(self.created_data['lectures'])} lectures")
    
    def _create_assignments(self):
        """Create assignments"""
        print("📝 Creating assignments...")
        
        assignment_types = [AssignmentTypeEnum.HOMEWORK, AssignmentTypeEnum.PROJECT, 
                          AssignmentTypeEnum.QUIZ, AssignmentTypeEnum.RESEARCH]
        
        for subject in self.created_data['subjects'][:6]:  # Limit to first 6 subjects
            teacher = random.choice([t for t in self.created_data['teachers'] 
                                   if subject.code in (t.subjects or [])])
            
            # Get sections that have students for this subject
            target_sections = list({s.section.value for s in self.created_data['students'] 
                                 if s.study_year == subject.study_year})
            
            if not target_sections:
                continue
            
            for i in range(random.randint(1, 3)):  # 1-3 assignments per subject
                due_date = datetime.now() + timedelta(days=random.randint(1, 30))
                
                assignment = Assignment.create_assignment(
                    title=f"واجب {i+1} - {subject.name}",
                    description=f"وصف الواجب {i+1} في مادة {subject.name}. يجب تسليم الحل كاملاً مع التوضيحات.",
                    subject_id=subject.id,
                    teacher_id=teacher.id,
                    due_date=due_date,
                    target_sections=target_sections,
                    target_year=subject.study_year,
                    created_by_user_id=teacher.user_id,
                    assignment_type=random.choice(assignment_types),
                    max_score=random.choice([10, 20, 25, 50, 100]),
                    weight_percentage=random.randint(5, 20)
                )
                
                # Publish some assignments
                if random.random() < 0.8:  # 80% published
                    assignment.publish_assignment()
                
                self.created_data['assignments'].append(assignment)
        
        print(f"  ✅ Created {len(self.created_data['assignments'])} assignments")
    
    def _create_qr_sessions(self):
        """Create QR sessions for active lectures"""
        print("📱 Creating QR sessions...")
        
        # Create QR sessions for today's lectures
        today_lectures = [l for l in self.created_data['lectures'] 
                         if l.lecture_date == date.today() and l.status == LectureStatusEnum.ACTIVE]
        
        for lecture in today_lectures:
            # Get teacher for this lecture
            teacher = lecture.schedule.teacher
            
            try:
                qr_session, encryption_key = QRSession.create_for_lecture(
                    lecture_id=lecture.id,
                    generated_by_teacher_id=teacher.id,
                    duration_minutes=random.randint(5, 30)
                )
                
                self.created_data['qr_sessions'].append(qr_session)
                
            except ValueError as e:
                print(f"    ⚠️ Skipped QR session: {e}")
        
        print(f"  ✅ Created {len(self.created_data['qr_sessions'])} QR sessions")
    
    def _create_submissions(self):
        """Create assignment submissions"""
        print("📋 Creating submissions...")
        
        active_assignments = [a for a in self.created_data['assignments'] 
                            if a.status == AssignmentStatusEnum.ACTIVE]
        
        for assignment in active_assignments:
            # Get students who can submit this assignment
            eligible_students = [s for s in self.created_data['students'] 
                               if (s.section.value in assignment.target_sections and 
                                   s.study_year == assignment.target_year)]
            
            # Random subset of students submit
            submitting_students = random.sample(eligible_students, 
                                               k=min(len(eligible_students), 
                                                   random.randint(3, len(eligible_students))))
            
            for student in submitting_students:
                try:
                    submission = Submission(
                        assignment_id=assignment.id,
                        student_id=student.id,
                        submission_type=random.choice([SubmissionTypeEnum.TEXT_SUBMISSION, 
                                                     SubmissionTypeEnum.FILE_UPLOAD]),
                        text_content=f"حل الواجب من الطالب {student.user.full_name}. هذا نص تجريبي للحل.",
                        submission_title=f"حل {assignment.title}"
                    )
                    
                    # Submit it
                    submission.submit_submission()
                    
                    # Some submissions are graded
                    if random.random() < 0.6:  # 60% graded
                        score = random.randint(60, 100)
                        submission.grade_submission(
                            score=score,
                            feedback=f"تقييم جيد. الدرجة: {score}/{assignment.max_score}",
                            graded_by_user_id=assignment.teacher.user_id
                        )
                    
                    self.created_data['submissions'].append(submission)
                    
                except ValueError as e:
                    print(f"    ⚠️ Skipped submission: {e}")
        
        print(f"  ✅ Created {len(self.created_data['submissions'])} submissions")
    
    def _create_attendance_records(self):
        """Create attendance records"""
        print("✅ Creating attendance records...")
        
        # Create attendance for completed lectures
        completed_lectures = [l for l in self.created_data['lectures'] 
                             if l.status == LectureStatusEnum.COMPLETED]
        
        for lecture in completed_lectures[:5]:  # Limit to 5 lectures for demo
            # Get students who should attend this lecture
            schedule = lecture.schedule
            attending_students = [s for s in self.created_data['students'] 
                                if (s.section == schedule.section and 
                                    s.study_year == schedule.subject.study_year)]
            
            # Random subset attend
            attended_students = random.sample(attending_students,
                                            k=min(len(attending_students),
                                                random.randint(2, len(attending_students))))
            
            for student in attended_students:
                try:
                    attendance = AttendanceRecord.create_attendance_record(
                        student_id=student.id,
                        lecture_id=lecture.id
                    )
                    
                    # Simulate verification process
                    room = schedule.room
                    
                    # Location verification
                    lat = float(room.center_latitude) + random.uniform(-0.00005, 0.00005)
                    lng = float(room.center_longitude) + random.uniform(-0.00005, 0.00005)
                    alt = float(room.floor_altitude) + random.uniform(-1, 1)
                    
                    attendance.verify_location(lat, lng, alt, accuracy=3.5)
                    
                    # QR verification (if available)
                    qr_sessions = [q for q in self.created_data['qr_sessions'] 
                                 if q.lecture_id == lecture.id]
                    if qr_sessions:
                        attendance.verify_qr_code(qr_sessions[0].id)
                    
                    # Face verification
                    face_score = random.uniform(0.75, 0.98)
                    attendance.verify_face(face_score)
                    
                    self.created_data['attendance_records'].append(attendance)
                    
                except ValueError as e:
                    print(f"    ⚠️ Skipped attendance: {e}")
        
        print(f"  ✅ Created {len(self.created_data['attendance_records'])} attendance records")
    
    def _create_notifications(self):
        """Create sample notifications"""
        print("🔔 Creating notifications...")
        
        # System notifications
        system_notifications = [
            {
                'title': 'مرحباً بكم في نظام الحضور الذكي',
                'message': 'تم تفعيل النظام بنجاح. يمكنكم الآن تسجيل الحضور والمشاركة في الأنشطة التعليمية.',
                'notification_type': NotificationTypeEnum.SYSTEM,
                'is_broadcast': True,
                'target_role': 'student'
            },
            {
                'title': 'تحديث مهم على النظام',
                'message': 'تم إضافة ميزات جديدة للنظام. يرجى مراجعة التحديثات.',
                'notification_type': NotificationTypeEnum.ANNOUNCEMENT,
                'is_broadcast': True,
                'target_role': 'teacher'
            }
        ]
        
        for notif_data in system_notifications:
            notification = Notification.create_notification(**notif_data)
            self.created_data['notifications'].append(notification)
        
        # Student-specific notifications
        for student in self.created_data['students'][:5]:  # First 5 students
            notification = Notification.create_notification(
                title='إشعار شخصي',
                message=f'مرحباً {student.user.full_name}، هذا إشعار تجريبي خاص بك.',
                notification_type=NotificationTypeEnum.SYSTEM,
                recipients={'student_id': student.id}
            )
            self.created_data['notifications'].append(notification)
        
        print(f"  ✅ Created {len(self.created_data['notifications'])} notifications")
    
    def _print_summary(self):
        """Print summary of created data"""
        print("\n" + "=" * 50)
        print("📊 Sample Data Generation Summary")
        print("=" * 50)
        
        for data_type, items in self.created_data.items():
            count = len(items)
            if count > 0:
                print(f"  {data_type}: {count}")
        
        print("=" * 50)
    
    def cleanup_sample_data(self):
        """Clean up all sample data"""
        print("🧹 Cleaning up sample data...")
        
        try:
            # Delete in reverse dependency order
            db.session.query(AttendanceRecord).delete()
            db.session.query(Submission).delete()
            db.session.query(QRSession).delete()
            db.session.query(Notification).delete()
            db.session.query(Assignment).delete()
            db.session.query(Lecture).delete()
            db.session.query(StudentCounter).delete()
            db.session.query(Schedule).delete()
            db.session.query(Student).delete()
            db.session.query(Teacher).delete()
            db.session.query(Room).delete()
            db.session.query(Subject).delete()
            
            # Keep admin user, delete others
            db.session.query(User).filter(User.username != 'admin').delete()
            
            # Keep system settings
            # SystemSetting can stay
            
            db.session.commit()
            print("✅ Sample data cleaned up successfully")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to cleanup sample data: {e}")

# Convenience functions
def generate_complete_sample_data():
    """Generate complete sample data"""
    generator = CompleteSampleDataGenerator()
    return generator.generate_all_sample_data()

def cleanup_all_sample_data():
    """Cleanup all sample data"""
    generator = CompleteSampleDataGenerator()
    return generator.cleanup_sample_data()

def test_sample_data():
    """Test the generated sample data"""
    print("🧪 Testing sample data...")
    
    try:
        # Test data counts
        user_count = User.query.count()
        student_count = Student.query.count()
        teacher_count = Teacher.query.count()
        subject_count = Subject.query.count()
        room_count = Room.query.count()
        schedule_count = Schedule.query.count()
        lecture_count = Lecture.query.count()
        assignment_count = Assignment.query.count()
        
        print(f"📊 Data validation:")
        print(f"  Users: {user_count}")
        print(f"  Students: {student_count}")
        print(f"  Teachers: {teacher_count}")
        print(f"  Subjects: {subject_count}")
        print(f"  Rooms: {room_count}")
        print(f"  Schedules: {schedule_count}")
        print(f"  Lectures: {lecture_count}")
        print(f"  Assignments: {assignment_count}")
        
        # Test relationships
        sample_student = Student.query.first()
        if sample_student:
            print(f"  Sample student: {sample_student.user.full_name}")
            print(f"  Student ID: {sample_student.university_id}")
        
        # Test admin login
        admin = User.query.filter_by(username='admin').first()
        if admin and admin.check_password('Password123!'):
            print("  ✅ Admin login test passed")
        else:
            print("  ❌ Admin login test failed")
        
        print("✅ Sample data test completed")
        return True
        
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        return False

# Export functions
__all__ = [
    'CompleteSampleDataGenerator',
    'generate_complete_sample_data',
    'cleanup_all_sample_data',
    'test_sample_data'
]