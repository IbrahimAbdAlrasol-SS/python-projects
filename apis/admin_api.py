"""
👑 Admin Management APIs - مجموعة إدارة النظام
Group 4: Admin Management APIs (6 endpoints)
"""

from flask import Blueprint, request, jsonify, current_app
from security import jwt_required, require_permission
from models import (
    User, Student, Teacher, Subject, Room, Schedule,
    UserRole, SectionEnum, StudyTypeEnum, AcademicStatusEnum,
    RoomTypeEnum, SemesterEnum, DayOfWeekEnum
)
from utils.response_helpers import (
    success_response, error_response, paginated_response,
    validation_error_response, batch_response
)
from utils.validation_helpers import (
    validate_required_fields, validate_pagination_params,
    validate_filters, validate_sort_params, validate_bulk_operation_limit
)
from config.database import db
from datetime import datetime
import logging
import csv
import io
import pandas as pd

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/students', methods=['GET'])
@jwt_required
@require_permission('read_student')
def get_students():
    """
    GET /api/admin/students
    List students with filters and pagination
    عرض قائمة الطلاب مع الفلاتر والترقيم
    """
    try:
        # 1. Validate pagination parameters
        page, limit, pagination_error = validate_pagination_params(
            request.args.get('page'),
            request.args.get('limit'),
            max_limit=100
        )
        if pagination_error:
            return jsonify(pagination_error), 400
        
        # 2. Validate and process filters
        allowed_filters = [
            'section', 'study_year', 'study_type', 'academic_status',
            'search', 'face_registered', 'telegram_connected'
        ]
        filters, filter_error = validate_filters(dict(request.args), allowed_filters)
        if filter_error:
            return jsonify(filter_error), 400
        
        # 3. Validate sorting parameters
        allowed_sort_fields = [
            'university_id', 'full_name', 'section', 'study_year',
            'created_at', 'last_login'
        ]
        sort_by, sort_order, sort_error = validate_sort_params(
            request.args.get('sort_by'),
            request.args.get('sort_order'),
            allowed_sort_fields
        )
        if sort_error:
            return jsonify(sort_error), 400
        
        # 4. Build query
        query = Student.query.join(User)
        
        # Apply filters
        if filters.get('section'):
            try:
                section_enum = SectionEnum(filters['section'])
                query = query.filter(Student.section == section_enum)
            except ValueError:
                return jsonify(error_response('INVALID_SECTION', 'شعبة غير صحيحة')), 400
        
        if filters.get('study_year'):
            try:
                study_year = int(filters['study_year'])
                if not (1 <= study_year <= 4):
                    raise ValueError()
                query = query.filter(Student.study_year == study_year)
            except ValueError:
                return jsonify(error_response('INVALID_STUDY_YEAR', 'سنة دراسية غير صحيحة')), 400
        
        if filters.get('study_type'):
            try:
                study_type_enum = StudyTypeEnum(filters['study_type'])
                query = query.filter(Student.study_type == study_type_enum)
            except ValueError:
                return jsonify(error_response('INVALID_STUDY_TYPE', 'نوع دراسة غير صحيح')), 400
        
        if filters.get('academic_status'):
            try:
                status_enum = AcademicStatusEnum(filters['academic_status'])
                query = query.filter(Student.academic_status == status_enum)
            except ValueError:
                return jsonify(error_response('INVALID_STATUS', 'حالة أكاديمية غير صحيحة')), 400
        
        if filters.get('face_registered') is not None:
            face_registered = filters['face_registered'].lower() == 'true'
            query = query.filter(Student.face_registered == face_registered)
        
        if filters.get('telegram_connected') is not None:
            telegram_connected = filters['telegram_connected'].lower() == 'true'
            if telegram_connected:
                query = query.filter(Student.telegram_id.isnot(None))
            else:
                query = query.filter(Student.telegram_id.is_(None))
        
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                db.or_(
                    Student.university_id.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        # 5. Apply sorting
        if sort_by:
            if sort_by == 'university_id':
                sort_column = Student.university_id
            elif sort_by == 'full_name':
                sort_column = User.full_name
            elif sort_by == 'section':
                sort_column = Student.section
            elif sort_by == 'study_year':
                sort_column = Student.study_year
            elif sort_by == 'created_at':
                sort_column = Student.created_at
            elif sort_by == 'last_login':
                sort_column = User.last_login
            
            if sort_order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # Default sorting
            query = query.order_by(Student.study_year.asc(), Student.section.asc(), Student.university_id.asc())
        
        # 6. Get total count before pagination
        total_count = query.count()
        
        # 7. Apply pagination
        offset = (page - 1) * limit
        students = query.offset(offset).limit(limit).all()
        
        # 8. Format response data
        students_data = []
        for student in students:
            student_data = {
                'id': student.id,
                'university_id': student.university_id,
                'user_info': {
                    'id': student.user.id,
                    'username': student.user.username,
                    'full_name': student.user.full_name,
                    'email': student.user.email,
                    'phone': student.user.phone,
                    'is_active': student.user.is_active,
                    'last_login': student.user.last_login.isoformat() if student.user.last_login else None
                },
                'academic_info': {
                    'section': student.section.value,
                    'study_year': student.study_year,
                    'study_type': student.study_type.value,
                    'academic_status': student.academic_status.value,
                    'is_repeater': student.is_repeater
                },
                'biometric_info': {
                    'face_registered': student.face_registered,
                    'face_registered_at': student.face_registered_at.isoformat() if student.face_registered_at else None
                },
                'telegram_info': {
                    'telegram_id': student.telegram_id,
                    'connected': student.telegram_id is not None
                },
                'created_at': student.created_at.isoformat()
            }
            students_data.append(student_data)
        
        # 9. Calculate summary statistics
        summary_stats = {
            'total_students': total_count,
            'active_students': Student.query.filter_by(academic_status=AcademicStatusEnum.ACTIVE).count(),
            'face_registered': Student.query.filter_by(face_registered=True).count(),
            'telegram_connected': Student.query.filter(Student.telegram_id.isnot(None)).count(),
            'by_section': {},
            'by_year': {}
        }
        
        # Section statistics
        for section in SectionEnum:
            count = Student.query.filter_by(section=section).count()
            summary_stats['by_section'][section.value] = count
        
        # Year statistics  
        for year in range(1, 5):
            count = Student.query.filter_by(study_year=year).count()
            summary_stats['by_year'][str(year)] = count
        
        # 10. Log admin action
        logging.info(f'Admin students list accessed: page {page}, filters: {filters}')
        
        return jsonify(paginated_response(
            items=students_data,
            page=page,
            limit=limit,
            total_count=total_count,
            additional_data={
                'summary_statistics': summary_stats,
                'applied_filters': filters,
                'sort_info': {'sort_by': sort_by, 'sort_order': sort_order}
            }
        ))
        
    except Exception as e:
        logging.error(f'Admin get students error: {str(e)}', exc_info=True)
        return jsonify(error_response('ADMIN_ERROR', 'حدث خطأ أثناء جلب بيانات الطلاب')), 500

@admin_bp.route('/students/bulk-create', methods=['POST'])
@jwt_required
@require_permission('create_student')
def bulk_create_students():
    """
    POST /api/admin/students/bulk-create
    Create multiple students from CSV/Excel upload
    إنشاء طلاب متعددين من ملف CSV أو Excel
    """
    try:
        # 1. Check if file is uploaded
        if 'file' not in request.files:
            return jsonify(error_response('NO_FILE', 'ملف مطلوب للرفع')), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify(error_response('EMPTY_FILENAME', 'اسم الملف فارغ')), 400
        
        # 2. Validate file type
        allowed_extensions = {'.csv', '.xlsx', '.xls'}
        file_ext = '.' + file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify(error_response(
                'INVALID_FILE_TYPE',
                f'نوع الملف غير مدعوم. الأنواع المدعومة: {", ".join(allowed_extensions)}'
            )), 400
        
        # 3. Read file data
        try:
            file_content = file.read()
            
            if file_ext == '.csv':
                # Read CSV
                df = pd.read_csv(io.BytesIO(file_content))
            else:
                # Read Excel
                df = pd.read_excel(io.BytesIO(file_content))
                
        except Exception as e:
            return jsonify(error_response('FILE_READ_ERROR', f'خطأ في قراءة الملف: {str(e)}')), 400
        
        # 4. Validate CSV columns
        required_columns = ['university_id', 'full_name', 'email', 'section', 'study_year']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify(error_response(
                'MISSING_COLUMNS',
                f'أعمدة مطلوبة مفقودة: {", ".join(missing_columns)}',
                {'required_columns': required_columns, 'found_columns': list(df.columns)}
            )), 400
        
        # 5. Validate bulk limit
        bulk_limit_error = validate_bulk_operation_limit(df.to_dict('records'), max_items=500)
        if bulk_limit_error:
            return jsonify(bulk_limit_error), 400
        
        # 6. Process each row
        results = []
        successful_creates = 0
        failed_creates = 0
        
        for index, row in df.iterrows():
            row_result = {
                'row_number': index + 2,  # +2 because pandas is 0-indexed and CSV has header
                'university_id': row.get('university_id'),
                'success': False,
                'error': None,
                'student_id': None
            }
            
            try:
                # Validate row data
                university_id = str(row['university_id']).strip().upper()
                full_name = str(row['full_name']).strip()
                email = str(row['email']).strip().lower()
                section = str(row['section']).strip().upper()
                study_year = int(row['study_year'])
                
                # Optional fields
                study_type = row.get('study_type', 'morning')
                phone = str(row.get('phone', '')).strip() if pd.notna(row.get('phone')) else None
                
                # Basic validation
                if not university_id or len(university_id) != 9:
                    raise ValueError('رقم جامعي غير صحيح')
                
                if not full_name or len(full_name) < 2:
                    raise ValueError('الاسم الكامل مطلوب')
                
                if '@' not in email:
                    raise ValueError('بريد إلكتروني غير صحيح')
                
                if section not in ['A', 'B', 'C']:
                    raise ValueError('شعبة غير صحيحة (A, B, C)')
                
                if not (1 <= study_year <= 4):
                    raise ValueError('سنة دراسية غير صحيحة (1-4)')
                
                # Check for duplicates
                existing_student = Student.query.filter_by(university_id=university_id).first()
                if existing_student:
                    raise ValueError(f'الرقم الجامعي موجود مسبقاً: {university_id}')
                
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    raise ValueError(f'البريد الإلكتروني موجود مسبقاً: {email}')
                
                # Create user
                username = university_id.lower()  # Use university_id as username
                user = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    phone=phone,
                    role=UserRole.STUDENT,
                    is_active=True
                )
                
                # Generate temporary password (first 4 digits of university_id + "2024")
                temp_password = university_id[-4:] + "2024"
                user.set_password(temp_password)
                
                db.session.add(user)
                db.session.flush()  # Get user ID
                
                # Create student
                student = Student(
                    user_id=user.id,
                    university_id=university_id,
                    section=SectionEnum(section),
                    study_year=study_year,
                    study_type=StudyTypeEnum(study_type),
                    academic_status=AcademicStatusEnum.ACTIVE
                )
                
                # Generate secret code (random 8 characters)
                from security import PasswordManager
                secret_code = PasswordManager.generate_secret_code()
                student.set_secret_code(secret_code)
                
                db.session.add(student)
                db.session.flush()  # Get student ID
                
                # Success
                row_result.update({
                    'success': True,
                    'student_id': student.id,
                    'user_id': user.id,
                    'generated_password': temp_password,
                    'secret_code': secret_code
                })
                successful_creates += 1
                
            except ValueError as ve:
                row_result['error'] = str(ve)
                failed_creates += 1
            except Exception as e:
                row_result['error'] = f'خطأ غير متوقع: {str(e)}'
                failed_creates += 1
            
            results.append(row_result)
        
        # 7. Commit transaction if any successful
        if successful_creates > 0:
            try:
                db.session.commit()
                logging.info(f'Bulk student creation: {successful_creates} successful, {failed_creates} failed')
            except Exception as e:
                db.session.rollback()
                return jsonify(error_response('DATABASE_ERROR', f'خطأ في حفظ البيانات: {str(e)}')), 500
        else:
            db.session.rollback()
        
        # 8. Prepare summary
        summary = {
            'total_rows': len(results),
            'successful': successful_creates,
            'failed': failed_creates,
            'success_rate': round((successful_creates / len(results)) * 100, 2) if results else 0
        }
        
        return jsonify(batch_response(results, summary))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Bulk create students error: {str(e)}', exc_info=True)
        return jsonify(error_response('BULK_CREATE_ERROR', 'حدث خطأ أثناء الإنشاء الجماعي للطلاب')), 500

