"""
⚡ Core Operations APIs - عمليات الحضور الأساسية
Implementation: 4 critical core operation endpoints
اليوم 4: تطبيق العمليات الأساسية للحضور
"""

from flask import Blueprint, request, jsonify, current_app, g
from security import jwt_required, require_permission, get_current_user
from models import (
    Lecture, QRSession, AttendanceRecord, Student, Teacher,
    LectureStatusEnum, QRStatusEnum, AttendanceStatusEnum,
    AttendanceTypeEnum, VerificationStepEnum
)
from utils.response_helpers import (
    success_response, error_response, batch_response,
    validation_error_response, not_found_response
)
from utils.validation_helpers import (
    validate_required_fields, validate_bulk_operation_limit,
    validate_ids_list, InputValidator
)
from config.database import db, redis_client
from datetime import datetime, timedelta
import logging
import uuid
import hashlib
import secrets
import json
import base64
from cryptography.fernet import Fernet

# Create blueprint
core_ops_bp = Blueprint('core_ops', __name__, url_prefix='/api')

# ============================================================================
# QR CODE GENERATION - توليد رموز QR
# ============================================================================

@core_ops_bp.route('/lectures/<int:lecture_id>/generate-qr', methods=['POST'])
@jwt_required
@require_permission('generate_qr')
def generate_qr_code(lecture_id):
    """
    POST /api/lectures/<id>/generate-qr
    Generate secure QR code for lecture attendance with comprehensive validation
    توليد رمز QR آمن لحضور المحاضرة مع تحقق شامل
    """
    try:
        # 1. Find and validate lecture
        lecture = Lecture.query.get(lecture_id)
        if not lecture:
            return jsonify(not_found_response('محاضرة', lecture_id)), 404
        
        # 2. Verify teacher authorization
        user = get_current_user()
        teacher = user.get_teacher_profile()
        
        if not teacher:
            return jsonify(error_response('NOT_TEACHER', 'هذا الـ API مخصص للمدرسين فقط')), 403
        
        # Verify teacher owns this lecture
        if lecture.schedule.teacher_id != teacher.id:
            return jsonify(error_response('UNAUTHORIZED_LECTURE', 'غير مصرح لك بإدارة هذه المحاضرة')), 403
        
        # 3. Validate lecture status and timing
        if lecture.status not in [LectureStatusEnum.SCHEDULED, LectureStatusEnum.ACTIVE]:
            return jsonify(error_response(
                'INVALID_LECTURE_STATUS',
                f'لا يمكن توليد QR للمحاضرة في الحالة: {lecture.status.value}'
            )), 400
        
        # Check if QR generation is allowed based on timing
        now = datetime.utcnow()
        scheduled_start = lecture.get_scheduled_start_time()
        
        if scheduled_start:
            # Allow QR generation 30 minutes before and 2 hours after scheduled start
            earliest_time = scheduled_start - timedelta(minutes=30)
            latest_time = scheduled_start + timedelta(hours=2)
            
            if now < earliest_time:
                return jsonify(error_response(
                    'TOO_EARLY',
                    f'يمكن توليد QR من {earliest_time.strftime("%H:%M")} فقط'
                )), 400
            
            if now > latest_time:
                return jsonify(error_response(
                    'TOO_LATE',
                    f'انتهت فترة توليد QR في {latest_time.strftime("%H:%M")}'
                )), 400
        
        # 4. Get and validate QR settings
        data = request.get_json() or {}
        
        # QR configuration
        duration_minutes = int(data.get('duration_minutes', 15))  # Default 15 minutes
        max_usage = int(data.get('max_usage_count', 1000))        # Default 1000 uses
        allow_multiple_scans = bool(data.get('allow_multiple_scans', True))
        
        # Validation
        if not (1 <= duration_minutes <= 60):
            return jsonify(error_response('INVALID_DURATION', 'مدة QR يجب أن تكون بين 1 و 60 دقيقة')), 400
        
        if not (1 <= max_usage <= 2000):
            return jsonify(error_response('INVALID_MAX_USAGE', 'العدد الأقصى للاستخدام يجب أن يكون بين 1 و 2000')), 400
        
        # 5. Check for existing active QR sessions
        existing_qr = QRSession.query.filter_by(
            lecture_id=lecture_id,
            is_active=True,
            status=QRStatusEnum.ACTIVE
        ).filter(
            QRSession.expires_at > datetime.utcnow()
        ).first()
        
        if existing_qr:
            # Check if teacher wants to replace existing QR
            force_new = data.get('force_new', False)
            
            if not force_new:
                # Return existing QR if still valid
                time_remaining = int((existing_qr.expires_at - datetime.utcnow()).total_seconds())
                if time_remaining > 0:
                    return jsonify(success_response({
                        'qr_session': {
                            'id': existing_qr.id,
                            'session_id': existing_qr.session_id,
                            'generated_at': existing_qr.generated_at.isoformat(),
                            'expires_at': existing_qr.expires_at.isoformat(),
                            'time_remaining_seconds': time_remaining,
                            'usage_count': existing_qr.current_usage_count,
                            'max_usage_count': existing_qr.max_usage_count,
                            'display_text': existing_qr.qr_display_text,
                            'status': 'existing',
                            'allow_multiple_scans': existing_qr.allow_multiple_scans
                        },
                        'lecture_info': {
                            'id': lecture.id,
                            'topic': lecture.topic,
                            'subject_name': lecture.schedule.subject.name if lecture.schedule and lecture.schedule.subject else None,
                            'room_name': lecture.schedule.room.name if lecture.schedule and lecture.schedule.room else None,
                            'section': lecture.schedule.section.value if lecture.schedule else None
                        }
                    }, message='QR موجود مسبقاً ولا يزال صالحاً'))
            else:
                # Deactivate existing QR
                existing_qr.is_active = False
                existing_qr.status = QRStatusEnum.EXPIRED
                existing_qr.deactivated_at = datetime.utcnow()
                db.session.add(existing_qr)
        
        # 6. Start lecture if not already started
        if lecture.status == LectureStatusEnum.SCHEDULED:
            lecture.start_lecture(teacher.user.id)
            db.session.add(lecture)
        
        # 7. Create comprehensive QR session
        session_id = str(uuid.uuid4())
        encryption_key = Fernet.generate_key()
        
        # Create QR data payload
        qr_payload = {
            'session_id': session_id,
            'lecture_id': lecture.id,
            'teacher_id': teacher.id,
            'room_id': lecture.schedule.room_id if lecture.schedule else None,
            'section': lecture.schedule.section.value if lecture.schedule else None,
            'generated_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=duration_minutes)).isoformat(),
            'verification_hash': hashlib.sha256(f"{session_id}{lecture.id}{teacher.id}".encode()).hexdigest()[:16]
        }
        
        # Encrypt QR payload
        fernet = Fernet(encryption_key)
        encrypted_payload = fernet.encrypt(json.dumps(qr_payload).encode())
        
        # Create QR session record
        qr_session = QRSession(
            session_id=session_id,
            lecture_id=lecture.id,
            generated_by_teacher_id=teacher.id,
            qr_data_encrypted=base64.b64encode(encrypted_payload).decode(),
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=duration_minutes),
            is_active=True,
            status=QRStatusEnum.ACTIVE,
            max_usage_count=max_usage,
            current_usage_count=0,
            allow_multiple_scans=allow_multiple_scans,
            encryption_algorithm='Fernet-AES256'
        )
        
        # Generate display text for QR code (what gets encoded in the QR image)
        qr_display_data = {
            'type': 'attendance_qr',
            'session': session_id,
            'lecture': lecture.id,
            'expires': qr_session.expires_at.isoformat(),
            'hash': qr_payload['verification_hash']
        }
        
        qr_session.qr_display_text = base64.b64encode(
            json.dumps(qr_display_data).encode()
        ).decode()
        
        # 8. Save to database and cache
        db.session.add(qr_session)
        db.session.commit()
        
        # Cache in Redis for fast access
        try:
            redis_key = f"qr_session:{session_id}"
            redis_data = {
                'lecture_id': lecture.id,
                'teacher_id': teacher.id,
                'expires_at': qr_session.expires_at.isoformat(),
                'max_usage': max_usage,
                'current_usage': 0
            }
            redis_client.setex(
                redis_key,
                duration_minutes * 60,  # TTL in seconds
                json.dumps(redis_data)
            )
        except Exception as e:
            logging.warning(f'Failed to cache QR session: {str(e)}')
        
        # 9. Log QR generation with details
        logging.info(f'QR generated for lecture {lecture_id} by teacher {teacher.employee_id}: session {session_id}, duration {duration_minutes}m, max_usage {max_usage}')
        
        # 10. Prepare comprehensive response
        response_data = {
            'qr_session': {
                'id': qr_session.id,
                'session_id': session_id,
                'generated_at': qr_session.generated_at.isoformat(),
                'expires_at': qr_session.expires_at.isoformat(),
                'time_remaining_seconds': duration_minutes * 60,
                'usage_count': 0,
                'max_usage_count': max_usage,
                'allow_multiple_scans': allow_multiple_scans,
                'display_text': qr_session.qr_display_text,
                'status': 'new'
            },
            'qr_payload': {
                'encoded_data': qr_session.qr_display_text,
                'format': 'base64_json',
                'encoding_instructions': 'Decode base64, then parse JSON for QR scanner'
            },
            'encryption_info': {
                'algorithm': 'Fernet-AES256',
                'key_for_mobile': base64.b64encode(encryption_key).decode(),  # For mobile app
                'key_storage_note': 'Store securely in device keychain'
            },
            'lecture_info': {
                'id': lecture.id,
                'topic': lecture.topic,
                'status': lecture.status.value,
                'subject': {
                    'code': lecture.schedule.subject.code,
                    'name': lecture.schedule.subject.name
                } if lecture.schedule and lecture.schedule.subject else None,
                'room': {
                    'name': lecture.schedule.room.name,
                    'building': lecture.schedule.room.building,
                    'floor': lecture.schedule.room.floor
                } if lecture.schedule and lecture.schedule.room else None,
                'section': lecture.schedule.section.value if lecture.schedule else None,
                'scheduled_time': scheduled_start.isoformat() if scheduled_start else None
            },
            'usage_guidelines': {
                'validity_period': f'{duration_minutes} دقيقة',
                'max_scans': max_usage,
                'multiple_scans_per_student': allow_multiple_scans,
                'recommended_display': 'عرض على الشاشة أو الإسقاط',
                'security_note': 'الرمز مشفر وآمن ضد التلاعب'
            }
        }
        
        return jsonify(success_response(response_data, message='تم توليد QR بنجاح')), 201
        
    except Exception as e:
        logging.error(f'QR generation error: {str(e)}', exc_info=True)
        return jsonify(error_response('QR_GENERATION_ERROR', 'حدث خطأ أثناء توليد QR')), 500

