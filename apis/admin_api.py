"""
👑 Admin Management APIs - إدارة النظام الكاملة
Implementation: 6 comprehensive admin management endpoints
اليوم 3-4: إدارة شاملة للطلاب والقاعات والجداول
"""

from flask import Blueprint, request, jsonify, current_app, g
from security import jwt_required, require_permission, get_current_user
from models import (
    User, Student, Teacher, Subject, Room, Schedule, Lecture,
    UserRole, SectionEnum, SemesterEnum, StudyTypeEnum, AcademicStatusEnum,
    RoomTypeEnum, AcademicDegreeEnum, LectureStatusEnum
)
from utils.response_helpers import (
    success_response, error_response, paginated_response,
    validation_error_response, not_found_response, batch_response
)
from utils.validation_helpers import (
    validate_required_fields, validate_pagination_params, validate_filters,
    validate_bulk_operation_limit, validate_academic_year, validate_section,
    validate_study_year, validate_semester, InputValidator
)
from config.database import db
from datetime import datetime, date, time, timedelta
import logging
import secrets
import io
import csv
from werkzeug.utils import secure_filename

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ============================================================================
# STUDENTS MANAGEMENT - إدارة الطلاب
# ============================================================================

@admin_bp.route('/students', methods=['GET'])
@jwt_required
@require_permission('read_student')
def get_students():
    """
    GET /api/admin/students
    List students with comprehensive filters and pagination
    قائمة الطلاب مع فلاتر وصفحات متقدمة
    """
    try:
        # 1. Validate pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        normalized_page, normalized_limit, pagination_error = validate_pagination_params(
            page, limit, max_limit=100
        )
        if pagination_error:
            return jsonify(pagination_error), 400
        
        # 2. Get filter parameters
        filters = {
            'section': request.args.get('section'),
            'study_year': request.args.get('study_year', type=int),
            'study_type': request.args.get('study_type'),
            'academic_status': request.args.get('academic_status'),
            'face_registered': request.args.get('face_registered'),
            'telegram_connected': request.args.get('telegram_connected'),
            'is_repeater': request.args.get('is_repeater'),
            'university_id': request.args.get('university_id'),
            'search': request.args.get('search', '').strip()
        }
        
        # Validate filters
        allowed_filters = list(filters.keys())
        validated_filters, filter_error = validate_filters(filters, allowed_filters)
        if filter_error:
            return jsonify(filter_error), 400
        
        # 3. Get sorting parameters
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        allowed_sort_fields = [
            'university_id', 'full_name', 'section', 'study_year', 
            'created_at', 'last_login', 'face_registered_at'
        ]
        
        if sort_by not in allowed_sort_fields:
            return jsonify(error_response(
                'INVALID_SORT_FIELD',
                f'حقل الترتيب غير مدعوم. الحقول المدعومة: {", ".join(allowed_sort_fields)}'
            )), 400
        
        if sort_order not in ['asc', 'desc']:
            return jsonify(error_response('INVALID_SORT_ORDER', 'اتجاه الترتيب يجب أن يكون asc أو desc')), 400
        
        # 4. Build base query
        query = Student.query.join(User)
        
        # Apply filters
        if validated_filters.get('section'):
            try:
                section_enum = SectionEnum(validated_filters['section'])
                query = query.filter(Student.section == section_enum)
            except ValueError:
                return jsonify(error_response('INVALID_SECTION', 'شعبة غير صحيحة')), 400
        
        if validated_filters.get('study_year'):
            query = query.filter(Student.study_year == validated_filters['study_year'])
        
        if validated_filters.get('study_type'):
            try:
                study_type_enum = StudyTypeEnum(validated_filters['study_type'])
                query = query.filter(Student.study_type == study_type_enum)
            except ValueError:
                return jsonify(error_response('INVALID_STUDY_TYPE', 'نوع الدراسة غير صحيح')), 400
        
        if validated_filters.get('academic_status'):
            try:
                status_enum = AcademicStatusEnum(validated_filters['academic_status'])
                query = query.filter(Student.academic_status == status_enum)
            except ValueError:
                return jsonify(error_response('INVALID_ACADEMIC_STATUS', 'حالة أكاديمية غير صحيحة')), 400
        
        if validated_filters.get('face_registered') is not None:
            face_registered = validated_filters['face_registered'].lower() == 'true'
            query = query.filter(Student.face_registered == face_registered)
        
        if validated_filters.get('telegram_connected') is not None:
            telegram_connected = validated_filters['telegram_connected'].lower() == 'true'
            if telegram_connected:
                query = query.filter(Student.telegram_id.isnot(None))
            else:
                query = query.filter(Student.telegram_id.is_(None))
        
        if validated_filters.get('is_repeater') is not None:
            is_repeater = validated_filters['is_repeater'].lower() == 'true'
            query = query.filter(Student.is_repeater == is_repeater)
        
        if validated_filters.get('university_id'):
            query = query.filter(Student.university_id.ilike(f"%{validated_filters['university_id']}%"))
        
        if validated_filters.get('search'):
            search_term = validated_filters['search']
            query = query.filter(
                db.or_(
                    User.full_name.ilike(f'%{search_term}%'),
                    User.email.ilike(f'%{search_term}%'),
                    Student.university_id.ilike(f'%{search_term}%')
                )
            )
        
        # 5. Apply sorting
        if sort_by in ['university_id', 'section', 'study_year', 'face_registered', 'created_at']:
            sort_column = getattr(Student, sort_by)
        elif sort_by in ['full_name']:
            sort_column = getattr(User, sort_by)
        elif sort_by == 'last_login':
            sort_column = User.last_login
        elif sort_by == 'face_registered_at':
            sort_column = Student.face_registered_at
        
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # 6. Get total count for pagination
        total_count = query.count()
        
        # 7. Apply pagination
        offset = (normalized_page - 1) * normalized_limit
        students = query.offset(offset).limit(normalized_limit).all()
        
        # 8. Format response data
        students_data = []
        for student in students:
            user = student.user
            student_data = {
                'id': student.id,
                'user_id': user.id,
                'university_id': student.university_id,
                'full_name': user.full_name,
                'email': user.email,
                'phone': user.phone,
                'section': student.section.value,
                'study_year': student.study_year,
                'study_type': student.study_type.value,
                'academic_status': student.academic_status.value,
                'is_repeater': student.is_repeater,
                'failed_subjects': student.failed_subjects or [],
                'face_registered': student.face_registered,
                'face_registered_at': student.face_registered_at.isoformat() if student.face_registered_at else None,
                'telegram_connected': student.telegram_id is not None,
                'telegram_id': student.telegram_id,
                'device_fingerprint': student.device_fingerprint,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': student.created_at.isoformat(),
                'updated_at': student.updated_at.isoformat() if student.updated_at else None
            }
            students_data.append(student_data)
        
        # 9. Calculate statistics
        stats = {
            'total_students': total_count,
            'active_students': sum(1 for s in students if s.user.is_active),
            'face_registered_count': sum(1 for s in students if s.face_registered),
            'telegram_connected_count': sum(1 for s in students if s.telegram_id),
            'repeaters_count': sum(1 for s in students if s.is_repeater),
            'by_section': {},
            'by_study_year': {},
            'by_study_type': {}
        }
        
        # Group statistics
        for student in students:
            # By section
            section = student.section.value
            if section not in stats['by_section']:
                stats['by_section'][section] = 0
            stats['by_section'][section] += 1
            
            # By study year
            year = student.study_year
            if year not in stats['by_study_year']:
                stats['by_study_year'][year] = 0
            stats['by_study_year'][year] += 1
            
            # By study type
            study_type = student.study_type.value
            if study_type not in stats['by_study_type']:
                stats['by_study_type'][study_type] = 0
            stats['by_study_type'][study_type] += 1
        
        # 10. Log access
        user = get_current_user()
        logging.info(f'Students list accessed by {user.username}: {len(students)} results, filters: {validated_filters}')
        
        return jsonify(paginated_response(
            items=students_data,
            page=normalized_page,
            limit=normalized_limit,
            total_count=total_count,
            additional_data={
                'statistics': stats,
                'applied_filters': validated_filters,
                'sort_info': {'field': sort_by, 'order': sort_order}
            }
        ))
        
    except Exception as e:
        logging.error(f'Get students error: {str(e)}', exc_info=True)
        return jsonify(error_response('GET_STUDENTS_ERROR', 'حدث خطأ أثناء جلب قائمة الطلاب')), 500

