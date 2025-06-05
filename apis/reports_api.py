"""
📊 Reports APIs - مجموعة التقارير والإحصائيات
Group 5: Reports APIs (3 endpoints)
"""

from flask import Blueprint, request, jsonify, make_response, current_app
from security import jwt_required, require_permission, get_current_user
from models import (
    Student, Teacher, Subject, Lecture, AttendanceRecord, Schedule,
    User, UserRole, SectionEnum, AttendanceStatusEnum, AttendanceTypeEnum,
    SemesterEnum, LectureStatusEnum
)
from utils.response_helpers import success_response, error_response, paginated_response
from utils.validation_helpers import (
    validate_date_range, validate_pagination_params,
    validate_filters, validate_sort_params
)
from config.database import db
from datetime import datetime, date, timedelta
import logging
import csv
import io
import json
from sqlalchemy import func, and_, or_

# Create blueprint
reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@reports_bp.route('/attendance/summary', methods=['GET'])
@jwt_required
@require_permission('generate_reports')
def attendance_summary():
    """
    GET /api/reports/attendance/summary
    Generate attendance summary report with filters
    تقرير ملخص الحضور مع فلاتر متقدمة
    """
    try:
        # 1. Validate date range parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date, end_date, date_error = validate_date_range(start_date_str, end_date_str)
        if date_error:
            return jsonify(date_error), 400
        
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # 2. Validate other filters
        allowed_filters = [
            'section', 'study_year', 'subject_id', 'teacher_id',
            'attendance_type', 'verification_status', 'academic_year', 'semester'
        ]
        filters, filter_error = validate_filters(dict(request.args), allowed_filters)
        if filter_error:
            return jsonify(filter_error), 400
        
        # 3. Build base query
        query = db.session.query(
            AttendanceRecord,
            Student,
            User,
            Lecture,
            Schedule,
            Subject
        ).join(
            Student, AttendanceRecord.student_id == Student.id
        ).join(
            User, Student.user_id == User.id
        ).join(
            Lecture, AttendanceRecord.lecture_id == Lecture.id
        ).join(
            Schedule, Lecture.schedule_id == Schedule.id
        ).join(
            Subject, Schedule.subject_id == Subject.id
        ).filter(
            Lecture.lecture_date >= start_date,
            Lecture.lecture_date <= end_date
        )
        
        # 4. Apply filters
        if filters.get('section'):
            try:
                section_enum = SectionEnum(filters['section'])
                query = query.filter(Student.section == section_enum)
            except ValueError:
                return jsonify(error_response('INVALID_SECTION', 'شعبة غير صحيحة')), 400
        
        if filters.get('study_year'):
            try:
                study_year = int(filters['study_year'])
                query = query.filter(Student.study_year == study_year)
            except ValueError:
                return jsonify(error_response('INVALID_STUDY_YEAR', 'سنة دراسية غير صحيحة')), 400
        
        if filters.get('subject_id'):
            query = query.filter(Subject.id == int(filters['subject_id']))
        
        if filters.get('teacher_id'):
            query = query.filter(Schedule.teacher_id == int(filters['teacher_id']))
        
        if filters.get('attendance_type'):
            try:
                attendance_type = AttendanceTypeEnum(filters['attendance_type'])
                query = query.filter(AttendanceRecord.attendance_type == attendance_type)
            except ValueError:
                return jsonify(error_response('INVALID_ATTENDANCE_TYPE', 'نوع الحضور غير صحيح')), 400
        
        if filters.get('verification_status'):
            if filters['verification_status'] == 'completed':
                query = query.filter(AttendanceRecord.verification_completed == True)
            elif filters['verification_status'] == 'incomplete':
                query = query.filter(AttendanceRecord.verification_completed == False)
        
        if filters.get('academic_year'):
            query = query.filter(Schedule.academic_year == filters['academic_year'])
        
        if filters.get('semester'):
            try:
                semester = SemesterEnum(filters['semester'])
                query = query.filter(Schedule.semester == semester)
            except ValueError:
                return jsonify(error_response('INVALID_SEMESTER', 'فصل دراسي غير صحيح')), 400
        
        # 5. Execute query and get results
        results = query.all()
        
        # 6. Calculate overall statistics
        total_attendance_records = len(results)
        
        # Count by attendance type
        on_time_count = sum(1 for r in results if r.AttendanceRecord.attendance_type == AttendanceTypeEnum.ON_TIME)
        late_count = sum(1 for r in results if r.AttendanceRecord.attendance_type == AttendanceTypeEnum.LATE)
        exceptional_count = sum(1 for r in results if r.AttendanceRecord.attendance_type == AttendanceTypeEnum.EXCEPTIONAL)
        
        # Count by verification status
        verified_count = sum(1 for r in results if r.AttendanceRecord.verification_completed)
        pending_count = sum(1 for r in results if not r.AttendanceRecord.verification_completed)
        
        # Count by status
        approved_count = sum(1 for r in results if r.AttendanceRecord.status == AttendanceStatusEnum.VERIFIED)
        rejected_count = sum(1 for r in results if r.AttendanceRecord.status == AttendanceStatusEnum.REJECTED)
        under_review_count = sum(1 for r in results if r.AttendanceRecord.status == AttendanceStatusEnum.UNDER_REVIEW)
        
        # 7. Group by section
        section_stats = {}
        for result in results:
            section = result.Student.section.value
            if section not in section_stats:
                section_stats[section] = {
                    'total': 0,
                    'on_time': 0,
                    'late': 0,
                    'exceptional': 0,
                    'verified': 0
                }
            
            section_stats[section]['total'] += 1
            if result.AttendanceRecord.attendance_type == AttendanceTypeEnum.ON_TIME:
                section_stats[section]['on_time'] += 1
            elif result.AttendanceRecord.attendance_type == AttendanceTypeEnum.LATE:
                section_stats[section]['late'] += 1
            elif result.AttendanceRecord.attendance_type == AttendanceTypeEnum.EXCEPTIONAL:
                section_stats[section]['exceptional'] += 1
            
            if result.AttendanceRecord.verification_completed:
                section_stats[section]['verified'] += 1
        
        # Calculate percentages for sections
        for section_data in section_stats.values():
            total = section_data['total']
            if total > 0:
                section_data['on_time_rate'] = round((section_data['on_time'] / total) * 100, 2)
                section_data['verification_rate'] = round((section_data['verified'] / total) * 100, 2)
        
        # 8. Group by subject
        subject_stats = {}
        for result in results:
            subject_id = result.Subject.id
            subject_name = result.Subject.name
            
            if subject_id not in subject_stats:
                subject_stats[subject_id] = {
                    'subject_name': subject_name,
                    'subject_code': result.Subject.code,
                    'total': 0,
                    'on_time': 0,
                    'late': 0,
                    'verified': 0
                }
            
            subject_stats[subject_id]['total'] += 1
            if result.AttendanceRecord.attendance_type == AttendanceTypeEnum.ON_TIME:
                subject_stats[subject_id]['on_time'] += 1
            elif result.AttendanceRecord.attendance_type == AttendanceTypeEnum.LATE:
                subject_stats[subject_id]['late'] += 1
            
            if result.AttendanceRecord.verification_completed:
                subject_stats[subject_id]['verified'] += 1
        
        # 9. Group by date (daily trend)
        daily_stats = {}
        for result in results:
            lecture_date = result.Lecture.lecture_date.isoformat()
            
            if lecture_date not in daily_stats:
                daily_stats[lecture_date] = {
                    'date': lecture_date,
                    'total': 0,
                    'on_time': 0,
                    'late': 0,
                    'verified': 0
                }
            
            daily_stats[lecture_date]['total'] += 1
            if result.AttendanceRecord.attendance_type == AttendanceTypeEnum.ON_TIME:
                daily_stats[lecture_date]['on_time'] += 1
            elif result.AttendanceRecord.attendance_type == AttendanceTypeEnum.LATE:
                daily_stats[lecture_date]['late'] += 1
            
            if result.AttendanceRecord.verification_completed:
                daily_stats[lecture_date]['verified'] += 1
        
        # Sort daily stats by date
        daily_stats_list = sorted(daily_stats.values(), key=lambda x: x['date'])
        
        # 10. Top performers (students with best attendance)
        student_performance = {}
        for result in results:
            student_id = result.Student.id
            university_id = result.Student.university_id
            full_name = result.User.full_name
            
            if student_id not in student_performance:
                student_performance[student_id] = {
                    'university_id': university_id,
                    'full_name': full_name,
                    'section': result.Student.section.value,
                    'total': 0,
                    'on_time': 0,
                    'late': 0,
                    'verified': 0
                }
            
            student_performance[student_id]['total'] += 1
            if result.AttendanceRecord.attendance_type == AttendanceTypeEnum.ON_TIME:
                student_performance[student_id]['on_time'] += 1
            elif result.AttendanceRecord.attendance_type == AttendanceTypeEnum.LATE:
                student_performance[student_id]['late'] += 1
            
            if result.AttendanceRecord.verification_completed:
                student_performance[student_id]['verified'] += 1
        
        # Calculate performance scores and sort
        for performance in student_performance.values():
            total = performance['total']
            if total > 0:
                performance['on_time_rate'] = round((performance['on_time'] / total) * 100, 2)
                performance['verification_rate'] = round((performance['verified'] / total) * 100, 2)
                # Combined score: 70% on-time rate + 30% verification rate
                performance['performance_score'] = round(
                    (performance['on_time_rate'] * 0.7) + (performance['verification_rate'] * 0.3), 2
                )
        
        # Get top 10 performers
        top_performers = sorted(
            student_performance.values(),
            key=lambda x: x['performance_score'],
            reverse=True
        )[:10]
        
        # 11. Prepare final response
        summary_report = {
            'report_info': {
                'report_type': 'attendance_summary',
                'generated_at': datetime.utcnow().isoformat(),
                'generated_by': get_current_user().full_name,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'total_days': (end_date - start_date).days + 1
                },
                'applied_filters': filters
            },
            'overall_statistics': {
                'total_records': total_attendance_records,
                'attendance_breakdown': {
                    'on_time': on_time_count,
                    'late': late_count,
                    'exceptional': exceptional_count
                },
                'verification_breakdown': {
                    'verified': verified_count,
                    'pending': pending_count
                },
                'status_breakdown': {
                    'approved': approved_count,
                    'rejected': rejected_count,
                    'under_review': under_review_count
                },
                'rates': {
                    'on_time_rate': round((on_time_count / total_attendance_records) * 100, 2) if total_attendance_records > 0 else 0,
                    'verification_rate': round((verified_count / total_attendance_records) * 100, 2) if total_attendance_records > 0 else 0,
                    'approval_rate': round((approved_count / total_attendance_records) * 100, 2) if total_attendance_records > 0 else 0
                }
            },
            'section_analysis': section_stats,
            'subject_analysis': list(subject_stats.values()),
            'daily_trends': daily_stats_list,
            'top_performers': top_performers
        }
        
        # 12. Log report generation
        logging.info(f'Attendance summary report generated: {total_attendance_records} records, filters: {filters}')
        
        return jsonify(success_response(summary_report))
        
    except Exception as e:
        logging.error(f'Attendance summary report error: {str(e)}', exc_info=True)
        return jsonify(error_response('REPORT_ERROR', 'حدث خطأ أثناء إنشاء تقرير الحضور')), 500

