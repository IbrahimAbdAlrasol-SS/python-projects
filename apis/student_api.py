"""
🎓 Student/Pre-Sync APIs - مجموعة بيانات الطلاب والمزامنة
Group 1: Pre-Sync APIs (4 endpoints)
"""

from flask import Blueprint, request, jsonify, g
from security import jwt_required, get_current_user, require_permission
from models import (
    User, Student, Subject, Room, Schedule, Lecture,
    UserRole, SectionEnum, SemesterEnum
)
from utils.response_helpers import success_response, error_response, paginated_response
from utils.validation_helpers import validate_pagination_params
from datetime import datetime, date, timedelta
import logging

# Create blueprint
student_bp = Blueprint('student', __name__, url_prefix='/api/student')

@student_bp.route('/sync-data', methods=['GET'])
@jwt_required
@require_permission('read_own_profile')
def sync_data():
    """
    GET /api/student/sync-data
    Download all student data for offline use
    تحميل جميع بيانات الطالب للعمل بدون انترنت
    """
    try:
        # 1. Get current user and student
        user = get_current_user()
        if user.role != UserRole.STUDENT:
            return jsonify(error_response('UNAUTHORIZED', 'هذا الـ API مخصص للطلاب فقط')), 403
        
        student = user.get_student_profile()
        if not student:
            return jsonify(error_response('STUDENT_NOT_FOUND', 'ملف الطالب غير موجود')), 404
        
        # 2. Get academic period info
        current_year = datetime.now().year
        academic_year = f"{current_year}-{current_year + 1}"
        
        # Determine current semester
        current_month = datetime.now().month
        if 9 <= current_month <= 12:
            current_semester = SemesterEnum.FIRST
        elif 2 <= current_month <= 6:
            current_semester = SemesterEnum.SECOND
        else:
            current_semester = SemesterEnum.SUMMER
        
        # 3. Get student's subjects for current year
        subjects = Subject.query.filter_by(
            study_year=student.study_year,
            is_active=True
        ).all()
        
        # 4. Get student's schedules
        schedules = Schedule.query.filter_by(
            section=student.section,
            academic_year=academic_year,
            semester=current_semester,
            is_active=True
        ).join(Subject).filter(
            Subject.study_year == student.study_year
        ).all()
        
        # 5. Get rooms for student's schedules
        room_ids = [schedule.room_id for schedule in schedules if schedule.room_id]
        rooms = Room.query.filter(
            Room.id.in_(room_ids),
            Room.is_active == True
        ).all() if room_ids else []
        
        # 6. Get recent and upcoming lectures (last 7 days + next 30 days)
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() + timedelta(days=30)
        
        schedule_ids = [schedule.id for schedule in schedules]
        lectures = Lecture.query.filter(
            Lecture.schedule_id.in_(schedule_ids),
            Lecture.lecture_date >= start_date,
            Lecture.lecture_date <= end_date
        ).order_by(Lecture.lecture_date, Lecture.actual_start_time).all() if schedule_ids else []
        
        # 7. Build response data
        sync_timestamp = datetime.utcnow()
        data_version = f"v1.0.{int(sync_timestamp.timestamp())}"
        
        response_data = {
            'student_profile': {
                'id': student.id,
                'user_id': user.id,
                'university_id': student.university_id,
                'full_name': user.full_name,
                'email': user.email,
                'section': student.section.value,
                'study_year': student.study_year,
                'study_type': student.study_type.value,
                'academic_status': student.academic_status.value,
                'face_registered': student.face_registered,
                'face_registered_at': student.face_registered_at.isoformat() if student.face_registered_at else None
            },
            'academic_info': {
                'academic_year': academic_year,
                'current_semester': current_semester.value,
                'semester_start': '2024-09-01',  # Configure this properly
                'semester_end': '2025-01-31'     # Configure this properly
            },
            'subjects': [
                {
                    'id': subject.id,
                    'code': subject.code,
                    'name': subject.name,
                    'department': subject.department,
                    'credit_hours': subject.credit_hours,
                    'study_year': subject.study_year,
                    'semester': subject.semester.value
                }
                for subject in subjects
            ],
            'schedules': [
                {
                    'id': schedule.id,
                    'subject_id': schedule.subject_id,
                    'teacher_id': schedule.teacher_id,
                    'room_id': schedule.room_id,
                    'section': schedule.section.value,
                    'day_of_week': schedule.day_of_week,
                    'day_name': schedule.get_day_name('ar'),
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M'),
                    'duration_minutes': schedule.get_duration_minutes(),
                    'subject': {
                        'code': schedule.subject.code,
                        'name': schedule.subject.name
                    } if schedule.subject else None,
                    'teacher': {
                        'full_name': schedule.teacher.user.full_name,
                        'employee_id': schedule.teacher.employee_id
                    } if schedule.teacher and schedule.teacher.user else None,
                    'room': {
                        'name': schedule.room.name,
                        'building': schedule.room.building,
                        'floor': schedule.room.floor
                    } if schedule.room else None
                }
                for schedule in schedules
            ],
            'rooms': [
                {
                    'id': room.id,
                    'name': room.name,
                    'building': room.building,
                    'floor': room.floor,
                    'room_type': room.room_type.value,
                    'capacity': room.capacity,
                    'center_latitude': float(room.center_latitude),
                    'center_longitude': float(room.center_longitude),
                    'gps_polygon': room.gps_polygon,
                    'ground_reference_altitude': float(room.ground_reference_altitude),
                    'floor_altitude': float(room.floor_altitude),
                    'ceiling_height': float(room.ceiling_height),
                    'wifi_ssid': room.wifi_ssid
                }
                for room in rooms
            ],
            'lectures': [
                {
                    'id': lecture.id,
                    'schedule_id': lecture.schedule_id,
                    'lecture_date': lecture.lecture_date.isoformat(),
                    'status': lecture.status.value,
                    'topic': lecture.topic,
                    'qr_enabled': lecture.qr_enabled,
                    'attendance_window_minutes': lecture.attendance_window_minutes,
                    'late_threshold_minutes': lecture.late_threshold_minutes,
                    'scheduled_start_time': lecture.get_scheduled_start_time().isoformat() if lecture.get_scheduled_start_time() else None,
                    'scheduled_end_time': lecture.get_scheduled_end_time().isoformat() if lecture.get_scheduled_end_time() else None,
                    'actual_start_time': lecture.actual_start_time.isoformat() if lecture.actual_start_time else None,
                    'actual_end_time': lecture.actual_end_time.isoformat() if lecture.actual_end_time else None
                }
                for lecture in lectures
            ],
            'sync_metadata': {
                'sync_timestamp': sync_timestamp.isoformat(),
                'data_version': data_version,
                'total_subjects': len(subjects),
                'total_schedules': len(schedules),
                'total_rooms': len(rooms),
                'total_lectures': len(lectures),
                'sync_scope': {
                    'lectures_from': start_date.isoformat(),
                    'lectures_to': end_date.isoformat(),
                    'academic_year': academic_year,
                    'semester': current_semester.value
                }
            }
        }
        
        # 8. Log sync operation
        logging.info(f'Student sync data: {student.university_id} - {len(subjects)} subjects, {len(schedules)} schedules')
        
        return jsonify(success_response(response_data))
        
    except Exception as e:
        logging.error(f'Student sync error: {str(e)}', exc_info=True)
        return jsonify(error_response('SYNC_ERROR', 'حدث خطأ أثناء مزامنة البيانات')), 500