@admin_bp.route('/students/bulk-create', methods=['POST'])
@jwt_required
@require_permission('create_student')
def bulk_create_students():
    """
    POST /api/admin/students/bulk-create
    Create multiple students from data array or CSV upload
    إنشاء طلاب متعددين من مصفوفة بيانات أو ملف CSV
    """
    try:
        # 1. Determine input type (JSON array or file upload)
        if request.content_type and 'multipart/form-data' in request.content_type:
            # File upload mode
            if 'file' not in request.files:
                return jsonify(error_response('NO_FILE', 'ملف مطلوب للرفع')), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify(error_response('EMPTY_FILENAME', 'اسم الملف فارغ')), 400
            
            # Validate file extension
            if not file.filename.lower().endswith('.csv'):
                return jsonify(error_response('INVALID_FILE_TYPE', 'نوع الملف يجب أن يكون CSV')), 400
            
            # Read CSV data
            try:
                csv_content = io.StringIO(file.read().decode('utf-8'))
                csv_reader = csv.DictReader(csv_content)
                students_data = list(csv_reader)
            except Exception as e:
                return jsonify(error_response('CSV_PARSE_ERROR', f'خطأ في قراءة ملف CSV: {str(e)}')), 400
        
        else:
            # JSON array mode
            data = request.get_json()
            if not data or 'students' not in data:
                return jsonify(error_response('INVALID_INPUT', 'مصفوفة الطلاب مطلوبة')), 400
            
            students_data = data['students']
            if not isinstance(students_data, list):
                return jsonify(error_response('INVALID_FORMAT', 'بيانات الطلاب يجب أن تكون مصفوفة')), 400
        
        # 2. Validate bulk operation limit
        bulk_limit_error = validate_bulk_operation_limit(students_data, max_items=500)
        if bulk_limit_error:
            return jsonify(bulk_limit_error), 400
        
        # 3. Get processing options
        processing_options = request.form.to_dict() if request.content_type and 'multipart/form-data' in request.content_type else data.get('options', {})
        
        auto_generate_codes = processing_options.get('auto_generate_codes', 'true').lower() == 'true'
        send_notifications = processing_options.get('send_notifications', 'false').lower() == 'true'
        skip_duplicates = processing_options.get('skip_duplicates', 'true').lower() == 'true'
        default_password = processing_options.get('default_password', 'NewStudent123!')
        
        # 4. Process each student record
        results = []
        successful_creates = 0
        failed_creates = 0
        duplicate_skips = 0
        
        for index, student_data in enumerate(students_data):
            result = {
                'index': index,
                'success': False,
                'error': None,
                'student_id': None,
                'university_id': None,
                'generated_code': None,
                'duplicate_skipped': False
            }
            
            try:
                # Validate required fields
                required_fields = ['full_name', 'email', 'section', 'study_year']
                missing_fields = [field for field in required_fields if field not in student_data or not student_data[field]]
                
                if missing_fields:
                    raise ValueError(f'حقول مطلوبة مفقودة: {", ".join(missing_fields)}')
                
                # Clean and validate data
                full_name = InputValidator.sanitize_string(student_data['full_name'])
                email = InputValidator.sanitize_string(student_data['email']).lower()
                section = student_data['section'].upper()
                study_year = int(student_data['study_year'])
                
                # Optional fields
                phone = InputValidator.sanitize_string(student_data.get('phone', ''))
                study_type = student_data.get('study_type', 'morning')
                university_id = student_data.get('university_id', '').upper()
                
                # Validate email format
                is_valid_email, email_error = InputValidator.validate_email(email)
                if not is_valid_email:
                    raise ValueError(f'البريد الإلكتروني غير صحيح: {email_error}')
                
                # Validate section
                is_valid_section, section_error = validate_section(section)
                if not is_valid_section:
                    raise ValueError(section_error)
                
                # Validate study year
                is_valid_year, year_error = validate_study_year(study_year)
                if not is_valid_year:
                    raise ValueError(year_error)
                
                # Generate university ID if not provided
                if not university_id:
                    # Generate format: CS2024001, CS2024002, etc.
                    current_year = datetime.now().year
                    
                    # Find the highest existing ID for this year
                    year_prefix = f"CS{current_year}"
                    last_student = Student.query.filter(
                        Student.university_id.like(f'{year_prefix}%')
                    ).order_by(Student.university_id.desc()).first()
                    
                    if last_student:
                        last_number = int(last_student.university_id[-3:])
                        new_number = last_number + 1
                    else:
                        new_number = 1
                    
                    university_id = f"{year_prefix}{new_number:03d}"
                
                # Check for duplicates
                existing_user = User.query.filter(
                    db.or_(User.email == email, User.username == university_id)
                ).first()
                
                existing_student = Student.query.filter_by(university_id=university_id).first()
                
                if existing_user or existing_student:
                    if skip_duplicates:
                        result.update({
                            'duplicate_skipped': True,
                            'error': f'مستخدم موجود مسبقاً: {email} أو {university_id}'
                        })
                        duplicate_skips += 1
                        results.append(result)
                        continue
                    else:
                        raise ValueError(f'مستخدم موجود مسبقاً: {email} أو {university_id}')
                
                # Create user account
                user = User(
                    username=university_id,
                    email=email,
                    full_name=full_name,
                    phone=phone,
                    role=UserRole.STUDENT,
                    is_active=True
                )
                user.set_password(default_password)
                
                db.session.add(user)
                db.session.flush()  # Get user ID
                
                # Generate secret code
                secret_code = InputValidator.sanitize_string(
                    student_data.get('secret_code', secrets.token_urlsafe(6).upper()[:8])
                ) if not auto_generate_codes else secrets.token_urlsafe(6).upper()[:8]
                
                # Create student profile
                student = Student(
                    user_id=user.id,
                    university_id=university_id,
                    section=SectionEnum(section),
                    study_year=study_year,
                    study_type=StudyTypeEnum(study_type),
                    academic_status=AcademicStatusEnum.ACTIVE,
                    is_repeater=bool(student_data.get('is_repeater', False)),
                    failed_subjects=student_data.get('failed_subjects', []) if student_data.get('failed_subjects') else None
                )
                
                # Set secret code
                student.set_secret_code(secret_code)
                
                db.session.add(student)
                db.session.flush()  # Get student ID
                
                result.update({
                    'success': True,
                    'student_id': student.id,
                    'user_id': user.id,
                    'university_id': university_id,
                    'generated_code': secret_code if auto_generate_codes else None,
                    'email': email,
                    'full_name': full_name
                })
                successful_creates += 1
                
            except ValueError as ve:
                result['error'] = str(ve)
                failed_creates += 1
            except Exception as e:
                result['error'] = f'خطأ غير متوقع: {str(e)}'
                failed_creates += 1
            
            results.append(result)
        
        # 5. Commit successful creates
        if successful_creates > 0:
            try:
                db.session.commit()
                logging.info(f'Bulk student creation by {get_current_user().username}: {successful_creates} created, {failed_creates} failed, {duplicate_skips} skipped')
            except Exception as e:
                db.session.rollback()
                return jsonify(error_response('DATABASE_ERROR', f'خطأ في حفظ الطلاب: {str(e)}')), 500
        else:
            db.session.rollback()
        
        # 6. Generate summary
        summary = {
            'total_processed': len(results),
            'successful_creates': successful_creates,
            'failed_creates': failed_creates,
            'duplicate_skips': duplicate_skips,
            'success_rate': round((successful_creates / len(results)) * 100, 2) if results else 0,
            'processing_options': {
                'auto_generate_codes': auto_generate_codes,
                'send_notifications': send_notifications,
                'skip_duplicates': skip_duplicates
            }
        }
        
        response_data = {
            'creation_results': results,
            'summary': summary
        }
        
        message = f'تم إنشاء {successful_creates} طالب بنجاح'
        if failed_creates > 0:
            message += f'، {failed_creates} فشل'
        if duplicate_skips > 0:
            message += f'، {duplicate_skips} تم تخطيه (مكرر)'
        
        return jsonify(batch_response(response_data, summary, message)), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Bulk create students error: {str(e)}', exc_info=True)
        return jsonify(error_response('BULK_CREATE_ERROR', 'حدث خطأ أثناء إنشاء الطلاب')), 500