# ============================================================================
# BATCH ATTENDANCE UPLOAD - رفع الحضور بشكل جماعي
# ============================================================================

@core_ops_bp.route('/attendance/batch-upload', methods=['POST'])
@jwt_required
@require_permission('submit_attendance')
def batch_upload_attendance():
    """
    POST /api/attendance/batch-upload
    Upload batch attendance records from mobile app with comprehensive processing
    رفع سجلات الحضور بشكل جماعي من التطبيق مع معالجة شاملة
    """
    try:
        # 1. Validate input structure
        data = request.get_json()
        if not data or 'attendance_records' not in data:
            return jsonify(error_response('INVALID_INPUT', 'سجلات الحضور مطلوبة')), 400
        
        attendance_records = data['attendance_records']
        if not isinstance(attendance_records, list):
            return jsonify(error_response('INVALID_FORMAT', 'سجلات الحضور يجب أن تكون مصفوفة')), 400
        
        # 2. Validate bulk operation limit
        bulk_limit_error = validate_bulk_operation_limit(attendance_records, max_items=100)
        if bulk_limit_error:
            return jsonify(bulk_limit_error), 400
        
        # 3. Get current user (must be student)
        user = get_current_user()
        if user.role.value != 'student':
            return jsonify(error_response('UNAUTHORIZED', 'هذا الـ API مخصص للطلاب فقط')), 403
        
        student = user.get_student_profile()
        if not student:
            return jsonify(not_found_response('ملف الطالب')), 404
        
        # 4. Get batch processing options
        batch_options = data.get('batch_options', {})
        validation_level = batch_options.get('validation_level', 'strict')  # strict, normal, lenient
        conflict_resolution = batch_options.get('conflict_resolution', 'skip')  # skip, overwrite, merge
        offline_duration = batch_options.get('offline_duration_hours', 0)
        
        # 5. Process each attendance record with comprehensive validation
        results = []
        successful_uploads = 0
        failed_uploads = 0
        conflicts = []
        warnings = []
        
        for index, record_data in enumerate(attendance_records):
            result = {
                'index': index,
                'local_id': record_data.get('local_id'),
                'success': False,
                'error': None,
                'attendance_id': None,
                'conflict_detected': False,
                'warnings': [],
                'verification_status': {}
            }
            
            try:
                # Validate required fields for each record
                required_fields = [
                    'lecture_id', 'qr_session_id', 'recorded_latitude',
                    'recorded_longitude', 'check_in_time'
                ]
                
                missing_fields = [field for field in required_fields if field not in record_data]
                if missing_fields:
                    raise ValueError(f'حقول مطلوبة مفقودة: {", ".join(missing_fields)}')
                
                # Extract and validate core data
                lecture_id = int(record_data['lecture_id'])
                qr_session_id = record_data['qr_session_id']
                recorded_lat = float(record_data['recorded_latitude'])
                recorded_lng = float(record_data['recorded_longitude'])
                recorded_altitude = float(record_data.get('recorded_altitude', 0))
                check_in_time_str = record_data['check_in_time']
                
                # Parse check-in time
                try:
                    check_in_time = datetime.fromisoformat(check_in_time_str.replace('Z', '+00:00'))
                except ValueError:
                    raise ValueError('تنسيق وقت تسجيل الدخول غير صحيح')
                
                # Verification data
                location_verified = bool(record_data.get('location_verified', False))
                qr_verified = bool(record_data.get('qr_verified', False))
                face_verified = bool(record_data.get('face_verified', False))
                
                # Optional metadata
                device_info = record_data.get('device_info', {})
                gps_accuracy = float(record_data.get('gps_accuracy', 0))
                verification_details = record_data.get('verification_details', {})
                sync_timestamp = record_data.get('sync_timestamp')
                
                # 6. Comprehensive validation
                
                # Time validation
                time_validation_errors = []
                if check_in_time > datetime.utcnow() + timedelta(minutes=5):
                    time_validation_errors.append('وقت التسجيل في المستقبل')
                
                if offline_duration > 0 and (datetime.utcnow() - check_in_time).total_seconds() / 3600 > offline_duration + 48:
                    time_validation_errors.append(f'وقت التسجيل قديم جداً (أكثر من {offline_duration + 48} ساعة)')
                
                # GPS validation
                gps_validation_errors = []
                if not (-90 <= recorded_lat <= 90):
                    gps_validation_errors.append('خط العرض غير صحيح')
                
                if not (-180 <= recorded_lng <= 180):
                    gps_validation_errors.append('خط الطول غير صحيح')
                
                if gps_accuracy > 50:  # More than 50 meters accuracy
                    result['warnings'].append(f'دقة GPS منخفضة: {gps_accuracy}m')
                
                # Lecture validation
                lecture = Lecture.query.get(lecture_id)
                if not lecture:
                    raise ValueError(f'محاضرة غير موجودة: {lecture_id}')
                
                # Check if student should be in this lecture
                if lecture.schedule:
                    if lecture.schedule.section != student.section:
                        if validation_level == 'strict':
                            raise ValueError(f'الطالب من شعبة {student.section.value} وليس {lecture.schedule.section.value}')
                        else:
                            result['warnings'].append('الطالب من شعبة مختلفة')
                    
                    if lecture.schedule.subject and lecture.schedule.subject.study_year != student.study_year:
                        if validation_level == 'strict':
                            raise ValueError(f'الطالب من سنة {student.study_year} وليس {lecture.schedule.subject.study_year}')
                        else:
                            result['warnings'].append('الطالب من سنة دراسية مختلفة')
                
                # 7. Check for existing attendance (conflict detection)
                existing_attendance = AttendanceRecord.query.filter_by(
                    student_id=student.id,
                    lecture_id=lecture_id
                ).first()
                
                if existing_attendance:
                    conflict = {
                        'local_record': record_data,
                        'server_record': {
                            'id': existing_attendance.id,
                            'check_in_time': existing_attendance.check_in_time.isoformat(),
                            'attendance_type': existing_attendance.attendance_type.value,
                            'verification_completed': existing_attendance.verification_completed,
                            'status': existing_attendance.status.value
                        },
                        'conflict_type': 'duplicate_attendance',
                        'student_id': student.id,
                        'lecture_id': lecture_id,
                        'resolution_options': ['skip', 'overwrite', 'merge']
                    }
                    conflicts.append(conflict)
                    
                    if conflict_resolution == 'skip':
                        result.update({
                            'conflict_detected': True,
                            'error': 'سجل حضور موجود مسبقاً لهذه المحاضرة',
                            'existing_attendance_id': existing_attendance.id,
                            'action_taken': 'skipped'
                        })
                        failed_uploads += 1
                        results.append(result)
                        continue
                    
                    elif conflict_resolution == 'overwrite':
                        # Update existing record
                        existing_attendance.check_in_time = check_in_time
                        existing_attendance.recorded_latitude = recorded_lat
                        existing_attendance.recorded_longitude = recorded_lng
                        existing_attendance.recorded_altitude = recorded_altitude
                        existing_attendance.gps_accuracy = gps_accuracy
                        existing_attendance.location_verified = location_verified
                        existing_attendance.qr_verified = qr_verified
                        existing_attendance.face_verified = face_verified
                        existing_attendance.verification_completed = (location_verified and qr_verified and face_verified)
                        existing_attendance.device_info = device_info
                        existing_attendance.updated_at = datetime.utcnow()
                        
                        if sync_timestamp:
                            existing_attendance.synced_at = datetime.fromisoformat(sync_timestamp.replace('Z', '+00:00'))
                        
                        result.update({
                            'success': True,
                            'attendance_id': existing_attendance.id,
                            'action_taken': 'overwritten',
                            'conflict_detected': True
                        })
                        successful_uploads += 1
                        results.append(result)
                        continue
                    
                    elif conflict_resolution == 'merge':
                        # Merge verification results (keep best results)
                        existing_attendance.location_verified = existing_attendance.location_verified or location_verified
                        existing_attendance.qr_verified = existing_attendance.qr_verified or qr_verified
                        existing_attendance.face_verified = existing_attendance.face_verified or face_verified
                        existing_attendance.verification_completed = (
                            existing_attendance.location_verified and 
                            existing_attendance.qr_verified and 
                            existing_attendance.face_verified
                        )
                        
                        # Use most accurate GPS data
                        if gps_accuracy < existing_attendance.gps_accuracy:
                            existing_attendance.recorded_latitude = recorded_lat
                            existing_attendance.recorded_longitude = recorded_lng
                            existing_attendance.gps_accuracy = gps_accuracy
                        
                        # Use earlier check-in time
                        if check_in_time < existing_attendance.check_in_time:
                            existing_attendance.check_in_time = check_in_time
                        
                        existing_attendance.updated_at = datetime.utcnow()
                        
                        result.update({
                            'success': True,
                            'attendance_id': existing_attendance.id,
                            'action_taken': 'merged',
                            'conflict_detected': True
                        })
                        successful_uploads += 1
                        results.append(result)
                        continue
                
                # 8. Create new attendance record
                attendance_record = AttendanceRecord(
                    student_id=student.id,
                    lecture_id=lecture_id,
                    qr_session_id=qr_session_id,
                    
                    # Verification status
                    location_verified=location_verified,
                    qr_verified=qr_verified,
                    face_verified=face_verified,
                    verification_completed=(location_verified and qr_verified and face_verified),
                    
                    # Location data
                    recorded_latitude=recorded_lat,
                    recorded_longitude=recorded_lng,
                    recorded_altitude=recorded_altitude,
                    gps_accuracy=gps_accuracy,
                    
                    # Timing
                    check_in_time=check_in_time,
                    verification_started_at=check_in_time,
                    
                    # Device and metadata
                    device_info=device_info,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', ''),
                    
                    # Sync information
                    is_synced=True,
                    local_id=record_data.get('local_id'),
                    batch_upload_id=data.get('batch_id'),
                    offline_duration_hours=offline_duration
                )
                
                if sync_timestamp:
                    attendance_record.synced_at = datetime.fromisoformat(sync_timestamp.replace('Z', '+00:00'))
                
                # Determine attendance type based on timing
                if lecture.is_late_attendance(check_in_time):
                    attendance_record.attendance_type = AttendanceTypeEnum.LATE
                else:
                    attendance_record.attendance_type = AttendanceTypeEnum.ON_TIME
                
                # Set initial status
                if attendance_record.verification_completed:
                    attendance_record.status = AttendanceStatusEnum.VERIFIED
                else:
                    attendance_record.status = AttendanceStatusEnum.PENDING
                
                # Add verification details if available
                if verification_details:
                    attendance_record.verification_metadata = verification_details
                
                db.session.add(attendance_record)
                db.session.flush()  # Get ID without committing
                
                result.update({
                    'success': True,
                    'attendance_id': attendance_record.id,
                    'verification_completed': attendance_record.verification_completed,
                    'attendance_type': attendance_record.attendance_type.value,
                    'status': attendance_record.status.value,
                    'action_taken': 'created'
                })
                successful_uploads += 1
                
            except ValueError as ve:
                result['error'] = str(ve)
                failed_uploads += 1
            except Exception as e:
                result['error'] = f'خطأ غير متوقع: {str(e)}'
                failed_uploads += 1
            
            results.append(result)
        
        # 9. Commit successful records
        if successful_uploads > 0:
            try:
                db.session.commit()
                logging.info(f'Batch attendance upload by student {student.university_id}: {successful_uploads} successful, {failed_uploads} failed, {len(conflicts)} conflicts')
            except Exception as e:
                db.session.rollback()
                return jsonify(error_response('DATABASE_ERROR', f'خطأ في حفظ سجلات الحضور: {str(e)}')), 500
        else:
            db.session.rollback()
        
        # 10. Generate comprehensive summary
        summary = {
            'total_records': len(results),
            'successful': successful_uploads,
            'failed': failed_uploads,
            'conflicts': len(conflicts),
            'success_rate': round((successful_uploads / len(results)) * 100, 2) if results else 0,
            'validation_level': validation_level,
            'conflict_resolution': conflict_resolution,
            'offline_duration': offline_duration,
            'warnings_count': sum(len(r.get('warnings', [])) for r in results)
        }
        
        # Add performance metrics
        processing_time = (datetime.utcnow() - g.start_time).total_seconds() if hasattr(g, 'start_time') else 0
        summary['processing_time_seconds'] = round(processing_time, 2)
        summary['records_per_second'] = round(len(results) / max(processing_time, 0.1), 2)
        
        response_data = {
            'upload_results': results,
            'conflicts': conflicts,
            'summary': summary,
            'recommendations': generate_upload_recommendations(results, conflicts)
        }
        
        message = f'تم رفع {successful_uploads} سجل حضور بنجاح'
        if conflicts:
            message += f' مع {len(conflicts)} تعارض'
        
        return jsonify(batch_response(response_data, summary, message))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Batch attendance upload error: {str(e)}', exc_info=True)
        return jsonify(error_response('BATCH_UPLOAD_ERROR', 'حدث خطأ أثناء رفع سجلات الحضور')), 500