@reports_bp.route('/student/<int:student_id>', methods=['GET'])
@jwt_required
@require_permission('read_student')
def student_detailed_report(student_id):
    """
    GET /api/reports/student/<id>
    Generate detailed report for specific student
    تقرير مفصل لطالب محدد
    """
    try:
        # 1. Find student
        student = Student.query.get(student_id)
        if not student:
            return jsonify(error_response('STUDENT_NOT_FOUND', f'طالب غير موجود: {student_id}')), 404
        
        # 2. Validate date range
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date, end_date, date_error = validate_date_range(start_date_str, end_date_str)
        if date_error:
            return jsonify(date_error), 400
        
        # Default to current semester if no dates
        if not start_date:
            start_date = date.today() - timedelta(days=90)  # ~3 months
        if not end_date:
            end_date = date.today()
        
        # 3. Get student's attendance records
        attendance_query = AttendanceRecord.query.filter_by(
            student_id=student_id
        ).join(
            Lecture
        ).join(
            Schedule
        ).join(
            Subject
        ).filter(
            Lecture.lecture_date >= start_date,
            Lecture.lecture_date <= end_date
        ).order_by(
            Lecture.lecture_date.desc()
        )
        
        attendance_records = attendance_query.all()
        
        # 4. Calculate attendance statistics
        total_attended = len(attendance_records)
        on_time_attended = sum(1 for r in attendance_records if r.attendance_type == AttendanceTypeEnum.ON_TIME)
        late_attended = sum(1 for r in attendance_records if r.attendance_type == AttendanceTypeEnum.LATE)
        exceptional_attended = sum(1 for r in attendance_records if r.attendance_type == AttendanceTypeEnum.EXCEPTIONAL)
        
        # Verification statistics
        verified_attendance = sum(1 for r in attendance_records if r.verification_completed)
        pending_verification = total_attended - verified_attendance
        
        # 5. Get total expected lectures for the student
        expected_lectures_query = Lecture.query.join(
            Schedule
        ).filter(
            Schedule.section == student.section,
            Lecture.lecture_date >= start_date,
            Lecture.lecture_date <= end_date,
            Lecture.status.in_([LectureStatusEnum.COMPLETED, LectureStatusEnum.ACTIVE])
        ).join(
            Subject
        ).filter(
            Subject.study_year == student.study_year
        )
        
        total_expected_lectures = expected_lectures_query.count()
        missed_lectures = total_expected_lectures - total_attended
        
        # 6. Subject-wise breakdown
        subject_breakdown = {}
        for record in attendance_records:
            lecture = record.lecture
            schedule = lecture.schedule
            subject = schedule.subject
            
            if subject.id not in subject_breakdown:
                subject_breakdown[subject.id] = {
                    'subject_code': subject.code,
                    'subject_name': subject.name,
                    'credit_hours': subject.credit_hours,
                    'attended': 0,
                    'on_time': 0,
                    'late': 0,
                    'exceptional': 0,
                    'verified': 0
                }
            
            subject_breakdown[subject.id]['attended'] += 1
            
            if record.attendance_type == AttendanceTypeEnum.ON_TIME:
                subject_breakdown[subject.id]['on_time'] += 1
            elif record.attendance_type == AttendanceTypeEnum.LATE:
                subject_breakdown[subject.id]['late'] += 1
            elif record.attendance_type == AttendanceTypeEnum.EXCEPTIONAL:
                subject_breakdown[subject.id]['exceptional'] += 1
            
            if record.verification_completed:
                subject_breakdown[subject.id]['verified'] += 1
        
        # Calculate subject attendance rates
        for subject_data in subject_breakdown.values():
            attended = subject_data['attended']
            if attended > 0:
                subject_data['on_time_rate'] = round((subject_data['on_time'] / attended) * 100, 2)
                subject_data['verification_rate'] = round((subject_data['verified'] / attended) * 100, 2)
        
        # 7. Monthly trends
        monthly_trends = {}
        for record in attendance_records:
            month_key = record.lecture.lecture_date.strftime('%Y-%m')
            
            if month_key not in monthly_trends:
                monthly_trends[month_key] = {
                    'month': month_key,
                    'attended': 0,
                    'on_time': 0,
                    'late': 0,
                    'verified': 0
                }
            
            monthly_trends[month_key]['attended'] += 1
            
            if record.attendance_type == AttendanceTypeEnum.ON_TIME:
                monthly_trends[month_key]['on_time'] += 1
            elif record.attendance_type == AttendanceTypeEnum.LATE:
                monthly_trends[month_key]['late'] += 1
            
            if record.verification_completed:
                monthly_trends[month_key]['verified'] += 1
        
        monthly_trends_list = sorted(monthly_trends.values(), key=lambda x: x['month'])
        
        # 8. Recent attendance history (last 20 records)
        recent_attendance = []
        for record in attendance_records[:20]:
            lecture = record.lecture
            schedule = lecture.schedule
            subject = schedule.subject
            
            recent_attendance.append({
                'attendance_id': record.id,
                'lecture_date': lecture.lecture_date.isoformat(),
                'subject': {
                    'code': subject.code,
                    'name': subject.name
                },
                'room_name': schedule.room.name if schedule.room else None,
                'check_in_time': record.check_in_time.isoformat(),
                'attendance_type': record.attendance_type.value,
                'verification_completed': record.verification_completed,
                'status': record.status.value,
                'is_exceptional': record.is_exceptional,
                'verification_steps': {
                    'location': record.location_verified,
                    'qr_code': record.qr_verified,
                    'face': record.face_verified
                }
            })
        
        # 9. Performance metrics
        attendance_rate = round((total_attended / total_expected_lectures) * 100, 2) if total_expected_lectures > 0 else 0
        punctuality_rate = round((on_time_attended / total_attended) * 100, 2) if total_attended > 0 else 0
        verification_rate = round((verified_attendance / total_attended) * 100, 2) if total_attended > 0 else 0
        
        # Performance grade
        overall_score = (attendance_rate * 0.5) + (punctuality_rate * 0.3) + (verification_rate * 0.2)
        if overall_score >= 90:
            performance_grade = 'ممتاز'
        elif overall_score >= 80:
            performance_grade = 'جيد جداً'
        elif overall_score >= 70:
            performance_grade = 'جيد'
        elif overall_score >= 60:
            performance_grade = 'مقبول'
        else:
            performance_grade = 'ضعيف'
        
        # 10. Prepare detailed report
        detailed_report = {
            'student_info': {
                'id': student.id,
                'university_id': student.university_id,
                'full_name': student.user.full_name,
                'email': student.user.email,
                'section': student.section.value,
                'study_year': student.study_year,
                'study_type': student.study_type.value,
                'academic_status': student.academic_status.value
            },
            'report_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_days': (end_date - start_date).days + 1
            },
            'attendance_summary': {
                'total_expected_lectures': total_expected_lectures,
                'total_attended': total_attended,
                'missed_lectures': missed_lectures,
                'attendance_breakdown': {
                    'on_time': on_time_attended,
                    'late': late_attended,
                    'exceptional': exceptional_attended
                },
                'verification_status': {
                    'verified': verified_attendance,
                    'pending': pending_verification
                }
            },
            'performance_metrics': {
                'attendance_rate': attendance_rate,
                'punctuality_rate': punctuality_rate,
                'verification_rate': verification_rate,
                'overall_score': round(overall_score, 2),
                'performance_grade': performance_grade
            },
            'subject_breakdown': list(subject_breakdown.values()),
            'monthly_trends': monthly_trends_list,
            'recent_attendance': recent_attendance,
            'recommendations': []
        }
        
        # 11. Add recommendations
        if attendance_rate < 75:
            detailed_report['recommendations'].append({
                'type': 'attendance_warning',
                'message': f'معدل الحضور منخفض ({attendance_rate}%). يُنصح بحضور المحاضرات بانتظام.',
                'priority': 'high'
            })
        
        if punctuality_rate < 80:
            detailed_report['recommendations'].append({
                'type': 'punctuality_warning',
                'message': f'معدل الحضور في الوقت المحدد منخفض ({punctuality_rate}%). يُنصح بالوصول مبكراً.',
                'priority': 'medium'
            })
        
        if verification_rate < 90:
            detailed_report['recommendations'].append({
                'type': 'verification_incomplete',
                'message': f'معدل إكمال التحقق منخفض ({verification_rate}%). تأكد من إكمال جميع خطوات التحقق.',
                'priority': 'medium'
            })
        
        # 12. Log report generation
        logging.info(f'Student detailed report generated for {student.university_id}')
        
        return jsonify(success_response(detailed_report))
        
    except Exception as e:
        logging.error(f'Student detailed report error: {str(e)}', exc_info=True)
        return jsonify(error_response('STUDENT_REPORT_ERROR', 'حدث خطأ أثناء إنشاء التقرير المفصل للطالب')), 500