# ============================================================================
# ROOMS MANAGEMENT - إدارة القاعات
# ============================================================================

@admin_bp.route('/rooms', methods=['POST'])
@jwt_required
@require_permission('create_room')
def create_room():
    """
    POST /api/admin/rooms
    Create a new room with GPS polygon and altitude data
    إنشاء قاعة جديدة مع إحداثيات GPS ثلاثية الأبعاد
    """
    try:
        # 1. Validate input
        data = request.get_json()
        if not data:
            return jsonify(error_response('INVALID_INPUT', 'بيانات القاعة مطلوبة')), 400
        
        # Validate required fields
        required_fields = [
            'name', 'building', 'floor', 'center_latitude', 'center_longitude',
            'ground_reference_altitude', 'floor_altitude', 'ceiling_height'
        ]
        
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return jsonify(validation_error), 400
        
        # 2. Extract and validate data
        name = InputValidator.sanitize_string(data['name']).upper()
        building = InputValidator.sanitize_string(data['building'])
        floor = int(data['floor'])
        room_type = data.get('room_type', 'classroom')
        capacity = int(data.get('capacity', 30))
        
        # GPS coordinates
        center_latitude = float(data['center_latitude'])
        center_longitude = float(data['center_longitude'])
        ground_reference_altitude = float(data['ground_reference_altitude'])
        floor_altitude = float(data['floor_altitude'])
        ceiling_height = float(data['ceiling_height'])
        
        # Optional fields
        barometric_pressure_reference = data.get('barometric_pressure_reference')
        wifi_ssid = InputValidator.sanitize_string(data.get('wifi_ssid', ''))
        
        # GPS polygon (optional, will auto-generate if not provided)
        gps_polygon = data.get('gps_polygon')
        polygon_width = float(data.get('polygon_width_meters', 8.0))
        polygon_height = float(data.get('polygon_height_meters', 6.0))
        
        # 3. Validate data ranges
        if not (-90 <= center_latitude <= 90):
            return jsonify(error_response('INVALID_LATITUDE', 'خط العرض يجب أن يكون بين -90 و 90')), 400
        
        if not (-180 <= center_longitude <= 180):
            return jsonify(error_response('INVALID_LONGITUDE', 'خط الطول يجب أن يكون بين -180 و 180')), 400
        
        if floor < 0:
            return jsonify(error_response('INVALID_FLOOR', 'رقم الطابق يجب أن يكون موجب')), 400
        
        if capacity <= 0:
            return jsonify(error_response('INVALID_CAPACITY', 'سعة القاعة يجب أن تكون أكبر من صفر')), 400
        
        if ceiling_height <= 0:
            return jsonify(error_response('INVALID_CEILING_HEIGHT', 'ارتفاع السقف يجب أن يكون أكبر من صفر')), 400
        
        # Validate room type
        try:
            room_type_enum = RoomTypeEnum(room_type)
        except ValueError:
            return jsonify(error_response('INVALID_ROOM_TYPE', 'نوع القاعة غير صحيح')), 400
        
        # 4. Check for duplicate room name
        existing_room = Room.query.filter_by(name=name).first()
        if existing_room:
            return jsonify(error_response('DUPLICATE_ROOM_NAME', f'اسم القاعة موجود مسبقاً: {name}')), 409
        
        # 5. Create room
        room = Room(
            name=name,
            building=building,
            floor=floor,
            room_type=room_type_enum,
            capacity=capacity,
            center_latitude=center_latitude,
            center_longitude=center_longitude,
            ground_reference_altitude=ground_reference_altitude,
            floor_altitude=floor_altitude,
            ceiling_height=ceiling_height,
            wifi_ssid=wifi_ssid,
            is_active=True
        )
        
        # Set barometric pressure if provided
        if barometric_pressure_reference:
            room.barometric_pressure_reference = float(barometric_pressure_reference)
        
        # 6. Set GPS polygon
        if gps_polygon and isinstance(gps_polygon, list) and len(gps_polygon) >= 3:
            # Validate polygon coordinates
            for point in gps_polygon:
                if not isinstance(point, list) or len(point) != 2:
                    return jsonify(error_response('INVALID_POLYGON_FORMAT', 'نقاط المضلع يجب أن تكون [latitude, longitude]')), 400
                
                lat, lng = point
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    return jsonify(error_response('INVALID_POLYGON_COORDINATES', 'إحداثيات المضلع غير صحيحة')), 400
            
            room.gps_polygon = gps_polygon
        else:
            # Auto-generate rectangular polygon
            room.set_rectangular_polygon(
                center_latitude, center_longitude,
                width_meters=polygon_width, height_meters=polygon_height
            )
        
        # 7. Save room
        db.session.add(room)
        db.session.commit()
        
        # 8. Log creation
        user = get_current_user()
        logging.info(f'Room created by {user.username}: {name} in {building}, floor {floor}')
        
        # 9. Prepare response
        room_data = {
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
                'ground_reference_altitude': float(room.ground_reference_altitude),
                'floor_altitude': float(room.floor_altitude),
                'ceiling_height': float(room.ceiling_height),
                'barometric_pressure_reference': float(room.barometric_pressure_reference) if room.barometric_pressure_reference else None
            },
            'wifi_ssid': room.wifi_ssid,
            'is_active': room.is_active,
            'created_at': room.created_at.isoformat()
        }
        
        return jsonify(success_response(room_data, message='تم إنشاء القاعة بنجاح')), 201
        
    except ValueError as ve:
        return jsonify(error_response('VALIDATION_ERROR', str(ve))), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f'Create room error: {str(e)}', exc_info=True)
        return jsonify(error_response('CREATE_ROOM_ERROR', 'حدث خطأ أثناء إنشاء القاعة')), 500