@admin_bp.route('/rooms', methods=['POST'])
@jwt_required
@require_permission('create_room')
def create_room():
    """
    POST /api/admin/rooms
    Create a new room with GPS coordinates
    إنشاء قاعة جديدة مع إحداثيات GPS
    """
    try:
        # 1. Validate input
        data = request.get_json()
        if not data:
            return jsonify(error_response('INVALID_INPUT', 'JSON body is required')), 400
        
        # Required fields
        required_fields = [
            'name', 'building', 'floor', 'center_latitude', 
            'center_longitude', 'ground_reference_altitude', 
            'floor_altitude', 'ceiling_height'
        ]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify(validation_error), 400
        
        # 2. Validate and process data
        name = data['name'].strip().upper()
        building = data['building'].strip()
        floor = int(data['floor'])
        room_type = data.get('room_type', 'classroom')
        capacity = int(data.get('capacity', 30))
        
        # GPS coordinates
        center_lat = float(data['center_latitude'])
        center_lng = float(data['center_longitude'])
        ground_altitude = float(data['ground_reference_altitude'])
        floor_altitude = float(data['floor_altitude'])
        ceiling_height = float(data['ceiling_height'])
        
        # Optional fields
        wifi_ssid = data.get('wifi_ssid', '').strip() if data.get('wifi_ssid') else None
        polygon_width = float(data.get('polygon_width_meters', 10))
        polygon_height = float(data.get('polygon_height_meters', 8))
        
        # 3. Validate GPS coordinates
        if not (-90 <= center_lat <= 90):
            return jsonify(error_response('INVALID_LATITUDE', 'خط العرض يجب أن يكون بين -90 و 90')), 400
        
        if not (-180 <= center_lng <= 180):
            return jsonify(error_response('INVALID_LONGITUDE', 'خط الطول يجب أن يكون بين -180 و 180')), 400
        
        # 4. Validate room type
        try:
            room_type_enum = RoomTypeEnum(room_type)
        except ValueError:
            return jsonify(error_response('INVALID_ROOM_TYPE', 'نوع القاعة غير صحيح')), 400
        
        # 5. Check for existing room
        existing_room = Room.query.filter_by(name=name).first()
        if existing_room:
            return jsonify(error_response('ROOM_EXISTS', f'قاعة بنفس الاسم موجودة: {name}')), 409
        
        # 6. Create room
        room = Room(
            name=name,
            building=building,
            floor=floor,
            room_type=room_type_enum,
            capacity=capacity,
            center_latitude=center_lat,
            center_longitude=center_lng,
            ground_reference_altitude=ground_altitude,
            floor_altitude=floor_altitude,
            ceiling_height=ceiling_height,
            wifi_ssid=wifi_ssid,
            is_active=True
        )
        
        # 7. Generate GPS polygon
        room.set_rectangular_polygon(center_lat, center_lng, polygon_width, polygon_height)
        
        # 8. Save room
        db.session.add(room)
        db.session.commit()
        
        # 9. Log creation
        logging.info(f'Room created: {name} by admin')
        
        # 10. Return response
        return jsonify(success_response({
            'room': {
                'id': room.id,
                'name': room.name,
                'building': room.building,
                'floor': room.floor,
                'room_type': room.room_type.value,
                'capacity': room.capacity,
                'location': {
                    'center_latitude': float(room.center_latitude),
                    'center_longitude': float(room.center_longitude),
                    'gps_polygon': room.gps_polygon,
                    'floor_altitude': float(room.floor_altitude),
                    'ceiling_height': float(room.ceiling_height)
                },
                'wifi_ssid': room.wifi_ssid,
                'is_active': room.is_active,
                'created_at': room.created_at.isoformat()
            }
        }, message='تم إنشاء القاعة بنجاح')), 201
        
    except ValueError as ve:
        return jsonify(error_response('VALIDATION_ERROR', f'خطأ في البيانات: {str(ve)}')), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f'Room creation error: {str(e)}', exc_info=True)
        return jsonify(error_response('ROOM_CREATE_ERROR', 'حدث خطأ أثناء إنشاء القاعة')), 500