@reports_bp.route('/export', methods=['POST'])
@jwt_required
@require_permission('export_reports')
def export_report():
    """
    POST /api/reports/export
    Export reports in various formats (CSV, Excel, PDF)
    تصدير التقارير بصيغ مختلفة
    """
    try:
        # 1. Validate input
        data = request.get_json()
        if not data:
            return jsonify(error_response('INVALID_INPUT', 'JSON body is required')), 400
        
        # Required fields
        required_fields = ['report_type', 'export_format']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify(error_response(
                'MISSING_FIELDS',
                f'حقول مطلوبة مفقودة: {", ".join(missing_fields)}'
            )), 400
        
        report_type = data['report_type']
        export_format = data['export_format'].lower()
        
        # Validate report type
        valid_report_types = ['attendance_summary', 'student_detailed', 'teacher_performance', 'subject_analysis']
        if report_type not in valid_report_types:
            return jsonify(error_response(
                'INVALID_REPORT_TYPE',
                f'نوع التقرير غير صحيح. الأنواع المدعومة: {", ".join(valid_report_types)}'
            )), 400
        
        # Validate export format
        valid_formats = ['csv', 'excel', 'json']
        if export_format not in valid_formats:
            return jsonify(error_response(
                'INVALID_FORMAT',
                f'صيغة التصدير غير صحيحة. الصيغ المدعومة: {", ".join(valid_formats)}'
            )), 400
        
        # 2. Get report parameters
        filters = data.get('filters', {})
        start_date_str = filters.get('start_date')
        end_date_str = filters.get('end_date')
        
        start_date, end_date, date_error = validate_date_range(start_date_str, end_date_str)
        if date_error:
            return jsonify(date_error), 400
        
        # Default date range
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # 3. Generate report data based on type
        if report_type == 'attendance_summary':
            report_data = generate_attendance_export_data(start_date, end_date, filters)
        elif report_type == 'student_detailed':
            student_id = filters.get('student_id')
            if not student_id:
                return jsonify(error_response('MISSING_STUDENT_ID', 'معرف الطالب مطلوب للتقرير المفصل')), 400
            report_data = generate_student_export_data(student_id, start_date, end_date)
        else:
            return jsonify(error_response('REPORT_NOT_IMPLEMENTED', 'نوع التقرير غير مُطبق بعد')), 501
        
        # 4. Format data based on export format
        if export_format == 'csv':
            output = generate_csv_export(report_data, report_type)
            mimetype = 'text/csv'
            filename = f'{report_type}_{start_date}_{end_date}.csv'
            
        elif export_format == 'excel':
            output = generate_excel_export(report_data, report_type)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'{report_type}_{start_date}_{end_date}.xlsx'
            
        elif export_format == 'json':
            output = json.dumps(report_data, ensure_ascii=False, indent=2, default=str)
            mimetype = 'application/json'
            filename = f'{report_type}_{start_date}_{end_date}.json'
        
        # 5. Create response
        response = make_response(output)
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # 6. Log export
        user = get_current_user()
        logging.info(f'Report exported: {report_type} in {export_format} format by {user.username}')
        
        return response
        
    except Exception as e:
        logging.error(f'Report export error: {str(e)}', exc_info=True)
        return jsonify(error_response('EXPORT_ERROR', 'حدث خطأ أثناء تصدير التقرير')), 500