# ============================================================================
# CONFLICT RESOLUTION - حل التعارضات
# ============================================================================

@core_ops_bp.route('/attendance/resolve-conflicts', methods=['POST'])
@jwt_required
@require_permission('update_attendance')
def resolve_conflicts():
    """
    POST /api/attendance/resolve-conflicts
    Resolve attendance data conflicts with comprehensive strategies
    حل تعارضات بيانات الحضور مع استراتيجيات شاملة
    """
    try:
        # 1. Validate input
        data = request.get_json()
        if not data or 'conflicts' not in data:
            return jsonify(error_response('INVALID_INPUT', 'قائمة التعارضات مطلوبة')), 400
        
        conflicts_data = data['conflicts']
        if not isinstance(conflicts_data, list):
            return jsonify(error_response('INVALID_FORMAT', 'التعارضات يجب أن تكون مصفوفة')), 400
        
        # 2. Validate bulk operation limit
        bulk_limit_error = validate_bulk_operation_limit(conflicts_data, max_items=50)
        if bulk_limit_error:
            return jsonify(bulk_limit_error), 400
        
        # 3. Get current user and verify permissions
        user = get_current_user()
        is_admin = user.role.value == 'admin'
        is_teacher = user.role.value == 'teacher'
        is_student = user.role.value == 'student'
        
        # Students can only resolve their own conflicts
        student = user.get_student_profile() if is_student else None
        teacher = user.get_teacher_profile() if is_teacher else None
        
        # 4. Process each conflict resolution
        results = []
        successful_resolutions = 0
        failed_resolutions = 0
        
        for index, conflict_data in enumerate(conflicts_data):
            result = {
                'index': index,
                'success': False,
                'error': None,
                'resolution_action': None,
                'attendance_id': None,
                'conflict_details': {}
            }
            
            try:
                # Validate conflict data structure
                required_fields = ['student_id', 'lecture_id', 'resolution_strategy']
                missing_fields = [field for field in required_fields if field not in conflict_data]
                if missing_fields:
                    raise ValueError(f'حقول مطلوبة مفقودة: {", ".join(missing_fields)}')
                
                student_id = int(conflict_data['student_id'])
                lecture_id = int(conflict_data['lecture_id'])
                resolution_strategy = conflict_data['resolution_strategy']
                
                # Validate resolution strategy
                valid_strategies = [
                    'keep_local', 'keep_server', 'merge', 'manual_review', 
                    'use_best_verification', 'use_earliest_time', 'use_latest_time',
                    'teacher_override', 'admin_override'
                ]
                if resolution_strategy not in valid_strategies:
                    raise ValueError(f'استراتيجية حل غير صحيحة: {resolution_strategy}')
                
                # Check permissions for resolution strategy
                if resolution_strategy == 'teacher_override' and not (is_teacher or is_admin):
                    raise ValueError('صلاحيات مدرس مطلوبة لهذه الاستراتيجية')
                
                if resolution_strategy == 'admin_override' and not is_admin:
                    raise ValueError('صلاحيات إدارية مطلوبة لهذه الاستراتيجية')
                
                # Students can only resolve their own conflicts
                if is_student and student_id != student.id:
                    raise ValueError('يمكن للطالب حل تعارضاته فقط')
                
                # Teachers can only resolve conflicts for their lectures
                if is_teacher:
                    lecture = Lecture.query.get(lecture_id)
                    if not lecture or (lecture.schedule and lecture.schedule.teacher_id != teacher.id):
                        raise ValueError('يمكن للمدرس حل تعارضات محاضراته فقط')
                
                # Find existing attendance record
                existing_record = AttendanceRecord.query.filter_by(
                    student_id=student_id,
                    lecture_id=lecture_id
                ).first()
                
                if not existing_record:
                    raise ValueError('سجل الحضور الأصلي غير موجود')
                
                # Get local record data if provided
                local_data = conflict_data.get('local_record', {})
                resolution_notes = conflict_data.get('notes', '')
                
                # Store original values for comparison
                original_values = {
                    'check_in_time': existing_record.check_in_time,
                    'location_verified': existing_record.location_verified,
                    'qr_verified': existing_record.qr_verified,
                    'face_verified': existing_record.face_verified,
                    'status': existing_record.status
                }
                
                # Apply resolution strategy
                changes_made = []
                
                if resolution_strategy == 'keep_local':
                    # Replace server record with local data
                    if 'recorded_latitude' in local_data:
                        existing_record.recorded_latitude = float(local_data['recorded_latitude'])
                        changes_made.append('latitude')
                    
                    if 'recorded_longitude' in local_data:
                        existing_record.recorded_longitude = float(local_data['recorded_longitude'])
                        changes_made.append('longitude')
                    
                    if 'check_in_time' in local_data:
                        new_time = datetime.fromisoformat(local_data['check_in_time'].replace('Z', '+00:00'))
                        existing_record.check_in_time = new_time
                        changes_made.append('check_in_time')
                    
                    if 'location_verified' in local_data:
                        existing_record.location_verified = bool(local_data['location_verified'])
                        changes_made.append('location_verified')
                    
                    if 'qr_verified' in local_data:
                        existing_record.qr_verified = bool(local_data['qr_verified'])
                        changes_made.append('qr_verified')
                    
                    if 'face_verified' in local_data:
                        existing_record.face_verified = bool(local_data['face_verified'])
                        changes_made.append('face_verified')
                    
                    result['resolution_action'] = 'replaced_with_local'
                    
                elif resolution_strategy == 'keep_server':
                    # Keep server record as is, just mark as resolved
                    result['resolution_action'] = 'kept_server'
                    
                elif resolution_strategy == 'merge':
                    # Merge data intelligently
                    
                    # Use best verification results (OR logic)
                    if local_data.get('location_verified') and not existing_record.location_verified:
                        existing_record.location_verified = True
                        changes_made.append('improved_location_verification')
                    
                    if local_data.get('qr_verified') and not existing_record.qr_verified:
                        existing_record.qr_verified = True
                        changes_made.append('improved_qr_verification')
                    
                    if local_data.get('face_verified') and not existing_record.face_verified:
                        existing_record.face_verified = True
                        changes_made.append('improved_face_verification')
                    
                    # Use more accurate GPS data (if accuracy provided)
                    local_accuracy = local_data.get('gps_accuracy', float('inf'))
                    server_accuracy = existing_record.gps_accuracy or float('inf')
                    
                    if local_accuracy < server_accuracy and 'recorded_latitude' in local_data:
                        existing_record.recorded_latitude = float(local_data['recorded_latitude'])
                        existing_record.recorded_longitude = float(local_data['recorded_longitude'])
                        existing_record.gps_accuracy = local_accuracy
                        changes_made.append('improved_gps_accuracy')
                    
                    # Use earlier check-in time (student's benefit)
                    if 'check_in_time' in local_data:
                        local_time = datetime.fromisoformat(local_data['check_in_time'].replace('Z', '+00:00'))
                        if local_time < existing_record.check_in_time:
                            existing_record.check_in_time = local_time
                            changes_made.append('used_earlier_time')
                    
                    result['resolution_action'] = 'merged_data'
                    
                elif resolution_strategy == 'use_best_verification':
                    # Use the record with better verification completion
                    local_verification_score = sum([
                        local_data.get('location_verified', False),
                        local_data.get('qr_verified', False),
                        local_data.get('face_verified', False)
                    ])
                    
                    server_verification_score = sum([
                        existing_record.location_verified,
                        existing_record.qr_verified,
                        existing_record.face_verified
                    ])
                    
                    if local_verification_score > server_verification_score:
                        # Use local verification data
                        existing_record.location_verified = local_data.get('location_verified', False)
                        existing_record.qr_verified = local_data.get('qr_verified', False)
                        existing_record.face_verified = local_data.get('face_verified', False)
                        changes_made.append('used_better_verification')
                    
                    result['resolution_action'] = 'used_best_verification'
                    
                elif resolution_strategy == 'use_earliest_time':
                    if 'check_in_time' in local_data:
                        local_time = datetime.fromisoformat(local_data['check_in_time'].replace('Z', '+00:00'))
                        if local_time < existing_record.check_in_time:
                            existing_record.check_in_time = local_time
                            changes_made.append('used_earlier_time')
                    
                    result['resolution_action'] = 'used_earliest_time'
                    
                elif resolution_strategy == 'use_latest_time':
                    if 'check_in_time' in local_data:
                        local_time = datetime.fromisoformat(local_data['check_in_time'].replace('Z', '+00:00'))
                        if local_time > existing_record.check_in_time:
                            existing_record.check_in_time = local_time
                            changes_made.append('used_later_time')
                    
                    result['resolution_action'] = 'used_latest_time'
                    
                elif resolution_strategy == 'manual_review':
                    # Mark for manual review
                    existing_record.status = AttendanceStatusEnum.UNDER_REVIEW
                    existing_record.notes = f"تعارض في البيانات - يحتاج مراجعة يدوية في {datetime.utcnow().isoformat()}"
                    if resolution_notes:
                        existing_record.notes += f"\nملاحظات: {resolution_notes}"
                    changes_made.append('marked_for_review')
                    
                    result['resolution_action'] = 'marked_for_review'
                    
                elif resolution_strategy in ['teacher_override', 'admin_override']:
                    # Allow teacher/admin to set specific values
                    override_data = conflict_data.get('override_values', {})
                    
                    for field, value in override_data.items():
                        if field in ['location_verified', 'qr_verified', 'face_verified']:
                            setattr(existing_record, field, bool(value))
                            changes_made.append(f'override_{field}')
                        elif field == 'status':
                            existing_record.status = AttendanceStatusEnum(value)
                            changes_made.append('override_status')
                        elif field == 'attendance_type':
                            existing_record.attendance_type = AttendanceTypeEnum(value)
                            changes_made.append('override_attendance_type')
                    
                    # Add override note
                    override_note = f"تم التدخل من قبل {user.role.value} {user.full_name} في {datetime.utcnow().isoformat()}"
                    if resolution_notes:
                        override_note += f"\nسبب التدخل: {resolution_notes}"
                    
                    existing_record.notes = (existing_record.notes or '') + '\n' + override_note
                    changes_made.append('admin_teacher_override')
                    
                    result['resolution_action'] = resolution_strategy
                
                # Recalculate verification completion after changes
                existing_record.verification_completed = (
                    existing_record.location_verified and 
                    existing_record.qr_verified and 
                    existing_record.face_verified
                )
                
                # Update status if verification is now complete
                if existing_record.verification_completed and existing_record.status == AttendanceStatusEnum.PENDING:
                    existing_record.status = AttendanceStatusEnum.VERIFIED
                    changes_made.append('auto_verified')
                
                # Update timestamp and conflict resolution info
                existing_record.updated_at = datetime.utcnow()
                existing_record.conflict_resolved_at = datetime.utcnow()
                existing_record.conflict_resolved_by = user.id
                existing_record.conflict_resolution_strategy = resolution_strategy
                
                # Store conflict resolution metadata
                conflict_metadata = {
                    'original_values': original_values,
                    'changes_made': changes_made,
                    'resolution_strategy': resolution_strategy,
                    'resolved_by': {
                        'user_id': user.id,
                        'username': user.username,
                        'role': user.role.value
                    },
                    'resolved_at': datetime.utcnow().isoformat(),
                    'notes': resolution_notes
                }
                
                existing_record.conflict_resolution_metadata = conflict_metadata
                
                result.update({
                    'success': True,
                    'attendance_id': existing_record.id,
                    'changes_made': changes_made,
                    'final_status': existing_record.status.value,
                    'verification_completed': existing_record.verification_completed,
                    'conflict_details': {
                        'original_values': original_values,
                        'final_values': {
                            'check_in_time': existing_record.check_in_time.isoformat(),
                            'location_verified': existing_record.location_verified,
                            'qr_verified': existing_record.qr_verified,
                            'face_verified': existing_record.face_verified,
                            'status': existing_record.status.value
                        }
                    }
                })
                successful_resolutions += 1
                
            except ValueError as ve:
                result['error'] = str(ve)
                failed_resolutions += 1
            except Exception as e:
                result['error'] = f'خطأ غير متوقع: {str(e)}'
                failed_resolutions += 1
            
            results.append(result)
        
        # 5. Commit changes
        if successful_resolutions > 0:
            try:
                db.session.commit()
                logging.info(f'Conflict resolution by {user.username}: {successful_resolutions} resolved, {failed_resolutions} failed')
            except Exception as e:
                db.session.rollback()
                return jsonify(error_response('DATABASE_ERROR', f'خطأ في حفظ حلول التعارضات: {str(e)}')), 500
        else:
            db.session.rollback()
        
        # 6. Generate summary and recommendations
        summary = {
            'total_conflicts': len(results),
            'resolved': successful_resolutions,
            'failed': failed_resolutions,
            'resolution_rate': round((successful_resolutions / len(results)) * 100, 2) if results else 0,
            'strategies_used': list(set(r.get('resolution_action') for r in results if r.get('resolution_action'))),
            'resolver_info': {
                'user_id': user.id,
                'username': user.username,
                'role': user.role.value
            }
        }
        
        response_data = {
            'results': results,
            'summary': summary,
            'recommendations': generate_conflict_resolution_recommendations(results)
        }
        
        message = f'تم حل {successful_resolutions} تعارض بنجاح'
        return jsonify(batch_response(response_data, summary, message))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Conflict resolution error: {str(e)}', exc_info=True)
        return jsonify(error_response('CONFLICT_RESOLUTION_ERROR', 'حدث خطأ أثناء حل التعارضات')), 500