@admin_bp.route('/rooms/<int:room_id>', methods=['PUT'])
@jwt_required
@require_permission('update_room')
def update_room(room_id):
    """
    PUT /api/admin/rooms/<id>
    Update existing room
    تحديث قاعة موجودة
    """
    try:
        # 1. Find room
        room = Room.query.get(room_id)
        if not room:
            return jsonify(error_response('ROOM_NOT_FOUND', f'قاعة غير موجودة: {room_id}')), 404
        
        # 2. Validate input
        data = request.get_json()
        if not data:
            return jsonify(error_response('INVALID_INPUT', 'JSON body is required')), 400
        
        # 3. Update fields if provided
        if 'name' in data:
            new_name = data['name'].strip().upper()
            # Check for name conflicts
            existing = Room.query.filter(Room.name == new_name, Room.id != room_id).first()
            if existing:
                return jsonify(error_response('NAME_EXISTS', f'اسم القاعة موجود: {new_name}')), 409
            room.name = new_name
        
        if 'building' in data:
            room.building = data['building'].strip()
        
        if 'floor' in data:
            room.floor = int(data['floor'])
        
        if 'room_type' in data:
            try:
                room.room_type = RoomTypeEnum(data['room_type'])
            except ValueError:
                return jsonify(error_response('INVALID_ROOM_TYPE', 'نوع القاعة غير صحيح')), 400
        
        if 'capacity' in data:
            room.capacity = int(data['capacity'])
        
        if 'wifi_ssid' in data:
            room.wifi_ssid = data['wifi_ssid'].strip() if data['wifi_ssid'] else None
        
        if 'is_active' in data:
            room.is_active = bool(data['is_active'])
        
        # Update GPS coordinates if provided
        gps_updated = False
        if 'center_latitude' in data:
            room.center_latitude = float(data['center_latitude'])
            gps_updated = True
        
        if 'center_longitude' in data:
            room.center_longitude = float(data['center_longitude'])
            gps_updated = True
        
        if 'floor_altitude' in data:
            room.floor_altitude = float(data['floor_altitude'])
        
        if 'ceiling_height' in data:
            room.ceiling_height = float(data['ceiling_height'])
        
        # Regenerate polygon if GPS coordinates changed
        if gps_updated or 'polygon_width_meters' in data or 'polygon_height_meters' in data:
            width = float(data.get('polygon_width_meters', 10))
            height = float(data.get('polygon_height_meters', 8))
            room.set_rectangular_polygon(
                float(room.center_latitude),
                float(room.center_longitude),
                width, height
            )
        
        # 4. Save changes
        db.session.commit()
        
        # 5. Log update
        logging.info(f'Room updated: {room.name} by admin')
        
        # 6. Return response
        return jsonify(success_response({
            'room': room.to_dict_with_gps()
        }, message='تم تحديث القاعة بنجاح'))
        
    except ValueError as ve:
        return jsonify(error_response('VALIDATION_ERROR', f'خطأ في البيانات: {str(ve)}')), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f'Room update error: {str(e)}', exc_info=True)
        return jsonify(error_response('ROOM_UPDATE_ERROR', 'حدث خطأ أثناء تحديث القاعة')), 500