def generate_attendance_export_data(start_date, end_date, filters):
    """Generate attendance data for export"""
    # Build query similar to attendance_summary but return raw data
    query = db.session.query(
        AttendanceRecord,
        Student,
        User,
        Lecture,
        Schedule,
        Subject
    ).join(
        Student, AttendanceRecord.student_id == Student.id
    ).join(
        User, Student.user_id == User.id
    ).join(
        Lecture, AttendanceRecord.lecture_id == Lecture.id
    ).join(
        Schedule, Lecture.schedule_id == Schedule.id
    ).join(
        Subject, Schedule.subject_id == Subject.id
    ).filter(
        Lecture.lecture_date >= start_date,
        Lecture.lecture_date <= end_date
    )
    
    # Apply filters (simplified for export)
    if filters.get('section'):
        query = query.filter(Student.section == SectionEnum(filters['section']))
    
    results = query.all()
    
    # Format for export
    export_data = []
    for result in results:
        export_data.append({
            'student_id': result.Student.university_id,
            'student_name': result.User.full_name,
            'section': result.Student.section.value,
            'study_year': result.Student.study_year,
            'subject_code': result.Subject.code,
            'subject_name': result.Subject.name,
            'lecture_date': result.Lecture.lecture_date.isoformat(),
            'check_in_time': result.AttendanceRecord.check_in_time.isoformat(),
            'attendance_type': result.AttendanceRecord.attendance_type.value,
            'verification_completed': result.AttendanceRecord.verification_completed,
            'status': result.AttendanceRecord.status.value,
            'location_verified': result.AttendanceRecord.location_verified,
            'qr_verified': result.AttendanceRecord.qr_verified,
            'face_verified': result.AttendanceRecord.face_verified,
            'is_exceptional': result.AttendanceRecord.is_exceptional,
            'room_name': result.Schedule.room.name if result.Schedule.room else None
        })
    
    return export_data