# ============================================================================
# SYNC STATUS MANAGEMENT - إدارة حالة المزامنة
# ============================================================================

@core_ops_bp.route('/attendance/sync-status', methods=['GET'])
@jwt_required
@require_permission('read_own_attendance')
def get_sync_status():
    """
    GET /api/attendance/sync-status
    Get comprehensive attendance synchronization status
    حالة مزامنة بيانات الحضور الشاملة
    """
    try:
        # 1. Get current user (should be student for personal sync status)
        user = get_current_user()
        if user.role.value != 'student':
            return jsonify(error_response('UNAUTHORIZED', 'هذا الـ API مخصص للطلاب فقط')), 403
        
        student = user.get_student_profile()
        if not student:
            return jsonify(not_found_response('ملف الطالب')), 404
        
        # 2. Get query parameters for filtering
        since_date = request.args.get('since_date')
        include_resolved = request.args.get('include_resolved', 'false').lower() == 'true'
        detailed_analysis = request.args.get('detailed_analysis', 'false').lower() == 'true'
        
        if since_date:
            try:
                since_datetime = datetime.fromisoformat(since_date.replace('Z', '+00:00'))
            except ValueError:
                return jsonify(error_response('INVALID_DATE', 'تنسيق التاريخ غير صحيح')), 400
        else:
            # Default to last 30 days
            since_datetime = datetime.utcnow() - timedelta(days=30)
        
        # 3. Get attendance records with comprehensive filtering
        base_query = AttendanceRecord.query.filter_by(student_id=student.id)
        
        # Apply date filter
        attendance_query = base_query.filter(
            AttendanceRecord.check_in_time >= since_datetime
        )
        
        # Get all records for analysis
        all_records = attendance_query.all()
        
        # 4. Calculate comprehensive statistics
        
        # Basic counts
        total_records = len(all_records)
        synced_records = sum(1 for r in all_records if r.is_synced)
        unsynced_records = total_records - synced_records
        
        # Status breakdown
        status_counts = {
            'pending': sum(1 for r in all_records if r.status == AttendanceStatusEnum.PENDING),
            'verified': sum(1 for r in all_records if r.status == AttendanceStatusEnum.VERIFIED),
            'rejected': sum(1 for r in all_records if r.status == AttendanceStatusEnum.REJECTED),
            'under_review': sum(1 for r in all_records if r.status == AttendanceStatusEnum.UNDER_REVIEW)
        }
        
        # Verification statistics
        verification_stats = {
            'completed_verification': sum(1 for r in all_records if r.verification_completed),
            'incomplete_verification': sum(1 for r in all_records if not r.verification_completed),
            'location_verified': sum(1 for r in all_records if r.location_verified),
            'qr_verified': sum(1 for r in all_records if r.qr_verified),
            'face_verified': sum(1 for r in all_records if r.face_verified)
        }
        
        # Sync-specific statistics
        sync_attempts = sum(r.sync_attempts or 0 for r in all_records)
        failed_sync_attempts = sum(1 for r in all_records if (r.sync_attempts or 0) > 0 and not r.is_synced)
        
        # Conflict analysis
        conflict_records = [r for r in all_records if r.conflict_resolution_metadata]
        resolved_conflicts = len(conflict_records) if include_resolved else 0
        
        # Get active conflicts (unresolved)
        active_conflicts = []
        unresolved_conflicts = base_query.filter(
            AttendanceRecord.conflict_resolution_metadata.is_(None),
            AttendanceRecord.status == AttendanceStatusEnum.UNDER_REVIEW
        ).all()
        
        for record in unresolved_conflicts:
            # Check for potential conflicts with other records
            potential_conflicts = base_query.filter(
                AttendanceRecord.lecture_id == record.lecture_id,
                AttendanceRecord.id != record.id
            ).all()
            
            if potential_conflicts:
                active_conflicts.append({
                    'attendance_id': record.id,
                    'lecture_id': record.lecture_id,
                    'conflict_type': 'duplicate_attendance',
                    'description': 'سجلات متعددة لنفس المحاضرة',
                    'check_in_time': record.check_in_time.isoformat(),
                    'status': record.status.value,
                    'requires_action': True,
                    'suggested_actions': ['resolve_conflicts', 'manual_review']
                })
        
        # 5. Get records that need attention
        attention_records = []
        
        # Records with sync failures
        sync_failure_records = [r for r in all_records if (r.sync_attempts or 0) > 3 and not r.is_synced]
        for record in sync_failure_records:
            attention_records.append({
                'id': record.id,
                'lecture_id': record.lecture_id,
                'issue_type': 'sync_failure',
                'description': f'فشل في المزامنة ({record.sync_attempts} محاولات)',
                'check_in_time': record.check_in_time.isoformat(),
                'requires_action': True,
                'priority': 'high'
            })
        
        # Records with incomplete verification
        incomplete_verification_records = [r for r in all_records if not r.verification_completed]
        for record in incomplete_verification_records:
            missing_verifications = []
            if not record.location_verified:
                missing_verifications.append('الموقع')
            if not record.qr_verified:
                missing_verifications.append('QR')
            if not record.face_verified:
                missing_verifications.append('الوجه')
            
            attention_records.append({
                'id': record.id,
                'lecture_id': record.lecture_id,
                'issue_type': 'incomplete_verification',
                'description': f'تحقق غير مكتمل: {", ".join(missing_verifications)}',
                'check_in_time': record.check_in_time.isoformat(),
                'requires_action': False,
                'priority': 'medium'
            })
        
        # 6. Calculate sync health score
        sync_health_score = 100
        
        if total_records > 0:
            sync_rate = (synced_records / total_records) * 100
            verification_rate = (verification_stats['completed_verification'] / total_records) * 100
            
            # Deduct points for issues
            if sync_rate < 90:
                sync_health_score -= (90 - sync_rate) * 0.5
            
            if verification_rate < 80:
                sync_health_score -= (80 - verification_rate) * 0.3
            
            if failed_sync_attempts > 5:
                sync_health_score -= min(20, failed_sync_attempts * 2)
            
            if len(active_conflicts) > 0:
                sync_health_score -= min(15, len(active_conflicts) * 5)
        
        sync_health_score = max(0, round(sync_health_score, 1))
        
        # Determine health status
        if sync_health_score >= 90:
            health_status = 'excellent'
        elif sync_health_score >= 75:
            health_status = 'good'
        elif sync_health_score >= 60:
            health_status = 'fair'
        elif sync_health_score >= 40:
            health_status = 'poor'
        else:
            health_status = 'critical'
        
        # 7. Prepare comprehensive response
        sync_status = {
            'student_info': {
                'university_id': student.university_id,
                'full_name': user.full_name,
                'section': student.section.value,
                'study_year': student.study_year
            },
            'sync_period': {
                'since_date': since_datetime.isoformat(),
                'until_date': datetime.utcnow().isoformat(),
                'total_days': (datetime.utcnow() - since_datetime).days
            },
            'sync_statistics': {
                'total_records': total_records,
                'synced_records': synced_records,
                'unsynced_records': unsynced_records,
                'sync_rate': round((synced_records / total_records) * 100, 2) if total_records > 0 else 100,
                'failed_sync_attempts': failed_sync_attempts,
                'total_sync_attempts': sync_attempts
            },
            'record_status': status_counts,
            'verification_status': {
                **verification_stats,
                'verification_rate': round((verification_stats['completed_verification'] / total_records) * 100, 2) if total_records > 0 else 0
            },
            'sync_health': {
                'status': health_status,
                'score': sync_health_score,
                'last_successful_sync': get_last_successful_sync_time(all_records),
                'next_sync_recommended': datetime.utcnow() + timedelta(hours=1)
            },
            'conflicts': {
                'active_conflicts': len(active_conflicts),
                'resolved_conflicts': resolved_conflicts,
                'conflict_details': active_conflicts
            },
            'attention_required': attention_records,
            'recommendations': []
        }
        
        # 8. Add detailed analysis if requested
        if detailed_analysis:
            sync_status['detailed_analysis'] = {
                'sync_patterns': analyze_sync_patterns(all_records),
                'verification_patterns': analyze_verification_patterns(all_records),
                'temporal_analysis': analyze_temporal_patterns(all_records),
                'performance_metrics': calculate_sync_performance_metrics(all_records)
            }
        
        # 9. Generate recommendations based on status
        sync_status['recommendations'] = generate_sync_recommendations(
            sync_status, attention_records, active_conflicts
        )
        
        # 10. Log sync status check
        logging.info(f'Sync status checked by student {student.university_id}: {health_status} (score: {sync_health_score})')
        
        return jsonify(success_response(sync_status))
        
    except Exception as e:
        logging.error(f'Sync status error: {str(e)}', exc_info=True)
        return jsonify(error_response('SYNC_STATUS_ERROR', 'حدث خطأ أثناء فحص حالة المزامنة')), 500