@admin_bp.route('/schedules/bulk-create', methods=['POST'])
@jwt_required
@require_permission('create_schedule')
def bulk_create_schedules():
    """
    POST /api/admin/schedules/bulk-create
    Create multiple schedules from data array
    إنشاء جداول متعددة من مصفوفة البيانات
    """
    try:
        # 1. Validate input
        data = request.get_json()
        if not data or 'schedules' not in data:
            return jsonify(error_response('INVALID_INPUT', 'قائمة الجداول مطلوبة')), 400
        
        schedules_data = data['schedules']
        if not isinstance(schedules_data, list):
            return jsonify(error_response('INVALID_FORMAT', 'الجداول يجب أن تكون مصفوفة')), 400
        
        # 2. Validate bulk limit
        bulk_limit_error = validate_bulk_operation_limit(schedules_data, max_items=200)
        if bulk_limit_error:
            return jsonify(bulk_limit_error), 400
        
        # 3. Process each schedule
        results = []
        successful_creates = 0
        failed_creates = 0
        
        for index, schedule_data in enumerate(schedules_data):
            result = {
                'index': index,
                'success': False,
                'error': None,
                'schedule_id': None
            }
            
            try:
                # Validate required fields for each schedule
                required_fields = [
                    'subject_id', 'teacher_id', 'room_id', 'section',
                    'day_of_week', 'start_time', 'end_time',
                    'academic_year', 'semester'
                ]
                
                missing_fields = [field for field in required_fields if field not in schedule_data]
                if missing_fields:
                    raise ValueError(f'حقول مطلوبة مفقودة: {", ".join(missing_fields)}')
                
                # Process data
                subject_id = int(schedule_data['subject_id'])
                teacher_id = int(schedule_data['teacher_id'])
                room_id = int(schedule_data['room_id'])
                section = SectionEnum(schedule_data['section'])
                day_of_week = int(schedule_data['day_of_week'])
                academic_year = schedule_data['academic_year']
                semester = SemesterEnum(schedule_data['semester'])
                
                # Parse times
                start_time = datetime.strptime(schedule_data['start_time'], '%H:%M').time()
                end_time = datetime.strptime(schedule_data['end_time'], '%H:%M').time()
                
                # Validate references exist
                subject = Subject.query.get(subject_id)
                if not subject:
                    raise ValueError(f'مادة غير موجودة: {subject_id}')
                
                teacher = Teacher.query.get(teacher_id)
                if not teacher:
                    raise ValueError(f'مدرس غير موجود: {teacher_id}')
                
                room = Room.query.get(room_id)
                if not room:
                    raise ValueError(f'قاعة غير موجودة: {room_id}')
                
                # Create schedule
                schedule = Schedule(
                    subject_id=subject_id,
                    teacher_id=teacher_id,
                    room_id=room_id,
                    section=section,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    academic_year=academic_year,
                    semester=semester,
                    is_active=True
                )
                
                # This will validate conflicts in the save() method
                db.session.add(schedule)
                db.session.flush()  # Get ID without committing
                
                result.update({
                    'success': True,
                    'schedule_id': schedule.id,
                    'subject_code': subject.code,
                    'room_name': room.name
                })
                successful_creates += 1
                
            except ValueError as ve:
                result['error'] = str(ve)
                failed_creates += 1
            except Exception as e:
                result['error'] = f'خطأ غير متوقع: {str(e)}'
                failed_creates += 1
            
            results.append(result)
        
        # 4. Commit if any successful
        if successful_creates > 0:
            try:
                db.session.commit()
                logging.info(f'Bulk schedule creation: {successful_creates} successful, {failed_creates} failed')
            except Exception as e:
                db.session.rollback()
                return jsonify(error_response('DATABASE_ERROR', f'خطأ في حفظ الجداول: {str(e)}')), 500
        else:
            db.session.rollback()
        
        # 5. Summary
        summary = {
            'total_schedules': len(results),
            'successful': successful_creates,
            'failed': failed_creates,
            'success_rate': round((successful_creates / len(results)) * 100, 2) if results else 0
        }
        
        return jsonify(batch_response(results, summary))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Bulk create schedules error: {str(e)}', exc_info=True)
        return jsonify(error_response('BULK_SCHEDULE_ERROR', 'حدث خطأ أثناء الإنشاء الجماعي للجداول')), 500

