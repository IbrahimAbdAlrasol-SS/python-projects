"""
🔄 Pre-Sync APIs - مجموعة المزامنة والبيانات التحضيرية
Implementation: 4 essential pre-sync endpoints
اليوم 1: التطبيق الكامل لـ APIs المزامنة
"""

from flask import Blueprint, request, jsonify, g
from security import jwt_required, get_current_user, require_permission
from models import (
    User, Student, Subject, Room, Schedule, Lecture,
    UserRole, SectionEnum, SemesterEnum, LectureStatusEnum
)
from utils.response_helpers import success_response, error_response, paginated_response
from utils.validation_helpers import validate_pagination_params, validate_filters
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
        
        # Determine current semester based on current month
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
        
        # 7. Build comprehensive response data
        sync_timestamp = datetime.utcnow()
        data_version = f"v1.0.{int(sync_timestamp.timestamp())}"
        
        response_data = {
            'student_profile': {
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
                'device_fingerprint': student.device_fingerprint
            },
            'academic_info': {
                'academic_year': academic_year,
                'current_semester': current_semester.value,
                'semester_start': get_semester_start_date(current_semester, current_year),
                'semester_end': get_semester_end_date(current_semester, current_year),
                'total_subjects': len(subjects),
                'total_credit_hours': sum(subject.credit_hours for subject in subjects)
            },
            'subjects': [
                {
                    'id': subject.id,
                    'code': subject.code,
                    'name': subject.name,
                    'department': subject.department,
                    'credit_hours': subject.credit_hours,
                    'study_year': subject.study_year,
                    'semester': subject.semester.value,
                    'is_active': subject.is_active,
                    'created_at': subject.created_at.isoformat()
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
                    'academic_year': schedule.academic_year,
                    'semester': schedule.semester.value,
                    'is_active': schedule.is_active,
                    'subject': {
                        'code': schedule.subject.code,
                        'name': schedule.subject.name,
                        'credit_hours': schedule.subject.credit_hours
                    } if schedule.subject else None,
                    'teacher': {
                        'full_name': schedule.teacher.user.full_name,
                        'employee_id': schedule.teacher.employee_id,
                        'department': schedule.teacher.department
                    } if schedule.teacher and schedule.teacher.user else None,
                    'room': {
                        'name': schedule.room.name,
                        'building': schedule.room.building,
                        'floor': schedule.room.floor,
                        'room_type': schedule.room.room_type.value
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
                    'barometric_pressure_reference': float(room.barometric_pressure_reference) if room.barometric_pressure_reference else None,
                    'wifi_ssid': room.wifi_ssid,
                    'is_active': room.is_active
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
                    'notes': lecture.notes,
                    'qr_enabled': lecture.qr_enabled,
                    'attendance_window_minutes': lecture.attendance_window_minutes,
                    'late_threshold_minutes': lecture.late_threshold_minutes,
                    'scheduled_start_time': lecture.get_scheduled_start_time().isoformat() if lecture.get_scheduled_start_time() else None,
                    'scheduled_end_time': lecture.get_scheduled_end_time().isoformat() if lecture.get_scheduled_end_time() else None,
                    'actual_start_time': lecture.actual_start_time.isoformat() if lecture.actual_start_time else None,
                    'actual_end_time': lecture.actual_end_time.isoformat() if lecture.actual_end_time else None,
                    'created_at': lecture.created_at.isoformat()
                }
                for lecture in lectures
            ],
            'sync_metadata': {
                'sync_timestamp': sync_timestamp.isoformat(),
                'data_version': data_version,
                'client_timezone': request.headers.get('X-Client-Timezone', 'UTC'),
                'total_subjects': len(subjects),
                'total_schedules': len(schedules),
                'total_rooms': len(rooms),
                'total_lectures': len(lectures),
                'sync_scope': {
                    'lectures_from': start_date.isoformat(),
                    'lectures_to': end_date.isoformat(),
                    'academic_year': academic_year,
                    'semester': current_semester.value
                },
                'recommended_sync_interval': '24h',
                'next_incremental_sync': (sync_timestamp + timedelta(hours=24)).isoformat()
            }
        }
        
        # 8. Log sync operation
        logging.info(f'Student sync data: {student.university_id} - {len(subjects)} subjects, {len(schedules)} schedules, {len(lectures)} lectures')
        
        return jsonify(success_response(response_data, message='تم تحميل البيانات بنجاح'))
        
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
            'rooms': [],
            'profile_updates': []
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
        
        # Get updated subjects
        updated_subjects = Subject.query.filter(
            Subject.study_year == student.study_year,
            Subject.updated_at > last_sync_time
        ).all()
        
        for subject in updated_subjects:
            changes['subjects'].append({
                'id': subject.id,
                'code': subject.code,
                'name': subject.name,
                'is_active': subject.is_active,
                'updated_at': subject.updated_at.isoformat(),
                'change_type': 'updated'
            })
        
        # Get updated rooms
        room_ids = [s.room_id for s in updated_schedules if s.room_id]
        if room_ids:
            updated_rooms = Room.query.filter(
                Room.id.in_(room_ids),
                Room.updated_at > last_sync_time
            ).all()
            
            for room in updated_rooms:
                changes['rooms'].append({
                    'id': room.id,
                    'name': room.name,
                    'building': room.building,
                    'floor': room.floor,
                    'center_latitude': float(room.center_latitude),
                    'center_longitude': float(room.center_longitude),
                    'updated_at': room.updated_at.isoformat(),
                    'change_type': 'updated'
                })
        
        # Check for profile updates
        if user.updated_at and user.updated_at > last_sync_time:
            changes['profile_updates'].append({
                'field': 'user_profile',
                'updated_at': user.updated_at.isoformat(),
                'change_type': 'updated'
            })
        
        if student.updated_at and student.updated_at > last_sync_time:
            changes['profile_updates'].append({
                'field': 'student_profile',
                'updated_at': student.updated_at.isoformat(),
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
                'changes_count': sum(len(change_list) for change_list in changes.values()),
                'next_incremental_sync': (sync_timestamp + timedelta(hours=6)).isoformat()
            }
        }
        
        # 5. Log incremental sync
        logging.info(f'Incremental sync: {student.university_id} - {response_data["sync_metadata"]["changes_count"]} changes since {last_sync}')
        
        return jsonify(success_response(response_data, message='تم تحديث البيانات بنجاح'))
        
    except Exception as e:
        logging.error(f'Incremental sync error: {str(e)}', exc_info=True)
        return jsonify(error_response('SYNC_ERROR', 'حدث خطأ أثناء المزامنة التدريجية')), 500

@student_bp.route('/schedule', methods=['GET'])
@jwt_required
@require_permission('read_own_schedule')
def get_student_schedule():
    """
    GET /api/student/schedule
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
                    'day_name_en': schedule.get_day_name('en'),
                    'classes': []
                }
            
            schedule_by_day[day_key]['classes'].append({
                'id': schedule.id,
                'subject': {
                    'id': schedule.subject.id,
                    'code': schedule.subject.code,
                    'name': schedule.subject.name,
                    'credit_hours': schedule.subject.credit_hours,
                    'department': schedule.subject.department
                } if schedule.subject else None,
                'teacher': {
                    'id': schedule.teacher.id,
                    'name': schedule.teacher.user.full_name,
                    'employee_id': schedule.teacher.employee_id,
                    'department': schedule.teacher.department,
                    'office_location': schedule.teacher.office_location
                } if schedule.teacher and schedule.teacher.user else None,
                'room': {
                    'id': schedule.room.id,
                    'name': schedule.room.name,
                    'building': schedule.room.building,
                    'floor': schedule.room.floor,
                    'capacity': schedule.room.capacity,
                    'room_type': schedule.room.room_type.value
                } if schedule.room else None,
                'time': {
                    'start': schedule.start_time.strftime('%H:%M'),
                    'end': schedule.end_time.strftime('%H:%M'),
                    'duration_minutes': schedule.get_duration_minutes(),
                    'formatted_duration': f"{schedule.get_duration_minutes() // 60}:{schedule.get_duration_minutes() % 60:02d}"
                },
                'academic_info': {
                    'academic_year': schedule.academic_year,
                    'semester': schedule.semester.value
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
        
        # Daily statistics
        daily_stats = {}
        for day_data in weekly_schedule:
            day_classes = len(day_data['classes'])
            day_hours = sum(cls['time']['duration_minutes'] for cls in day_data['classes']) / 60
            daily_stats[day_data['day_name']] = {
                'classes_count': day_classes,
                'total_hours': round(day_hours, 2),
                'first_class': min([cls['time']['start'] for cls in day_data['classes']]) if day_data['classes'] else None,
                'last_class': max([cls['time']['end'] for cls in day_data['classes']]) if day_data['classes'] else None
            }
        
        response_data = {
            'student_info': {
                'university_id': student.university_id,
                'full_name': user.full_name,
                'section': student.section.value,
                'study_year': student.study_year,
                'study_type': student.study_type.value
            },
            'academic_period': {
                'academic_year': academic_year,
                'semester': semester,
                'semester_display': get_semester_display_name(semester)
            },
            'weekly_schedule': weekly_schedule,
            'schedule_statistics': {
                'total_classes': total_classes,
                'total_credit_hours': total_credit_hours,
                'unique_subjects': unique_subjects,
                'days_with_classes': len(schedule_by_day),
                'average_classes_per_day': round(total_classes / max(len(schedule_by_day), 1), 2)
            },
            'daily_statistics': daily_stats,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # 7. Log schedule access
        logging.info(f'Student schedule accessed: {student.university_id} - {total_classes} classes for {academic_year}/{semester}')
        
        return jsonify(success_response(response_data, message='تم تحميل الجدول بنجاح'))
        
    except Exception as e:
        logging.error(f'Student schedule error: {str(e)}', exc_info=True)
        return jsonify(error_response('SCHEDULE_ERROR', 'حدث خطأ أثناء تحميل الجدول')), 500

# Rooms Bulk Download API (تحت blueprint منفصل)
rooms_bp = Blueprint('rooms', __name__, url_prefix='/api/rooms')

@rooms_bp.route('/bulk-download', methods=['GET'])
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
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        # 2. Build query
        query = Room.query
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
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
                    },
                    'barometric_pressure_reference': float(room.barometric_pressure_reference) if room.barometric_pressure_reference else None
                },
                'network': {
                    'wifi_ssid': room.wifi_ssid
                } if room.wifi_ssid else None,
                'metadata': {
                    'is_active': room.is_active,
                    'created_at': room.created_at.isoformat(),
                    'updated_at': room.updated_at.isoformat() if room.updated_at else None
                }
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
                    'room_types': {},
                    'rooms': []
                }
            
            buildings[building_name]['total_rooms'] += 1
            buildings[building_name]['rooms'].append(room_data)
            
            # Group by floor
            floor_num = room_data['floor']
            if floor_num not in buildings[building_name]['floors']:
                buildings[building_name]['floors'][floor_num] = 0
            buildings[building_name]['floors'][floor_num] += 1
            
            # Group by room type
            room_type = room_data['room_type']
            if room_type not in buildings[building_name]['room_types']:
                buildings[building_name]['room_types'][room_type] = 0
            buildings[building_name]['room_types'][room_type] += 1
        
        response_data = {
            'rooms': rooms_data,
            'buildings': list(buildings.values()),
            'summary': {
                'total_rooms': len(rooms_data),
                'total_buildings': len(buildings),
                'room_types': list(set(room['room_type'] for room in rooms_data)),
                'available_floors': sorted(list(set(room['floor'] for room in rooms_data))),
                'capacity_range': {
                    'min': min((room['capacity'] for room in rooms_data), default=0),
                    'max': max((room['capacity'] for room in rooms_data), default=0),
                    'average': round(sum(room['capacity'] for room in rooms_data) / len(rooms_data), 2) if rooms_data else 0
                }
            },
            'download_info': {
                'generated_at': datetime.utcnow().isoformat(),
                'filters_applied': {
                    'building': building,
                    'floor': floor,
                    'room_type': room_type,
                    'include_inactive': include_inactive
                },
                'gps_coordinate_system': 'WGS84',
                'altitude_reference': 'Mean Sea Level (MSL)'
            }
        }
        
        # 6. Log bulk download
        user = get_current_user()
        logging.info(f'Rooms bulk download: {len(rooms_data)} rooms downloaded by {user.username} ({user.role.value})')
        
        return jsonify(success_response(response_data, message='تم تحميل بيانات القاعات بنجاح'))
        
    except Exception as e:
        logging.error(f'Rooms bulk download error: {str(e)}', exc_info=True)
        return jsonify(error_response('DOWNLOAD_ERROR', 'حدث خطأ أثناء تحميل بيانات القاعات')), 500

# Helper functions
def get_semester_start_date(semester, year):
    """Get semester start date"""
    if semester == SemesterEnum.FIRST:
        return f"{year}-09-01"
    elif semester == SemesterEnum.SECOND:
        return f"{year + 1}-02-01"
    else:  # SUMMER
        return f"{year + 1}-07-01"

def get_semester_end_date(semester, year):
    """Get semester end date"""
    if semester == SemesterEnum.FIRST:
        return f"{year + 1}-01-31"
    elif semester == SemesterEnum.SECOND:
        return f"{year + 1}-06-30"
    else:  # SUMMER
        return f"{year + 1}-08-31"

def get_semester_display_name(semester):
    """Get semester display name in Arabic"""
    display_names = {
        'first': 'الفصل الأول',
        'second': 'الفصل الثاني',
        'summer': 'الفصل الصيفي'
    }
    return display_names.get(semester, semester)

# Error handlers
@student_bp.errorhandler(403)
def student_forbidden(error):
    """Handle forbidden access"""
    return jsonify(error_response(
        'FORBIDDEN',
        'غير مصرح بالوصول لهذا المورد'
    )), 403

@rooms_bp.errorhandler(404)
def rooms_not_found(error):
    """Handle not found errors for rooms"""
    return jsonify(error_response(
        'ROOMS_NOT_FOUND',
        'لم يتم العثور على قاعات تطابق المعايير المحددة'
    )), 404