# ============================================================================
# HELPER FUNCTIONS - الدوال المساعدة
# ============================================================================

def generate_upload_recommendations(results, conflicts):
    """Generate recommendations based on upload results"""
    recommendations = []
    
    # High failure rate
    failed_count = sum(1 for r in results if not r['success'])
    if failed_count > len(results) * 0.3:  # More than 30% failed
        recommendations.append({
            'type': 'high_failure_rate',
            'message': f'معدل فشل مرتفع ({failed_count}/{len(results)}). تحقق من جودة البيانات.',
            'priority': 'high'
        })
    
    # GPS accuracy issues
    low_accuracy_count = sum(1 for r in results if 'دقة GPS منخفضة' in str(r.get('warnings', [])))
    if low_accuracy_count > 0:
        recommendations.append({
            'type': 'gps_accuracy',
            'message': f'{low_accuracy_count} سجل بدقة GPS منخفضة. استخدم الـ WiFi للحصول على دقة أفضل.',
            'priority': 'medium'
        })
    
    # Conflicts detected
    if conflicts:
        recommendations.append({
            'type': 'conflicts',
            'message': f'{len(conflicts)} تعارض مكتشف. راجع استراتيجية حل التعارضات.',
            'priority': 'medium'
        })
    
    return recommendations

def generate_conflict_resolution_recommendations(results):
    """Generate recommendations for conflict resolution"""
    recommendations = []
    
    failed_resolutions = sum(1 for r in results if not r['success'])
    if failed_resolutions > 0:
        recommendations.append({
            'type': 'resolution_failures',
            'message': f'{failed_resolutions} تعارض فشل في حله. راجع الأخطاء وأعد المحاولة.',
            'priority': 'high'
        })
    
    manual_reviews = sum(1 for r in results if r.get('resolution_action') == 'marked_for_review')
    if manual_reviews > 0:
        recommendations.append({
            'type': 'manual_review_needed',
            'message': f'{manual_reviews} سجل يحتاج مراجعة يدوية من المدرس أو الإدارة.',
            'priority': 'medium'
        })
    
    return recommendations