@student_bp.route('/incremental-sync', methods=['GET'])
@jwt_required
@require_permission('read_own_profile')
def incremental_sync():
    """
    GET /api/student/incremental-sync
    Get only changed data since last sync
    تحديث البيانات المتغيرة فقط منذ آخر مزامنة
    """
    try:
        # 1. Get parameters
        last_sync = request.args.get('last_sync')
        data_version = request.args.get('data_version')
        
        if not last_sync:
            return jsonify(error_response('MISSING_PARAMETER', 'معامل last_sync مطلوب')), 400
        
        # Parse last sync timestamp
        try:
            last_sync_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
        except ValueError:
            return jsonify(error_response('INVALID_TIMESTAMP', 'تنسيق التاريخ غير صحيح')), 400
        
        # 2. Get current user and student
        user = get_current_user()
        if user.role != UserRole.STUDENT:
            return jsonify(error_response('UNAUTHORIZED', 'هذا الـ API مخصص للطلاب فقط')), 403
        
        student = user.get_student_profile()
        if not student:
            return jsonify(error_response('STUDENT_NOT_FOUND', 'ملف الطالب غير موجود')), 404
        
        # 3. Get changes since last sync
        changes = {
            'lectures': [],
            'schedules': [],
            'subjects': [],
            'rooms': []
        }
        
        # Get updated lectures
        updated_lectures = Lecture.query.join(Schedule).filter(
            Schedule.section == student.section,
            Lecture.updated_at > last_sync_time
        ).order_by(Lecture.updated_at).all()
        
        for lecture in updated_lectures:
            changes['lectures'].append({
                'id': lecture.id,
                'schedule_id': lecture.schedule_id,
                'lecture_date': lecture.lecture_date.isoformat(),
                'status': lecture.status.value,
                'topic': lecture.topic,
                'qr_enabled': lecture.qr_enabled,
                'updated_at': lecture.updated_at.isoformat(),
                'change_type': 'updated'
            })
        
        # Get updated schedules
        updated_schedules = Schedule.query.filter(
            Schedule.section == student.section,
            Schedule.updated_at > last_sync_time
        ).all()
        
        for schedule in updated_schedules:
            changes['schedules'].append({
                'id': schedule.id,
                'subject_id': schedule.subject_id,
                'day_of_week': schedule.day_of_week,
                'start_time': schedule.start_time.strftime('%H:%M'),
                'end_time': schedule.end_time.strftime('%H:%M'),
                'is_active': schedule.is_active,
                'updated_at': schedule.updated_at.isoformat(),
                'change_type': 'updated'
            })
        
        # 4. Generate new data version
        sync_timestamp = datetime.utcnow()
        new_data_version = f"v1.0.{int(sync_timestamp.timestamp())}"
        
        response_data = {
            'changes': changes,
            'has_changes': any(len(change_list) > 0 for change_list in changes.values()),
            'sync_metadata': {
                'sync_timestamp': sync_timestamp.isoformat(),
                'last_sync': last_sync,
                'new_data_version': new_data_version,
                'previous_version': data_version,
                'changes_count': sum(len(change_list) for change_list in changes.values())
            }
        }
        
        # 5. Log incremental sync
        logging.info(f'Incremental sync: {student.university_id} - {response_data["sync_metadata"]["changes_count"]} changes')
        
        return jsonify(success_response(response_data))
        
    except Exception as e:
        logging.error(f'Incremental sync error: {str(e)}', exc_info=True)
        return jsonify(error_response('SYNC_ERROR', 'حدث خطأ أثناء المزامنة التدريجية')), 500