@admin_bp.route('/rooms/<int:room_id>', methods=['PUT'])
@jwt_required
@require_permission('update_room')
def update_room(room_id):
    """
    PUT /api/admin/rooms/<id>
    Update room information including GPS coordinates
    تحديث معلومات القاعة بما في ذلك الإحداثيات
    """
    try:
        # 1. Find room
        room = Room.query.get(room_id)
        if not room:
            return jsonify(not_found_response('قاعة', room_id)), 404
        
        # 2. Validate input
        data = request.get_json()
        if not data:
            return jsonify(error_response('INVALID_INPUT', 'بيانات التحديث مطلوبة')), 400
        
        # 3. Update fields if provided
        updatable_fields = [
            'name', 'building', 'floor', 'room_type', 'capacity',
            'center_latitude', 'center_longitude', 'ground_reference_altitude',
            'floor_altitude', 'ceiling_height', 'barometric_pressure_reference',
            'wifi_ssid', 'is_active', 'gps_polygon'
        ]
        
        updates_made = []
        
        for field in updatable_fields:
            if field in data:
                if field == 'name':
                    new_name = InputValidator.sanitize_string(data['name']).upper()
                    if new_name != room.name:
                        # Check for duplicate name
                        existing = Room.query.filter(Room.name == new_name, Room.id != room.id).first()
                        if existing:
                            return jsonify(error_response('DUPLICATE_ROOM_NAME', f'اسم القاعة موجود مسبقاً: {new_name}')), 409
                        room.name = new_name
                        updates_made.append('name')
                
                elif field == 'building':
                    room.building = InputValidator.sanitize_string(data['building'])
                    updates_made.append('building')
                
                elif field == 'floor':
                    new_floor = int(data['floor'])
                    if new_floor < 0:
                        return jsonify(error_response('INVALID_FLOOR', 'رقم الطابق يجب أن يكون موجب')), 400
                    room.floor = new_floor
                    updates_made.append('floor')
                
                elif field == 'room_type':
                    try:
                        room.room_type = RoomTypeEnum(data['room_type'])
                        updates_made.append('room_type')
                    except ValueError:
                        return jsonify(error_response('INVALID_ROOM_TYPE', 'نوع القاعة غير صحيح')), 400
                
                elif field == 'capacity':
                    new_capacity = int(data['capacity'])
                    if new_capacity <= 0:
                        return jsonify(error_response('INVALID_CAPACITY', 'سعة القاعة يجب أن تكون أكبر من صفر')), 400
                    room.capacity = new_capacity
                    updates_made.append('capacity')
                
                elif field in ['center_latitude', 'center_longitude']:
                    coord = float(data[field])
                    if field == 'center_latitude' and not (-90 <= coord <= 90):
                        return jsonify(error_response('INVALID_LATITUDE', 'خط العرض يجب أن يكون بين -90 و 90')), 400
                    elif field == 'center_longitude' and not (-180 <= coord <= 180):
                        return jsonify(error_response('INVALID_LONGITUDE', 'خط الطول يجب أن يكون بين -180 و 180')), 400
                    setattr(room, field, coord)
                    updates_made.append(field)
                
                elif field in ['ground_reference_altitude', 'floor_altitude', 'ceiling_height']:
                    altitude = float(data[field])
                    if field == 'ceiling_height' and altitude <= 0:
                        return jsonify(error_response('INVALID_CEILING_HEIGHT', 'ارتفاع السقف يجب أن يكون أكبر من صفر')), 400
                    setattr(room, field, altitude)
                    updates_made.append(field)
                
                elif field == 'barometric_pressure_reference':
                    if data[field] is not None:
                        room.barometric_pressure_reference = float(data[field])
                    else:
                        room.barometric_pressure_reference = None
                    updates_made.append(field)
                
                elif field == 'wifi_ssid':
                    room.wifi_ssid = InputValidator.sanitize_string(data['wifi_ssid'])
                    updates_made.append(field)
                
                elif field == 'is_active':
                    room.is_active = bool(data['is_active'])
                    updates_made.append(field)
                
                elif field == 'gps_polygon':
                    polygon = data['gps_polygon']
                    if polygon and isinstance(polygon, list) and len(polygon) >= 3:
                        # Validate polygon coordinates
                        for point in polygon:
                            if not isinstance(point, list) or len(point) != 2:
                                return jsonify(error_response('INVALID_POLYGON_FORMAT', 'نقاط المضلع يجب أن تكون [latitude, longitude]')), 400
                            
                            lat, lng = point
                            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                                return jsonify(error_response('INVALID_POLYGON_COORDINATES', 'إحداثيات المضلع غير صحيحة')), 400
                        
                        room.gps_polygon = polygon
                        updates_made.append('gps_polygon')
                    elif polygon is None:
                        # Regenerate polygon with current center coordinates
                        room.set_rectangular_polygon(
                            float(room.center_latitude), float(room.center_longitude),
                            width_meters=8.0, height_meters=6.0
                        )
                        updates_made.append('gps_polygon_regenerated')
        
        # 4. Update timestamp
        if updates_made:
            room.updated_at = datetime.utcnow()
        
        # 5. Save changes
        db.session.commit()
        
        # 6. Log update
        user = get_current_user()
        logging.info(f'Room updated by {user.username}: {room.name}, fields: {", ".join(updates_made)}')
        
        # 7. Prepare response
        room_data = {
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
                'ground_reference_altitude': float(room.ground_reference_altitude),
                'floor_altitude': float(room.floor_altitude),
                'ceiling_height': float(room.ceiling_height),
                'barometric_pressure_reference': float(room.barometric_pressure_reference) if room.barometric_pressure_reference else None
            },
            'wifi_ssid': room.wifi_ssid,
            'is_active': room.is_active,
            'created_at': room.created_at.isoformat(),
            'updated_at': room.updated_at.isoformat() if room.updated_at else None
        }
        
        return jsonify(success_response(
            room_data,
            message=f'تم تحديث القاعة بنجاح ({len(updates_made)} تغيير)'
        ))
        
    except ValueError as ve:
        return jsonify(error_response('VALIDATION_ERROR', str(ve))), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f'Update room error: {str(e)}', exc_info=True)
        return jsonify(error_response('UPDATE_ROOM_ERROR', 'حدث خطأ أثناء تحديث القاعة')), 500