def generate_student_export_data(student_id, start_date, end_date):
    """Generate student-specific data for export"""
    student = Student.query.get(student_id)
    if not student:
        return []
    
    attendance_records = AttendanceRecord.query.filter_by(
        student_id=student_id
    ).join(Lecture).filter(
        Lecture.lecture_date >= start_date,
        Lecture.lecture_date <= end_date
    ).join(Schedule).join(Subject).all()
    
    export_data = []
    for record in attendance_records:
        export_data.append({
            'attendance_id': record.id,
            'lecture_date': record.lecture.lecture_date.isoformat(),
            'subject_code': record.lecture.schedule.subject.code,
            'subject_name': record.lecture.schedule.subject.name,
            'check_in_time': record.check_in_time.isoformat(),
            'attendance_type': record.attendance_type.value,
            'verification_completed': record.verification_completed,
            'location_verified': record.location_verified,
            'qr_verified': record.qr_verified,
            'face_verified': record.face_verified,
            'status': record.status.value,
            'room_name': record.lecture.schedule.room.name if record.lecture.schedule.room else None
        })
    
    return export_data

def generate_csv_export(data, report_type):
    """Generate CSV format export"""
    if not data:
        return "No data available"
    
    output = io.StringIO()
    
    # Get field names from first record
    fieldnames = list(data[0].keys())
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()

def generate_excel_export(data, report_type):
    """Generate Excel format export"""
    if not data:
        return b"No data available"
    
    try:
        import pandas as pd
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Report Data', index=False)
        
        return output.getvalue()
        
    except ImportError:
        # Fallback to simple format if pandas not available
        return generate_csv_export(data, report_type).encode('utf-8')

# Error handlers specific to reports blueprint
@reports_bp.errorhandler(413)
def reports_file_too_large(error):
    """Handle large report generation"""
    return jsonify(error_response(
        'REPORT_TOO_LARGE',
        'التقرير كبير جداً. يرجى تضييق نطاق التواريخ أو الفلاتر'
    )), 413