@student_bp.route('/schedule', methods=['GET'])
@jwt_required
@require_permission('read_own_schedule')
def get_student_schedule():
    """
    GET /api/schedules/student-schedule
    Download student's personal schedule
    تحميل الجدول الشخصي للطالب
    """
    try:
        # 1. Get current user and student
        user = get_current_user()
        if user.role != UserRole.STUDENT:
            return jsonify(error_response('UNAUTHORIZED', 'هذا الـ API مخصص للطلاب فقط')), 403
        
        student = user.get_student_profile()
        if not student:
            return jsonify(error_response('STUDENT_NOT_FOUND', 'ملف الطالب غير موجود')), 404
        
        # 2. Get query parameters
        academic_year = request.args.get('academic_year')
        semester = request.args.get('semester')
        
        # Default to current academic period
        if not academic_year:
            current_year = datetime.now().year
            academic_year = f"{current_year}-{current_year + 1}"
        
        if not semester:
            current_month = datetime.now().month
            if 9 <= current_month <= 12:
                semester = 'first'
            elif 2 <= current_month <= 6:
                semester = 'second'
            else:
                semester = 'summer'
        
        # 3. Get student's schedule
        schedules = Schedule.query.filter_by(
            section=student.section,
            academic_year=academic_year,
            semester=SemesterEnum(semester),
            is_active=True
        ).join(Subject).filter(
            Subject.study_year == student.study_year
        ).order_by(Schedule.day_of_week, Schedule.start_time).all()
        
        # 4. Organize schedule by days
        schedule_by_day = {}
        for schedule in schedules:
            day_key = schedule.day_of_week
            day_name = schedule.get_day_name('ar')
            
            if day_key not in schedule_by_day:
                schedule_by_day[day_key] = {
                    'day_number': day_key,
                    'day_name': day_name,
                    'classes': []
                }
            
            schedule_by_day[day_key]['classes'].append({
                'id': schedule.id,
                'subject': {
                    'id': schedule.subject.id,
                    'code': schedule.subject.code,
                    'name': schedule.subject.name,
                    'credit_hours': schedule.subject.credit_hours
                } if schedule.subject else None,
                'teacher': {
                    'id': schedule.teacher.id,
                    'name': schedule.teacher.user.full_name,
                    'employee_id': schedule.teacher.employee_id
                } if schedule.teacher and schedule.teacher.user else None,
                'room': {
                    'id': schedule.room.id,
                    'name': schedule.room.name,
                    'building': schedule.room.building,
                    'floor': schedule.room.floor
                } if schedule.room else None,
                'time': {
                    'start': schedule.start_time.strftime('%H:%M'),
                    'end': schedule.end_time.strftime('%H:%M'),
                    'duration_minutes': schedule.get_duration_minutes()
                }
            })
        
        # 5. Convert to sorted list
        weekly_schedule = [
            schedule_by_day[day] for day in sorted(schedule_by_day.keys())
        ]
        
        # 6. Calculate schedule statistics
        total_classes = len(schedules)
        total_credit_hours = sum(
            schedule.subject.credit_hours for schedule in schedules 
            if schedule.subject
        )
        unique_subjects = len(set(
            schedule.subject_id for schedule in schedules 
            if schedule.subject_id
        ))
        
        response_data = {
            'student_info': {
                'university_id': student.university_id,
                'full_name': user.full_name,
                'section': student.section.value,
                'study_year': student.study_year
            },
            'academic_period': {
                'academic_year': academic_year,
                'semester': semester
            },
            'weekly_schedule': weekly_schedule,
            'schedule_statistics': {
                'total_classes': total_classes,
                'total_credit_hours': total_credit_hours,
                'unique_subjects': unique_subjects,
                'days_with_classes': len(schedule_by_day)
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # 7. Log schedule access
        logging.info(f'Student schedule accessed: {student.university_id} - {total_classes} classes')
        
        return jsonify(success_response(response_data))
        
    except Exception as e:
        logging.error(f'Student schedule error: {str(e)}', exc_info=True)
        return jsonify(error_response('SCHEDULE_ERROR', 'حدث خطأ أثناء تحميل الجدول')), 500

# Rooms API moved to separate endpoint
@student_bp.route('/../rooms/bulk-download', methods=['GET'])
@jwt_required
@require_permission('read_room')
def bulk_download_rooms():
    """
    GET /api/rooms/bulk-download
    Download room data with GPS coordinates
    تحميل بيانات القاعات مع الإحداثيات
    """
    try:
        # 1. Get query parameters
        building = request.args.get('building')
        floor = request.args.get('floor', type=int)
        room_type = request.args.get('room_type')
        
        # 2. Build query
        query = Room.query.filter_by(is_active=True)
        
        if building:
            query = query.filter_by(building=building)
        
        if floor is not None:
            query = query.filter_by(floor=floor)
        
        if room_type:
            query = query.filter_by(room_type=room_type)
        
        # 3. Get rooms ordered by building and name
        rooms = query.order_by(Room.building, Room.name).all()
        
        # 4. Format room data with full GPS information
        rooms_data = []
        for room in rooms:
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
                    'altitude_info': {
                        'ground_reference_altitude': float(room.ground_reference_altitude),
                        'floor_altitude': float(room.floor_altitude),
                        'ceiling_height': float(room.ceiling_height)
                    }
                },
                'network': {
                    'wifi_ssid': room.wifi_ssid
                } if room.wifi_ssid else None,
                'updated_at': room.updated_at.isoformat()
            }
            rooms_data.append(room_data)
        
        # 5. Group by building for easier consumption
        buildings = {}
        for room_data in rooms_data:
            building_name = room_data['building']
            if building_name not in buildings:
                buildings[building_name] = {
                    'building_name': building_name,
                    'total_rooms': 0,
                    'floors': {},
                    'rooms': []
                }
            
            buildings[building_name]['total_rooms'] += 1
            buildings[building_name]['rooms'].append(room_data)
            
            # Group by floor
            floor_num = room_data['floor']
            if floor_num not in buildings[building_name]['floors']:
                buildings[building_name]['floors'][floor_num] = 0
            buildings[building_name]['floors'][floor_num] += 1
        
        response_data = {
            'rooms': rooms_data,
            'buildings': list(buildings.values()),
            'summary': {
                'total_rooms': len(rooms_data),
                'total_buildings': len(buildings),
                'room_types': list(set(room['room_type'] for room in rooms_data))
            },
            'download_info': {
                'generated_at': datetime.utcnow().isoformat(),
                'filters_applied': {
                    'building': building,
                    'floor': floor,
                    'room_type': room_type
                }
            }
        }
        
        # 6. Log bulk download
        logging.info(f'Rooms bulk download: {len(rooms_data)} rooms downloaded')
        
        return jsonify(success_response(response_data))
        
    except Exception as e:
        logging.error(f'Rooms bulk download error: {str(e)}', exc_info=True)
        return jsonify(error_response('DOWNLOAD_ERROR', 'حدث خطأ أثناء تحميل بيانات القاعات')), 500