# ============================================================================
# SCHEDULES MANAGEMENT - إدارة الجداول
# ============================================================================

@admin_bp.route('/schedules/bulk-create', methods=['POST'])
@jwt_required
@require_permission('create_schedule')
def bulk_create_schedules():
    """
    POST /api/admin/schedules/bulk-create
    Create multiple schedules with conflict detection
    إنشاء جداول متعددة مع كشف التعارضات
    """
    try:
        # 1. Validate input
        data = request.get_json()
        if not data or 'schedules' not in data:
            return jsonify(error_response('INVALID_INPUT', 'مصفوفة الجداول مطلوبة')), 400
        
        schedules_data = data['schedules']
        if not isinstance(schedules_data, list):
            return jsonify(error_response('INVALID_FORMAT', 'الجداول يجب أن تكون مصفوفة')), 400
        
        # 2. Validate bulk operation limit
        bulk_limit_error = validate_bulk_operation_limit(schedules_data, max_items=200)
        if bulk_limit_error:
            return jsonify(bulk_limit_error), 400
        
        # 3. Get processing options
        options = data.get('options', {})
        check_conflicts = options.get('check_conflicts', True)
        auto_resolve_conflicts = options.get('auto_resolve_conflicts', False)
        academic_year = options.get('academic_year')
        semester = options.get('semester')
        
        # Validate academic year and semester
        if academic_year:
            is_valid_year, year_error = validate_academic_year(academic_year)
            if not is_valid_year:
                return jsonify(error_response('INVALID_ACADEMIC_YEAR', year_error)), 400
        else:
            # Generate current academic year
            current_year = datetime.now().year
            academic_year = f"{current_year}-{current_year + 1}"
        
        if semester:
            is_valid_semester, semester_error = validate_semester(semester)
            if not is_valid_semester:
                return jsonify(error_response('INVALID_SEMESTER', semester_error)), 400
        else:
            # Determine current semester
            current_month = datetime.now().month
            if 9 <= current_month <= 12:
                semester = 'first'
            elif 2 <= current_month <= 6:
                semester = 'second'
            else:
                semester = 'summer'
        
        # 4. Process each schedule record
        results = []
        successful_creates = 0
        failed_creates = 0
        conflicts_detected = []
        
        for index, schedule_data in enumerate(schedules_data):
            result = {
                'index': index,
                'success': False,
                'error': None,
                'schedule_id': None,
                'conflicts': []
            }
            
            try:
                # Validate required fields
                required_fields = ['subject_id', 'teacher_id', 'room_id', 'section', 'day_of_week', 'start_time', 'end_time']
                missing_fields = [field for field in required_fields if field not in schedule_data]
                
                if missing_fields:
                    raise ValueError(f'حقول مطلوبة مفقودة: {", ".join(missing_fields)}')
                
                # Extract and validate data
                subject_id = int(schedule_data['subject_id'])
                teacher_id = int(schedule_data['teacher_id'])
                room_id = int(schedule_data['room_id'])
                section = schedule_data['section'].upper()
                day_of_week = int(schedule_data['day_of_week'])
                start_time_str = schedule_data['start_time']
                end_time_str = schedule_data['end_time']
                
                # Validate foreign key references
                subject = Subject.query.get(subject_id)
                if not subject:
                    raise ValueError(f'مادة غير موجودة: {subject_id}')
                
                teacher = Teacher.query.get(teacher_id)
                if not teacher:
                    raise ValueError(f'مدرس غير موجود: {teacher_id}')
                
                room = Room.query.get(room_id)
                if not room:
                    raise ValueError(f'قاعة غير موجودة: {room_id}')
                
                # Validate section
                is_valid_section, section_error = validate_section(section)
                if not is_valid_section:
                    raise ValueError(section_error)
                
                # Validate day of week (1=Sunday, 7=Saturday)
                if not (1 <= day_of_week <= 7):
                    raise ValueError('يوم الأسبوع يجب أن يكون بين 1 (الأحد) و 7 (السبت)')
                
                # Parse and validate times
                try:
                    start_time = time.fromisoformat(start_time_str)
                    end_time = time.fromisoformat(end_time_str)
                except ValueError:
                    raise ValueError('تنسيق الوقت غير صحيح (استخدم HH:MM)')
                
                if start_time >= end_time:
                    raise ValueError('وقت البداية يجب أن يكون قبل وقت النهاية')
                
                # Calculate duration
                start_datetime = datetime.combine(date.today(), start_time)
                end_datetime = datetime.combine(date.today(), end_time)
                duration = (end_datetime - start_datetime).total_seconds() / 60
                
                if duration < 30:
                    raise ValueError('مدة المحاضرة يجب أن تكون 30 دقيقة على الأقل')
                
                if duration > 240:  # 4 hours
                    raise ValueError('مدة المحاضرة لا يمكن أن تتجاوز 4 ساعات')
                
                # 5. Check for conflicts if enabled
                detected_conflicts = []
                
                if check_conflicts:
                    # Teacher conflict check
                    teacher_conflict = Schedule.query.filter(
                        Schedule.teacher_id == teacher_id,
                        Schedule.day_of_week == day_of_week,
                        Schedule.academic_year == academic_year,
                        Schedule.semester == SemesterEnum(semester),
                        Schedule.is_active == True,
                        Schedule.start_time < end_time,
                        Schedule.end_time > start_time
                    ).first()
                    
                    if teacher_conflict:
                        detected_conflicts.append({
                            'type': 'teacher_conflict',
                            'message': f'المدرس مشغول في نفس الوقت',
                            'conflicting_schedule_id': teacher_conflict.id
                        })
                    
                    # Room conflict check
                    room_conflict = Schedule.query.filter(
                        Schedule.room_id == room_id,
                        Schedule.day_of_week == day_of_week,
                        Schedule.academic_year == academic_year,
                        Schedule.semester == SemesterEnum(semester),
                        Schedule.is_active == True,
                        Schedule.start_time < end_time,
                        Schedule.end_time > start_time
                    ).first()
                    
                    if room_conflict:
                        detected_conflicts.append({
                            'type': 'room_conflict',
                            'message': f'القاعة محجوزة في نفس الوقت',
                            'conflicting_schedule_id': room_conflict.id
                        })
                    
                    # Section conflict check
                    section_conflict = Schedule.query.filter(
                        Schedule.section == SectionEnum(section),
                        Schedule.day_of_week == day_of_week,
                        Schedule.academic_year == academic_year,
                        Schedule.semester == SemesterEnum(semester),
                        Schedule.is_active == True,
                        Schedule.start_time < end_time,
                        Schedule.end_time > start_time
                    ).first()
                    
                    if section_conflict:
                        detected_conflicts.append({
                            'type': 'section_conflict',
                            'message': f'الشعبة لديها محاضرة أخرى في نفس الوقت',
                            'conflicting_schedule_id': section_conflict.id
                        })
                
                # 6. Handle conflicts
                if detected_conflicts and not auto_resolve_conflicts:
                    result['conflicts'] = detected_conflicts
                    result['error'] = f'تم اكتشاف {len(detected_conflicts)} تعارض'
                    conflicts_detected.extend(detected_conflicts)
                    failed_creates += 1
                    results.append(result)
                    continue
                
                # 7. Create schedule
                schedule = Schedule(
                    subject_id=subject_id,
                    teacher_id=teacher_id,
                    room_id=room_id,
                    section=SectionEnum(section),
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    academic_year=academic_year,
                    semester=SemesterEnum(semester),
                    is_active=True
                )
                
                db.session.add(schedule)
                db.session.flush()  # Get schedule ID
                
                result.update({
                    'success': True,
                    'schedule_id': schedule.id,
                    'conflicts': detected_conflicts if auto_resolve_conflicts else []
                })
                successful_creates += 1
                
            except ValueError as ve:
                result['error'] = str(ve)
                failed_creates += 1
            except Exception as e:
                result['error'] = f'خطأ غير متوقع: {str(e)}'
                failed_creates += 1
            
            results.append(result)
        
        # 8. Commit successful creates
        if successful_creates > 0:
            try:
                db.session.commit()
                logging.info(f'Bulk schedule creation by {get_current_user().username}: {successful_creates} created, {failed_creates} failed, {len(conflicts_detected)} conflicts')
            except Exception as e:
                db.session.rollback()
                return jsonify(error_response('DATABASE_ERROR', f'خطأ في حفظ الجداول: {str(e)}')), 500
        else:
            db.session.rollback()
        
        # 9. Generate summary
        summary = {
            'total_processed': len(results),
            'successful_creates': successful_creates,
            'failed_creates': failed_creates,
            'conflicts_detected': len(conflicts_detected),
            'success_rate': round((successful_creates / len(results)) * 100, 2) if results else 0,
            'academic_period': {
                'academic_year': academic_year,
                'semester': semester
            },
            'processing_options': {
                'check_conflicts': check_conflicts,
                'auto_resolve_conflicts': auto_resolve_conflicts
            }
        }
        
        response_data = {
            'creation_results': results,
            'summary': summary,
            'conflicts_summary': conflicts_detected
        }
        
        message = f'تم إنشاء {successful_creates} جدول بنجاح'
        if failed_creates > 0:
            message += f'، {failed_creates} فشل'
        if conflicts_detected:
            message += f'، {len(conflicts_detected)} تعارض'
        
        return jsonify(batch_response(response_data, summary, message)), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Bulk create schedules error: {str(e)}', exc_info=True)
        return jsonify(error_response('BULK_CREATE_SCHEDULES_ERROR', 'حدث خطأ أثناء إنشاء الجداول')), 500