def get_last_successful_sync_time(records):
    """Get the timestamp of the last successful sync"""
    synced_records = [r for r in records if r.is_synced and r.synced_at]
    if synced_records:
        return max(r.synced_at for r in synced_records).isoformat()
    return None

def analyze_sync_patterns(records):
    """Analyze synchronization patterns"""
    if not records:
        return {}
    
    sync_success_rate = sum(1 for r in records if r.is_synced) / len(records) * 100
    
    return {
        'overall_sync_rate': round(sync_success_rate, 2),
        'avg_sync_attempts': round(sum(r.sync_attempts or 0 for r in records) / len(records), 2),
        'sync_failure_rate': round((1 - sync_success_rate / 100) * 100, 2)
    }

def analyze_verification_patterns(records):
    """Analyze verification patterns"""
    if not records:
        return {}
    
    total = len(records)
    return {
        'location_success_rate': round(sum(1 for r in records if r.location_verified) / total * 100, 2),
        'qr_success_rate': round(sum(1 for r in records if r.qr_verified) / total * 100, 2),
        'face_success_rate': round(sum(1 for r in records if r.face_verified) / total * 100, 2),
        'complete_verification_rate': round(sum(1 for r in records if r.verification_completed) / total * 100, 2)
    }

def analyze_temporal_patterns(records):
    """Analyze temporal patterns in attendance"""
    if not records:
        return {}
    
    # Group by day of week
    from collections import defaultdict
    by_day = defaultdict(int)
    
    for record in records:
        day_name = record.check_in_time.strftime('%A')
        by_day[day_name] += 1
    
    return {
        'attendance_by_day': dict(by_day),
        'most_active_day': max(by_day.items(), key=lambda x: x[1])[0] if by_day else None,
        'least_active_day': min(by_day.items(), key=lambda x: x[1])[0] if by_day else None
    }