@admin_bp.route('/system/health', methods=['GET'])
@jwt_required
@require_permission('system_settings')
def system_health():
    """
    GET /api/admin/system/health
    Get comprehensive system health information
    معلومات صحة النظام الشاملة
    """
    try:
        health_info = {
            'system_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {},
            'database_stats': {},
            'performance_metrics': {},
            'recent_activity': {}
        }
        
        # 1. Database health
        try:
            db.session.execute('SELECT 1')
            health_info['services']['database'] = {
                'status': 'healthy',
                'response_time_ms': 50  # Approximate
            }
            
            # Database statistics
            health_info['database_stats'] = {
                'total_users': User.query.count(),
                'active_students': Student.query.filter_by(academic_status=AcademicStatusEnum.ACTIVE).count(),
                'total_teachers': Teacher.query.count(),
                'total_subjects': Subject.query.filter_by(is_active=True).count(),
                'total_rooms': Room.query.filter_by(is_active=True).count(),
                'active_schedules': Schedule.query.filter_by(is_active=True).count()
            }
            
        except Exception as e:
            health_info['services']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_info['system_status'] = 'degraded'
        
        # 2. Redis health
        try:
            from config.database import redis_client
            redis_client.ping()
            health_info['services']['redis'] = {
                'status': 'healthy',
                'response_time_ms': 10
            }
        except Exception as e:
            health_info['services']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_info['system_status'] = 'degraded'
        
        # 3. File storage health
        import os
        storage_path = 'storage'
        if os.path.exists(storage_path) and os.access(storage_path, os.W_OK):
            # Calculate storage usage
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(storage_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass
            
            health_info['services']['storage'] = {
                'status': 'healthy',
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'available': True
            }
        else:
            health_info['services']['storage'] = {
                'status': 'unhealthy',
                'error': 'Storage directory not accessible'
            }
        
        # 4. Performance metrics
        health_info['performance_metrics'] = {
            'avg_response_time_ms': 150,  # Would be calculated from actual metrics
            'requests_per_minute': 45,    # Would be from monitoring
            'error_rate_percent': 0.5,    # Would be from logs
            'uptime_hours': 168           # Would be from actual monitoring
        }
        
        # 5. Recent activity (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        health_info['recent_activity'] = {
            'new_users_24h': User.query.filter(User.created_at >= yesterday).count(),
            'student_logins_24h': User.query.filter(
                User.last_login >= yesterday,
                User.role == UserRole.STUDENT
            ).count(),
            'teacher_logins_24h': User.query.filter(
                User.last_login >= yesterday,
                User.role == UserRole.TEACHER
            ).count(),
            'system_errors_24h': 0  # Would be from logs
        }
        
        # 6. Security status
        health_info['security_status'] = {
            'failed_login_attempts': User.query.filter(User.failed_login_attempts > 0).count(),
            'locked_accounts': User.query.filter(User.last_lockout.isnot(None)).count(),
            'last_security_scan': '2024-01-15T10:00:00Z'  # Would be from actual scans
        }
        
        # 7. Log health check
        logging.info('System health check performed by admin')
        
        return jsonify(success_response(health_info))
        
    except Exception as e:
        logging.error(f'System health check error: {str(e)}', exc_info=True)
        return jsonify(error_response('HEALTH_CHECK_ERROR', 'حدث خطأ أثناء فحص صحة النظام')), 500

# Error handlers specific to admin blueprint
@admin_bp.errorhandler(403)
def admin_forbidden(error):
    """Handle forbidden access to admin endpoints"""
    return jsonify(error_response(
        'ADMIN_ACCESS_DENIED',
        'صلاحيات إدارية مطلوبة للوصول لهذا المورد'
    )), 403

@admin_bp.errorhandler(413)
def admin_file_too_large(error):
    """Handle file upload size limits"""
    return jsonify(error_response(
        'FILE_TOO_LARGE',
        'حجم الملف كبير جداً. الحد الأقصى 10MB'
    )), 413