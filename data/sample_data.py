"""
Sample Data Generator
إنشاء بيانات تجريبية للاختبار - FIXED VERSION
"""

from datetime import datetime, date, time
from models import *
from config.database import db
import random
import string

class SampleDataGenerator:
    """Generate sample data for testing"""
    
    @staticmethod
    def create_admin_user():
        """Create default admin user"""
        try:
            # Check if admin already exists
            existing_admin = User.find_by_username('admin')
            if existing_admin:
                print("ℹ️ Admin user already exists")
                return existing_admin
            
            admin_user = User(
                username='admin',
                email='admin@university.edu',
                full_name='مدير النظام',
                role=UserRole.ADMIN,
                is_active=True
            )
            admin_user.set_password('Admin123!')
            admin_user.save()
            
            print("✅ Admin user created: admin / Admin123!")
            return admin_user
            
        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")
            return None
    
    @staticmethod
    def create_sample_students():
        """Create sample students"""
        try:
            students_data = [
                {
                    'username': 'student1', 'email': 'student1@uni.edu', 'full_name': 'أحمد محمد علي',
                    'university_id': 'CS2021001', 'section': SectionEnum.A, 'study_year': 3
                },
                {
                    'username': 'student2', 'email': 'student2@uni.edu', 'full_name': 'فاطمة أحمد حسن',
                    'university_id': 'CS2021002', 'section': SectionEnum.A, 'study_year': 3
                },
                {
                    'username': 'student3', 'email': 'student3@uni.edu', 'full_name': 'محمد صالح عبدالله',
                    'university_id': 'CS2021003', 'section': SectionEnum.B, 'study_year': 3
                },
                {
                    'username': 'student4', 'email': 'student4@uni.edu', 'full_name': 'زينب علي محمد',
                    'university_id': 'CS2021004', 'section': SectionEnum.B, 'study_year': 3
                },
                {
                    'username': 'student5', 'email': 'student5@uni.edu', 'full_name': 'عبدالرحمن خالد',
                    'university_id': 'CS2021005', 'section': SectionEnum.C, 'study_year': 3
                }
            ]
            
            created_students = []
            
            for student_data in students_data:
                # Check if student already exists
                existing_student = Student.find_by_university_id(student_data['university_id'])
                if existing_student:
                    print(f"ℹ️ Student {student_data['university_id']} already exists")
                    created_students.append(existing_student)
                    continue
                
                # Create user first
                user = User(
                    username=student_data['username'],
                    email=student_data['email'],
                    full_name=student_data['full_name'],
                    role=UserRole.STUDENT,
                    is_active=True
                )
                user.set_password('Student123!')
                user.save()
                
                # Create student profile
                student = Student(
                    user_id=user.id,
                    university_id=student_data['university_id'],
                    section=student_data['section'],
                    study_year=student_data['study_year'],
                    study_type=StudyTypeEnum.MORNING,
                    academic_status=AcademicStatusEnum.ACTIVE
                )
                student.set_secret_code('ABC123')
                student.save()
                
                created_students.append(student)
                print(f"✅ Created student: {student_data['university_id']}")
            
            return created_students
            
        except Exception as e:
            print(f"❌ Failed to create sample students: {e}")
            return []
    
    @staticmethod
    def create_sample_teachers():
        """Create sample teachers"""
        try:
            teachers_data = [
                {
                    'username': 'teacher1', 'email': 'teacher1@uni.edu', 'full_name': 'د. عبدالعزيز الأحمد',
                    'employee_id': 'T001', 'department': 'Computer Science', 'degree': AcademicDegreeEnum.PHD
                },
                {
                    'username': 'teacher2', 'email': 'teacher2@uni.edu', 'full_name': 'د. سارة المحمد',
                    'employee_id': 'T002', 'department': 'Computer Science', 'degree': AcademicDegreeEnum.MASTER
                },
                {
                    'username': 'teacher3', 'email': 'teacher3@uni.edu', 'full_name': 'د. خالد البصري',
                    'employee_id': 'T003', 'department': 'Information Technology', 'degree': AcademicDegreeEnum.PHD
                }
            ]
            
            created_teachers = []
            
            for teacher_data in teachers_data:
                # Check if teacher already exists
                existing_teacher = Teacher.find_by_employee_id(teacher_data['employee_id'])
                if existing_teacher:
                    print(f"ℹ️ Teacher {teacher_data['employee_id']} already exists")
                    created_teachers.append(existing_teacher)
                    continue
                
                # Create user first
                user = User(
                    username=teacher_data['username'],
                    email=teacher_data['email'],
                    full_name=teacher_data['full_name'],
                    role=UserRole.TEACHER,
                    is_active=True
                )
                user.set_password('Teacher123!')
                user.save()
                
                # Create teacher profile
                teacher = Teacher(
                    user_id=user.id,
                    employee_id=teacher_data['employee_id'],
                    department=teacher_data['department'],
                    academic_degree=teacher_data['degree'],
                    office_location=f"Office {teacher_data['employee_id']}"
                )
                teacher.save()
                
                created_teachers.append(teacher)
                print(f"✅ Created teacher: {teacher_data['employee_id']}")
            
            return created_teachers
            
        except Exception as e:
            print(f"❌ Failed to create sample teachers: {e}")
            return []
    
    @staticmethod
    def create_sample_subjects():
        """Create sample subjects"""
        try:
            subjects_data = [
                {'code': 'CS301', 'name': 'Data Structures and Algorithms', 'credit_hours': 3, 'year': 3, 'semester': SemesterEnum.FIRST},
                {'code': 'CS302', 'name': 'Database Systems', 'credit_hours': 3, 'year': 3, 'semester': SemesterEnum.FIRST},
                {'code': 'CS303', 'name': 'Operating Systems', 'credit_hours': 3, 'year': 3, 'semester': SemesterEnum.SECOND},
                {'code': 'CS304', 'name': 'Computer Networks', 'credit_hours': 3, 'year': 3, 'semester': SemesterEnum.SECOND},
                {'code': 'CS305', 'name': 'Software Engineering', 'credit_hours': 4, 'year': 3, 'semester': SemesterEnum.FIRST}
            ]
            
            created_subjects = []
            
            for subject_data in subjects_data:
                # Check if subject already exists
                existing_subject = Subject.find_by_code(subject_data['code'])
                if existing_subject:
                    print(f"ℹ️ Subject {subject_data['code']} already exists")
                    created_subjects.append(existing_subject)
                    continue
                
                subject = Subject(
                    code=subject_data['code'],
                    name=subject_data['name'],
                    department='Computer Science',
                    credit_hours=subject_data['credit_hours'],
                    study_year=subject_data['year'],
                    semester=subject_data['semester'],
                    is_active=True
                )
                subject.save()
                
                created_subjects.append(subject)
                print(f"✅ Created subject: {subject_data['code']}")
            
            return created_subjects
            
        except Exception as e:
            print(f"❌ Failed to create sample subjects: {e}")
            return []
    
    @staticmethod
    def create_sample_rooms():
        """Create sample rooms with GPS coordinates"""
        try:
            # Sample coordinates for Baghdad University (approximate)
            base_lat, base_lng = 33.2778, 44.3661
            
            rooms_data = [
                {'name': 'A101', 'building': 'Computer Science Building', 'floor': 1, 'capacity': 40},
                {'name': 'A102', 'building': 'Computer Science Building', 'floor': 1, 'capacity': 35},
                {'name': 'A201', 'building': 'Computer Science Building', 'floor': 2, 'capacity': 45},
                {'name': 'B101', 'building': 'Engineering Building', 'floor': 1, 'capacity': 50},
                {'name': 'B201', 'building': 'Engineering Building', 'floor': 2, 'capacity': 60}
            ]
            
            created_rooms = []
            
            for i, room_data in enumerate(rooms_data):
                # Check if room already exists
                existing_room = Room.find_by_name(room_data['name'])
                if existing_room:
                    print(f"ℹ️ Room {room_data['name']} already exists")
                    created_rooms.append(existing_room)
                    continue
                
                # Generate slightly different coordinates for each room
                room_lat = base_lat + (i * 0.001)  # Small offset
                room_lng = base_lng + (i * 0.001)
                
                room = Room(
                    name=room_data['name'],
                    building=room_data['building'],
                    floor=room_data['floor'],
                    room_type=RoomTypeEnum.CLASSROOM,
                    capacity=room_data['capacity'],
                    center_latitude=room_lat,
                    center_longitude=room_lng,
                    ground_reference_altitude=50.0,  # Base altitude
                    floor_altitude=50.0 + (room_data['floor'] - 1) * 3.5,  # 3.5m per floor
                    ceiling_height=3.0,
                    is_active=True
                )
                
                # Set rectangular GPS polygon (10m x 8m room)
                room.set_rectangular_polygon(room_lat, room_lng, 10, 8)
                room.save()
                
                created_rooms.append(room)
                print(f"✅ Created room: {room_data['name']}")
            
            return created_rooms
            
        except Exception as e:
            print(f"❌ Failed to create sample rooms: {e}")
            return []
    
    @classmethod
    def generate_all_sample_data(cls):
        """Generate all sample data"""
        print("🚀 Starting sample data generation...")
        
        try:
            # Generate data step by step
            print("1️⃣ Creating admin user...")
            admin = cls.create_admin_user()
            
            print("2️⃣ Creating sample students...")
            students = cls.create_sample_students()
            
            print("3️⃣ Creating sample teachers...")
            teachers = cls.create_sample_teachers()
            
            print("4️⃣ Creating sample subjects...")
            subjects = cls.create_sample_subjects()
            
            print("5️⃣ Creating sample rooms...")
            rooms = cls.create_sample_rooms()
            
            print("✅ Sample data generation completed!")
            print(f"📊 Generated: {len(students)} students, {len(teachers)} teachers, {len(subjects)} subjects, {len(rooms)} rooms")
            
            return {
                'admin': admin,
                'students': students,
                'teachers': teachers,
                'subjects': subjects,
                'rooms': rooms
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to generate sample data: {e}")
            return None

def test_sample_data():
    """Test sample data functionality"""
    print("🧪 Testing sample data...")
    
    # Test basic queries
    users_count = User.query.count()
    students_count = Student.query.count()
    teachers_count = Teacher.query.count()
    subjects_count = Subject.query.count()
    rooms_count = Room.query.count()
    
    print(f"📊 Data counts:")
    print(f"   Users: {users_count}")
    print(f"   Students: {students_count}")
    print(f"   Teachers: {teachers_count}")
    print(f"   Subjects: {subjects_count}")
    print(f"   Rooms: {rooms_count}")
    
    # Test sample user
    sample_user = User.query.first()
    if sample_user:
        print(f"👤 Sample user: {sample_user.username}")
        print(f"   Name: {sample_user.full_name}")
        print(f"   Role: {sample_user.role.value}")
    
    # Test sample student
    sample_student = Student.query.first()
    if sample_student:
        print(f"🎓 Sample student: {sample_student.university_id}")
        print(f"   Section: {sample_student.section.value}")
        print(f"   Year: {sample_student.study_year}")
    
    print("✅ Sample data testing completed!")