def calculate_sync_performance_metrics(records):
    """Calculate performance metrics for sync operations"""
    if not records:
        return {}
    
    offline_records = [r for r in records if r.offline_duration_hours and r.offline_duration_hours > 0]
    
    return {
        'total_records': len(records),
        'offline_records': len(offline_records),
        'avg_offline_duration': round(sum(r.offline_duration_hours for r in offline_records) / len(offline_records), 2) if offline_records else 0,
        'max_offline_duration': max(r.offline_duration_hours for r in offline_records) if offline_records else 0
    }

def generate_sync_recommendations(sync_status, attention_records, active_conflicts):
    """Generate comprehensive sync recommendations"""
    recommendations = []
    
    # Sync rate recommendations
    sync_rate = sync_status['sync_statistics']['sync_rate']
    if sync_rate < 90:
        recommendations.append({
            'type': 'sync_required',
            'message': f'معدل المزامنة منخفض ({sync_rate:.1f}%). يُنصح بالمزامنة فوراً.',
            'priority': 'high' if sync_rate < 70 else 'medium'
        })
    
    # Verification recommendations
    verification_rate = sync_status['verification_status']['verification_rate']
    if verification_rate < 80:
        recommendations.append({
            'type': 'verification_incomplete',
            'message': f'معدل التحقق منخفض ({verification_rate:.1f}%). تأكد من إكمال جميع خطوات التحقق.',
            'priority': 'medium'
        })
    
    # Conflict recommendations
    if active_conflicts:
        recommendations.append({
            'type': 'conflicts_active',
            'message': f'{len(active_conflicts)} تعارض نشط يحتاج حل. استخدم واجهة حل التعارضات.',
            'priority': 'high'
        })
    
    # Attention records recommendations
    high_priority_issues = sum(1 for r in attention_records if r.get('priority') == 'high')
    if high_priority_issues > 0:
        recommendations.append({
            'type': 'high_priority_issues',
            'message': f'{high_priority_issues} مشكلة ذات أولوية عالية تحتاج انتباه فوري.',
            'priority': 'high'
        })
    
    # Health score recommendations
    health_score = sync_status['sync_health']['score']
    if health_score < 60:
        recommendations.append({
            'type': 'poor_sync_health',
            'message': f'صحة المزامنة ضعيفة ({health_score}%). راجع جميع المشاكل واتصل بالدعم.',
            'priority': 'critical'
        })
    
    return recommendations

# Error handlers specific to core operations blueprint
@core_ops_bp.errorhandler(422)
def core_ops_validation_error(error):
    """Handle validation errors in core operations"""
    return jsonify(error_response(
        'CORE_OPS_VALIDATION_ERROR',
        'بيانات العملية غير صحيحة أو غير مكتملة'
    )), 422

@core_ops_bp.errorhandler(409)
def core_ops_conflict_error(error):
    """Handle conflict errors in core operations"""
    return jsonify(error_response(
        'CORE_OPS_CONFLICT',
        'تعارض في البيانات. استخدم واجهة حل التعارضات.'
    )), 409