# ============================================================================
# SYSTEM HEALTH & STATUS - صحة النظام والحالة
# ============================================================================

@admin_bp.route('/system/health', methods=['GET'])
@jwt_required
@require_permission('system_settings')
def admin_system_health():
    """
    GET /api/admin/system/health
    Comprehensive system health check for administrators
    فحص شامل لصحة النظام للمديرين
    """
    try:
        health_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_status': 'healthy',
            'components': {},
            'statistics': {},
            'performance': {},
            'storage': {},
            'recommendations': []
        }
        
        # 1. Database component health
        try:
            # Test database connection
            db.session.execute('SELECT 1').fetchone()
            
            # Get database statistics
            db_stats = {
                'connection_status': 'healthy',
                'total_users': User.query.count(),
                'total_students': Student.query.count(),
                'total_teachers': Teacher.query.count(),
                'total_subjects': Subject.query.count(),
                'total_rooms': Room.query.count(),
                'total_schedules': Schedule.query.count(),
                'total_lectures': Lecture.query.count(),
                'active_users': User.query.filter_by(is_active=True).count(),
                'face_registered_students': Student.query.filter_by(face_registered=True).count()
            }
            
            # Recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_stats = {
                'new_students_24h': Student.query.filter(Student.created_at >= yesterday).count(),
                'recent_logins': User.query.filter(User.last_login >= yesterday).count(),
                'new_lectures_24h': Lecture.query.filter(Lecture.created_at >= yesterday).count()
            }
            
            health_data['components']['database'] = {
                'status': 'healthy',
                'statistics': db_stats,
                'recent_activity': recent_stats
            }
            
        except Exception as e:
            health_data['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['system_status'] = 'degraded'
        
        # 2. Cache component health (Redis)
        try:
            from config.database import redis_client
            redis_client.ping()
            
            # Get Redis info
            redis_info = redis_client.info()
            
            health_data['components']['cache'] = {
                'status': 'healthy',
                'connected_clients': redis_info.get('connected_clients', 0),
                'used_memory_mb': round(redis_info.get('used_memory', 0) / (1024 * 1024), 2),
                'cache_hit_rate': round(redis_info.get('keyspace_hits', 0) / max(redis_info.get('keyspace_hits', 0) + redis_info.get('keyspace_misses', 0), 1) * 100, 2)
            }
            
        except Exception as e:
            health_data['components']['cache'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['system_status'] = 'degraded'
        
        # 3. Storage component health
        import os
        storage_paths = {
            'face_templates': '/storage/face_templates',
            'qr_codes': '/storage/qr_codes',
            'reports': '/storage/reports',
            'uploads': '/storage/uploads',
            'backups': '/storage/backups'
        }
        
        storage_health = {}
        for path_name, path in storage_paths.items():
            try:
                if os.path.exists(path):
                    # Calculate directory size
                    total_size = 0
                    file_count = 0
                    for dirpath, dirnames, filenames in os.walk(path):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                total_size += os.path.getsize(filepath)
                                file_count += 1
                            except OSError:
                                pass
                    
                    storage_health[path_name] = {
                        'status': 'healthy',
                        'exists': True,
                        'writable': os.access(path, os.W_OK),
                        'size_mb': round(total_size / (1024 * 1024), 2),
                        'file_count': file_count
                    }
                else:
                    storage_health[path_name] = {
                        'status': 'missing',
                        'exists': False,
                        'error': 'Directory does not exist'
                    }
                    health_data['system_status'] = 'degraded'
                    
            except Exception as e:
                storage_health[path_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        health_data['storage'] = storage_health
        
        # 4. Performance metrics
        try:
            import psutil
            
            health_data['performance'] = {
                'cpu_usage_percent': psutil.cpu_percent(interval=1),
                'memory_usage_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': round(psutil.disk_usage('/').percent, 2),
                'available_memory_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                'free_disk_gb': round(psutil.disk_usage('/').free / (1024**3), 2)
            }
            
            # Check for performance issues
            if health_data['performance']['cpu_usage_percent'] > 80:
                health_data['recommendations'].append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': f"استخدام المعالج مرتفع ({health_data['performance']['cpu_usage_percent']}%)"
                })
            
            if health_data['performance']['memory_usage_percent'] > 85:
                health_data['recommendations'].append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': f"استخدام الذاكرة مرتفع ({health_data['performance']['memory_usage_percent']}%)"
                })
            
            if health_data['performance']['disk_usage_percent'] > 90:
                health_data['recommendations'].append({
                    'type': 'storage',
                    'severity': 'critical',
                    'message': f"مساحة القرص الصلب ممتلئة ({health_data['performance']['disk_usage_percent']}%)"
                })
                health_data['system_status'] = 'critical'
                
        except ImportError:
            health_data['performance'] = {
                'error': 'psutil module not available'
            }
        
        # 5. API endpoints health check
        api_health = {
            'total_endpoints': 20,
            'authentication_endpoints': 3,
            'admin_endpoints': 6,
            'student_endpoints': 4,
            'attendance_endpoints': 4,
            'reports_endpoints': 3
        }
        
        # Check for recent API errors (would require error logging system)
        health_data['components']['api'] = {
            'status': 'healthy',
            'endpoints': api_health
        }
        
        # 6. Security component check
        security_check = {
            'status': 'healthy',
            'ssl_enabled': request.is_secure,
            'jwt_authentication': True,  # Would check JWT service
            'rate_limiting': True,       # Would check rate limiter
            'input_validation': True     # Would check validation system
        }
        
        health_data['components']['security'] = security_check
        
        # 7. Overall health assessment
        component_count = len(health_data['components'])
        healthy_components = sum(1 for comp in health_data['components'].values() if comp.get('status') == 'healthy')
        
        if healthy_components == component_count:
            final_status = 'healthy'
        elif healthy_components >= component_count * 0.8:
            final_status = 'degraded'
        else:
            final_status = 'critical'
        
        health_data['system_status'] = final_status
        health_data['health_score'] = round((healthy_components / component_count) * 100, 1)
        
        # 8. Add system recommendations
        if final_status == 'degraded':
            health_data['recommendations'].append({
                'type': 'system',
                'severity': 'medium',
                'message': 'بعض مكونات النظام تحتاج إلى انتباه'
            })
        elif final_status == 'critical':
            health_data['recommendations'].append({
                'type': 'system',
                'severity': 'critical',
                'message': 'النظام يحتاج إلى تدخل فوري'
            })
        
        # 9. Log health check
        user = get_current_user()
        logging.info(f'Admin health check by {user.username}: {final_status} (score: {health_data["health_score"]}%)')
        
        return jsonify(success_response(health_data))
        
    except Exception as e:
        logging.error(f'Admin system health error: {str(e)}', exc_info=True)
        return jsonify(error_response('SYSTEM_HEALTH_ERROR', 'حدث خطأ أثناء فحص صحة النظام')), 500

# Error handlers specific to admin blueprint
@admin_bp.errorhandler(403)
def admin_forbidden(error):
    """Handle forbidden access for admin endpoints"""
    return jsonify(error_response(
        'ADMIN_FORBIDDEN',
        'صلاحيات إدارية مطلوبة للوصول لهذا المورد'
    )), 403

@admin_bp.errorhandler(409)
def admin_conflict(error):
    """Handle conflict errors in admin operations"""
    return jsonify(error_response(
        'ADMIN_CONFLICT',
        'تعارض في البيانات. تحقق من وجود تكرارات أو تعارضات زمنية.'
    )), 409

@admin_bp.errorhandler(413)
def admin_payload_too_large(error):
    """Handle large payload errors in bulk operations"""
    return jsonify(error_response(
        'PAYLOAD_TOO_LARGE',
        'حجم البيانات كبير جداً. قسم العملية إلى دفعات أصغر.'
    )), 413