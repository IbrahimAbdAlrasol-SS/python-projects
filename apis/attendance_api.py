"""
✅ Attendance/Core Operations APIs - مجموعة عمليات الحضور الأساسية
Group 3: Core Operations APIs (4 endpoints)
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
    validation_error_response
)
from utils.validation_helpers import (
    validate_required_fields, validate_bulk_operation_limit,
    validate_ids_list
)
from config.database import db
from datetime import datetime, timedelta
import logging
import uuid

# Create blueprint
attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

@attendance_bp.route('/generate-qr/<int:lecture_id>', methods=['POST'])
@jwt_required
@require_permission('generate_qr')
def generate_qr_code(lecture_id):
    """
    POST /api/lectures/generate-qr/<id>
    Generate QR code for lecture attendance
    توليد رمز QR لحضور المحاضرة
    """
    try:
        # 1. Find lecture
        lecture = Lecture.query.get(lecture_id)
        if not lecture:
            return jsonify(error_response('LECTURE_NOT_FOUND', f'محاضرة غير موجودة: {lecture_id}')), 404
        
        # 2. Verify teacher permission
        user = get_current_user()
        teacher = user.get_teacher_profile()
        
        if not teacher:
            return jsonify(error_response('NOT_TEACHER', 'هذا الـ API مخصص للمدرسين فقط')), 403
        
        # Verify teacher owns this lecture
        if lecture.schedule.teacher_id != teacher.id:
            return jsonify(error_response('UNAUTHORIZED_LECTURE', 'غير مصرح لك بإدارة هذه المحاضرة')), 403
        
        # 3. Validate lecture status
        if lecture.status not in [LectureStatusEnum.SCHEDULED, LectureStatusEnum.ACTIVE]:
            return jsonify(error_response(
                'INVALID_LECTURE_STATUS',
                f'لا يمكن توليد QR للمحاضرة في الحالة: {lecture.status.value}'
            )), 400
        
        # 4. Check if QR generation is allowed
        if not lecture.can_generate_qr():
            return jsonify(error_response('QR_NOT_ALLOWED', 'توليد QR غير مسموح لهذه المحاضرة')), 400
        
        # 5. Get QR settings from request
        data = request.get_json() or {}
        duration_minutes = int(data.get('duration_minutes', 15))  # Default 15 minutes
        max_usage = int(data.get('max_usage_count', 1000))        # Default 1000 uses
        
        # Validate duration
        if not (1 <= duration_minutes <= 60):
            return jsonify(error_response('INVALID_DURATION', 'مدة QR يجب أن تكون بين 1 و 60 دقيقة')), 400
        
        # 6. Check for existing active QR sessions
        existing_qr = QRSession.query.filter_by(
            lecture_id=lecture_id,
            is_active=True,
            status=QRStatusEnum.ACTIVE
        ).filter(
            QRSession.expires_at > datetime.utcnow()
        ).first()
        
        if existing_qr:
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
                        'status': 'existing'
                    },
                    'lecture_info': {
                        'id': lecture.id,
                        'topic': lecture.topic,
                        'subject_name': lecture.schedule.subject.name if lecture.schedule and lecture.schedule.subject else None,
                        'room_name': lecture.schedule.room.name if lecture.schedule and lecture.schedule.room else None
                    }
                }, message='QR موجود مسبقاً ولا يزال صالحاً'))
        
        # 7. Start lecture if not already started
        if lecture.status == LectureStatusEnum.SCHEDULED:
            lecture.start_lecture(teacher.user.id)
        
        # 8. Create new QR session
        qr_session, encryption_key = QRSession.create_for_lecture(
            lecture_id=lecture_id,
            generated_by_teacher_id=teacher.id,
            duration_minutes=duration_minutes,
            max_usage_count=max_usage,
            allow_multiple_scans=True
        )
        
        # 9. Log QR generation
        logging.info(f'QR generated for lecture {lecture_id} by teacher {teacher.employee_id}')
        
        # 10. Return QR session info
        return jsonify(success_response({
            'qr_session': {
                'id': qr_session.id,
                'session_id': qr_session.session_id,
                'generated_at': qr_session.generated_at.isoformat(),
                'expires_at': qr_session.expires_at.isoformat(),
                'time_remaining_seconds': int(duration_minutes * 60),
                'usage_count': 0,
                'max_usage_count': max_usage,
                'display_text': qr_session.qr_display_text,
                'status': 'new'
            },
            'qr_payload': qr_session.generate_qr_payload(),
            'encryption_key': encryption_key.decode(),  # For mobile app to store locally
            'lecture_info': {
                'id': lecture.id,
                'topic': lecture.topic,
                'status': lecture.status.value,
                'subject_name': lecture.schedule.subject.name if lecture.schedule and lecture.schedule.subject else None,
                'room_name': lecture.schedule.room.name if lecture.schedule and lecture.schedule.room else None,
                'section': lecture.schedule.section.value if lecture.schedule and lecture.schedule.section else None
            }
        }, message='تم توليد QR بنجاح')), 201
        
    except Exception as e:
        logging.error(f'QR generation error: {str(e)}', exc_info=True)
        return jsonify(error_response('QR_GENERATION_ERROR', 'حدث خطأ أثناء توليد QR')), 500

@attendance_bp.route('/batch-upload', methods=['POST'])
@jwt_required
@require_permission('submit_attendance')
def batch_upload_attendance():
    """
    POST /api/attendance/batch-upload
    Upload batch attendance records from mobile app
    رفع سجلات الحضور بشكل جماعي من التطبيق
    """
    try:
        # 1. Validate input
        data = request.get_json()
        if not data or 'attendance_records' not in data:
            return jsonify(error_response('INVALID_INPUT', 'سجلات الحضور مطلوبة')), 400
        
        attendance_records = data['attendance_records']
        if not isinstance(attendance_records, list):
            return jsonify(error_response('INVALID_FORMAT', 'سجلات الحضور يجب أن تكون مصفوفة')), 400
        
        # 2. Validate bulk limit
        bulk_limit_error = validate_bulk_operation_limit(attendance_records, max_items=100)
        if bulk_limit_error:
            return jsonify(bulk_limit_error), 400
        
        # 3. Get current user (should be student)
        user = get_current_user()
        if user.role.value != 'student':
            return jsonify(error_response('UNAUTHORIZED', 'هذا الـ API مخصص للطلاب فقط')), 403
        
        student = user.get_student_profile()
        if not student:
            return jsonify(error_response('STUDENT_NOT_FOUND', 'ملف الطالب غير موجود')), 404
        
        # 4. Process each attendance record
        results = []
        successful_uploads = 0
        failed_uploads = 0
        conflicts = []
        
        for index, record_data in enumerate(attendance_records):
            result = {
                'index': index,
                'local_id': record_data.get('local_id'),
                'success': False,
                'error': None,
                'attendance_id': None,
                'conflict_detected': False
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
                
                # Extract data
                lecture_id = int(record_data['lecture_id'])
                qr_session_id = record_data['qr_session_id']
                recorded_lat = float(record_data['recorded_latitude'])
                recorded_lng = float(record_data['recorded_longitude'])
                recorded_altitude = float(record_data.get('recorded_altitude', 0))
                check_in_time = datetime.fromisoformat(record_data['check_in_time'].replace('Z', '+00:00'))
                
                # Verification data
                location_verified = bool(record_data.get('location_verified', False))
                qr_verified = bool(record_data.get('qr_verified', False))
                face_verified = bool(record_data.get('face_verified', False))
                
                # Optional data
                device_info = record_data.get('device_info', {})
                gps_accuracy = float(record_data.get('gps_accuracy', 0))
                
                # 5. Check for existing attendance
                existing_attendance = AttendanceRecord.query.filter_by(
                    student_id=student.id,
                    lecture_id=lecture_id
                ).first()
                
                if existing_attendance:
                    # Conflict detected
                    conflict = {
                        'local_record': record_data,
                        'server_record': existing_attendance.to_dict(),
                        'conflict_type': 'duplicate_attendance',
                        'student_id': student.id,
                        'lecture_id': lecture_id
                    }
                    conflicts.append(conflict)
                    
                    result.update({
                        'conflict_detected': True,
                        'error': 'سجل حضور موجود مسبقاً لهذه المحاضرة',
                        'existing_attendance_id': existing_attendance.id
                    })
                    failed_uploads += 1
                    continue
                
                # 6. Verify lecture exists
                lecture = Lecture.query.get(lecture_id)
                if not lecture:
                    raise ValueError(f'محاضرة غير موجودة: {lecture_id}')
                
                # 7. Create attendance record
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
                    
                    # Device info
                    device_info=device_info,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', ''),
                    
                    # Status
                    status=AttendanceStatusEnum.VERIFIED if (location_verified and qr_verified and face_verified) else AttendanceStatusEnum.PENDING,
                    
                    # Determine attendance type
                    attendance_type=AttendanceTypeEnum.ON_TIME,  # Will be updated by business logic
                    
                    # Sync info
                    is_synced=True,
                    local_id=record_data.get('local_id')
                )
                
                # Determine if late
                if lecture.is_late_attendance(check_in_time):
                    attendance_record.attendance_type = AttendanceTypeEnum.LATE
                
                db.session.add(attendance_record)
                db.session.flush()  # Get ID without committing
                
                result.update({
                    'success': True,
                    'attendance_id': attendance_record.id,
                    'verification_completed': attendance_record.verification_completed,
                    'attendance_type': attendance_record.attendance_type.value
                })
                successful_uploads += 1
                
            except ValueError as ve:
                result['error'] = str(ve)
                failed_uploads += 1
            except Exception as e:
                result['error'] = f'خطأ غير متوقع: {str(e)}'
                failed_uploads += 1
            
            results.append(result)
        
        # 8. Commit successful records
        if successful_uploads > 0:
            try:
                db.session.commit()
                logging.info(f'Batch attendance upload: {successful_uploads} successful, {failed_uploads} failed by student {student.university_id}')
            except Exception as e:
                db.session.rollback()
                return jsonify(error_response('DATABASE_ERROR', f'خطأ في حفظ سجلات الحضور: {str(e)}')), 500
        else:
            db.session.rollback()
        
        # 9. Prepare response
        summary = {
            'total_records': len(results),
            'successful': successful_uploads,
            'failed': failed_uploads,
            'conflicts': len(conflicts),
            'success_rate': round((successful_uploads / len(results)) * 100, 2) if results else 0
        }
        
        response_data = {
            'upload_results': results,
            'conflicts': conflicts,
            'summary': summary
        }
        
        return jsonify(batch_response(response_data, summary))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Batch attendance upload error: {str(e)}', exc_info=True)
        return jsonify(error_response('BATCH_UPLOAD_ERROR', 'حدث خطأ أثناء رفع سجلات الحضور')), 500

@attendance_bp.route('/resolve-conflicts', methods=['POST'])
@jwt_required
@require_permission('update_attendance')
def resolve_conflicts():
    """
    POST /api/attendance/resolve-conflicts
    Resolve attendance data conflicts
    حل تعارضات بيانات الحضور
    """
    try:
        # 1. Validate input
        data = request.get_json()
        if not data or 'conflicts' not in data:
            return jsonify(error_response('INVALID_INPUT', 'قائمة التعارضات مطلوبة')), 400
        
        conflicts_data = data['conflicts']
        if not isinstance(conflicts_data, list):
            return jsonify(error_response('INVALID_FORMAT', 'التعارضات يجب أن تكون مصفوفة')), 400
        
        # 2. Process each conflict resolution
        results = []
        successful_resolutions = 0
        failed_resolutions = 0
        
        for index, conflict_data in enumerate(conflicts_data):
            result = {
                'index': index,
                'success': False,
                'error': None,
                'resolution_action': None
            }
            
            try:
                # Validate conflict data
                required_fields = ['student_id', 'lecture_id', 'resolution_strategy']
                missing_fields = [field for field in required_fields if field not in conflict_data]
                if missing_fields:
                    raise ValueError(f'حقول مطلوبة مفقودة: {", ".join(missing_fields)}')
                
                student_id = int(conflict_data['student_id'])
                lecture_id = int(conflict_data['lecture_id'])
                resolution_strategy = conflict_data['resolution_strategy']
                
                # Validate resolution strategy
                valid_strategies = ['keep_local', 'keep_server', 'merge', 'manual_review']
                if resolution_strategy not in valid_strategies:
                    raise ValueError(f'استراتيجية حل غير صحيحة: {resolution_strategy}')
                
                # Find existing attendance record
                existing_record = AttendanceRecord.query.filter_by(
                    student_id=student_id,
                    lecture_id=lecture_id
                ).first()
                
                if not existing_record:
                    raise ValueError('سجل الحضور الأصلي غير موجود')
                
                # Apply resolution strategy
                if resolution_strategy == 'keep_local':
                    # Replace server record with local data
                    local_data = conflict_data['local_record']
                    
                    # Update fields from local record
                    existing_record.recorded_latitude = float(local_data['recorded_latitude'])
                    existing_record.recorded_longitude = float(local_data['recorded_longitude'])
                    existing_record.check_in_time = datetime.fromisoformat(local_data['check_in_time'].replace('Z', '+00:00'))
                    existing_record.location_verified = bool(local_data.get('location_verified', False))
                    existing_record.qr_verified = bool(local_data.get('qr_verified', False))
                    existing_record.face_verified = bool(local_data.get('face_verified', False))
                    
                    # Recalculate verification completion
                    existing_record.verification_completed = (
                        existing_record.location_verified and 
                        existing_record.qr_verified and 
                        existing_record.face_verified
                    )
                    
                    result['resolution_action'] = 'replaced_with_local'
                    
                elif resolution_strategy == 'keep_server':
                    # Keep server record as is
                    result['resolution_action'] = 'kept_server'
                    
                elif resolution_strategy == 'merge':
                    # Merge data (keep best verification results)
                    local_data = conflict_data['local_record']
                    
                    # Use best verification results
                    existing_record.location_verified = existing_record.location_verified or bool(local_data.get('location_verified', False))
                    existing_record.qr_verified = existing_record.qr_verified or bool(local_data.get('qr_verified', False))
                    existing_record.face_verified = existing_record.face_verified or bool(local_data.get('face_verified', False))
                    
                    # Use most recent check-in time
                    local_time = datetime.fromisoformat(local_data['check_in_time'].replace('Z', '+00:00'))
                    if local_time > existing_record.check_in_time:
                        existing_record.check_in_time = local_time
                    
                    existing_record.verification_completed = (
                        existing_record.location_verified and 
                        existing_record.qr_verified and 
                        existing_record.face_verified
                    )
                    
                    result['resolution_action'] = 'merged_data'
                    
                elif resolution_strategy == 'manual_review':
                    # Mark for manual review
                    existing_record.status = AttendanceStatusEnum.UNDER_REVIEW
                    existing_record.notes = f"تعارض في البيانات - يحتاج مراجعة يدوية في {datetime.utcnow().isoformat()}"
                    
                    result['resolution_action'] = 'marked_for_review'
                
                # Update record timestamp
                existing_record.updated_at = datetime.utcnow()
                
                result.update({
                    'success': True,
                    'attendance_id': existing_record.id,
                    'final_status': existing_record.status.value,
                    'verification_completed': existing_record.verification_completed
                })
                successful_resolutions += 1
                
            except ValueError as ve:
                result['error'] = str(ve)
                failed_resolutions += 1
            except Exception as e:
                result['error'] = f'خطأ غير متوقع: {str(e)}'
                failed_resolutions += 1
            
            results.append(result)
        
        # 3. Commit changes
        if successful_resolutions > 0:
            try:
                db.session.commit()
                logging.info(f'Conflict resolution: {successful_resolutions} resolved, {failed_resolutions} failed')
            except Exception as e:
                db.session.rollback()
                return jsonify(error_response('DATABASE_ERROR', f'خطأ في حفظ حلول التعارضات: {str(e)}')), 500
        else:
            db.session.rollback()
        
        # 4. Summary
        summary = {
            'total_conflicts': len(results),
            'resolved': successful_resolutions,
            'failed': failed_resolutions,
            'resolution_rate': round((successful_resolutions / len(results)) * 100, 2) if results else 0
        }
        
        return jsonify(batch_response(results, summary))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Conflict resolution error: {str(e)}', exc_info=True)
        return jsonify(error_response('CONFLICT_RESOLUTION_ERROR', 'حدث خطأ أثناء حل التعارضات')), 500

@attendance_bp.route('/sync-status', methods=['GET'])
@jwt_required
@require_permission('read_own_attendance')
def get_sync_status():
    """
    GET /api/attendance/sync-status
    Get attendance synchronization status
    حالة مزامنة بيانات الحضور
    """
    try:
        # 1. Get current user (should be student)
        user = get_current_user()
        if user.role.value != 'student':
            return jsonify(error_response('UNAUTHORIZED', 'هذا الـ API مخصص للطلاب فقط')), 403
        
        student = user.get_student_profile()
        if not student:
            return jsonify(error_response('STUDENT_NOT_FOUND', 'ملف الطالب غير موجود')), 404
        
        # 2. Get query parameters
        since_date = request.args.get('since_date')
        if since_date:
            try:
                since_datetime = datetime.fromisoformat(since_date.replace('Z', '+00:00'))
            except ValueError:
                return jsonify(error_response('INVALID_DATE', 'تنسيق التاريخ غير صحيح')), 400
        else:
            # Default to last 30 days
            since_datetime = datetime.utcnow() - timedelta(days=30)
        
        # 3. Get attendance records statistics
        base_query = AttendanceRecord.query.filter_by(student_id=student.id)
        
        # Total records since date
        total_records = base_query.filter(
            AttendanceRecord.check_in_time >= since_datetime
        ).count()
        
        # Synced vs unsynced
        synced_records = base_query.filter(
            AttendanceRecord.check_in_time >= since_datetime,
            AttendanceRecord.is_synced == True
        ).count()
        
        unsynced_records = total_records - synced_records
        
        # Records by status
        pending_records = base_query.filter(
            AttendanceRecord.check_in_time >= since_datetime,
            AttendanceRecord.status == AttendanceStatusEnum.PENDING
        ).count()
        
        verified_records = base_query.filter(
            AttendanceRecord.check_in_time >= since_datetime,
            AttendanceRecord.status == AttendanceStatusEnum.VERIFIED
        ).count()
        
        rejected_records = base_query.filter(
            AttendanceRecord.check_in_time >= since_datetime,
            AttendanceRecord.status == AttendanceStatusEnum.REJECTED
        ).count()
        
        under_review_records = base_query.filter(
            AttendanceRecord.check_in_time >= since_datetime,
            AttendanceRecord.status == AttendanceStatusEnum.UNDER_REVIEW
        ).count()
        
        # Verification statistics
        completed_verification = base_query.filter(
            AttendanceRecord.check_in_time >= since_datetime,
            AttendanceRecord.verification_completed == True
        ).count()
        
        incomplete_verification = total_records - completed_verification
        
        # Recent sync attempts
        failed_sync_attempts = base_query.filter(
            AttendanceRecord.sync_attempts > 0,
            AttendanceRecord.is_synced == False
        ).count()
        
        # 4. Calculate sync health
        sync_health = 'healthy'
        if unsynced_records > 10:
            sync_health = 'warning'
        if unsynced_records > 50 or failed_sync_attempts > 5:
            sync_health = 'critical'
        
        # 5. Get recent records that need attention
        attention_records = []
        
        # Records with sync conflicts
        conflict_records = base_query.filter(
            AttendanceRecord.sync_conflicts.isnot(None)
        ).limit(5).all()
        
        for record in conflict_records:
            attention_records.append({
                'id': record.id,
                'lecture_id': record.lecture_id,
                'issue_type': 'sync_conflict',
                'description': 'تعارض في بيانات المزامنة',
                'check_in_time': record.check_in_time.isoformat(),
                'requires_action': True
            })
        
        # Records under review
        review_records = base_query.filter(
            AttendanceRecord.status == AttendanceStatusEnum.UNDER_REVIEW
        ).limit(5).all()
        
        for record in review_records:
            attention_records.append({
                'id': record.id,
                'lecture_id': record.lecture_id,
                'issue_type': 'under_review',
                'description': 'في انتظار المراجعة',
                'check_in_time': record.check_in_time.isoformat(),
                'requires_action': False
            })
        
        # 6. Prepare response
        sync_status = {
            'student_info': {
                'university_id': student.university_id,
                'full_name': user.full_name
            },
            'sync_period': {
                'since_date': since_datetime.isoformat(),
                'until_date': datetime.utcnow().isoformat()
            },
            'sync_statistics': {
                'total_records': total_records,
                'synced_records': synced_records,
                'unsynced_records': unsynced_records,
                'sync_rate': round((synced_records / total_records) * 100, 2) if total_records > 0 else 100,
                'failed_sync_attempts': failed_sync_attempts
            },
            'record_status': {
                'pending': pending_records,
                'verified': verified_records,
                'rejected': rejected_records,
                'under_review': under_review_records
            },
            'verification_status': {
                'completed_verification': completed_verification,
                'incomplete_verification': incomplete_verification,
                'verification_rate': round((completed_verification / total_records) * 100, 2) if total_records > 0 else 0
            },
            'sync_health': {
                'status': sync_health,
                'last_successful_sync': None,  # Would be calculated from actual sync logs
                'next_sync_recommended': datetime.utcnow() + timedelta(hours=1)
            },
            'attention_required': attention_records,
            'recommendations': []
        }
        
        # 7. Add recommendations based on status
        if unsynced_records > 0:
            sync_status['recommendations'].append({
                'type': 'sync_required',
                'message': f'لديك {unsynced_records} سجل حضور غير متزامن. يُنصح بالمزامنة.',
                'priority': 'medium' if unsynced_records < 10 else 'high'
            })
        
        if incomplete_verification > 0:
            sync_status['recommendations'].append({
                'type': 'verification_incomplete',
                'message': f'{incomplete_verification} سجل حضور لم يكتمل التحقق منه.',
                'priority': 'low'
            })
        
        if failed_sync_attempts > 0:
            sync_status['recommendations'].append({
                'type': 'sync_failures',
                'message': f'{failed_sync_attempts} محاولة مزامنة فاشلة. قد تحتاج لحل يدوي.',
                'priority': 'high'
            })
        
        # 8. Log sync status check
        logging.info(f'Sync status checked by student {student.university_id}: {sync_health}')
        
        return jsonify(success_response(sync_status))
        
    except Exception as e:
        logging.error(f'Sync status error: {str(e)}', exc_info=True)
        return jsonify(error_response('SYNC_STATUS_ERROR', 'حدث خطأ أثناء فحص حالة المزامنة')), 500

# Error handlers specific to attendance blueprint
@attendance_bp.errorhandler(422)
def attendance_validation_error(error):
    """Handle attendance-specific validation errors"""
    return jsonify(error_response(
        'ATTENDANCE_VALIDATION_ERROR',
        'بيانات الحضور غير صحيحة أو غير مكتملة'
    )), 422