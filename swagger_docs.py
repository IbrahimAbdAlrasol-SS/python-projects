"""
📚 Swagger Documentation Setup - توثيق APIs بـ Swagger
Complete API documentation for Smart Attendance System
"""

from flask import Flask
from flask_restx import Api, Resource, fields
from flask_restx import Namespace

def setup_swagger_docs(app: Flask):
    """Setup comprehensive Swagger documentation"""
    
    # API Documentation Setup
    api = Api(
        app,
        version='1.0.0',
        title='Smart Attendance System API',
        description='''
# نظام الحضور الذكي - واجهة برمجة التطبيقات

## المميزات الأساسية:
- **التحقق الثلاثي:** GPS + QR + Face Recognition
- **العمل بدون انترنت:** مزامنة ذكية للبيانات  
- **إدارة شاملة:** طلاب، مدرسين، قاعات، جداول
- **تقارير متقدمة:** إحصائيات وتحليلات مفصلة
- **أمان محكم:** JWT Authentication + RBAC

## استخدام الـ API:
1. سجل دخول للحصول على access_token
2. أرفق الـ token في Authorization header
3. استخدم الـ endpoints بحسب صلاحياتك

## أنواع المستخدمين:
- **طلاب:** تسجيل حضور، عرض جداول، تسليم واجبات
- **مدرسين:** إدارة محاضرات، تقارير حضور، واجبات
- **إداريين:** إدارة شاملة للنظام
        ''',
        doc='/docs/',
        prefix='/api',
        authorizations={
            'Bearer': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'JWT Authorization header. Format: "Bearer {token}"'
            }
        },
        security='Bearer'
    )
    
    # ============================================================================
    # MODEL DEFINITIONS - تعريف النماذج
    # ============================================================================
    
    # Authentication Models
    student_login_model = api.model('StudentLogin', {
        'university_id': fields.String(required=True, description='الرقم الجامعي (مثال: CS2021001)', example='CS2024001'),
        'secret_code': fields.String(required=True, description='الكود السري (8 أحرف)', example='SEC001'),
        'device_fingerprint': fields.String(description='بصمة الجهاز', example='device-001')
    })
    
    teacher_login_model = api.model('TeacherLogin', {
        'username': fields.String(required=True, description='اسم المستخدم', example='teacher1'),
        'password': fields.String(required=True, description='كلمة المرور', example='Teacher123!'),
        'device_fingerprint': fields.String(description='بصمة الجهاز', example='device-001')
    })
    
    # Student Models
    student_model = api.model('Student', {
        'id': fields.Integer(description='معرف الطالب'),
        'university_id': fields.String(required=True, description='الرقم الجامعي'),
        'full_name': fields.String(required=True, description='الاسم الكامل'),
        'email': fields.String(required=True, description='البريد الإلكتروني'),
        'section': fields.String(required=True, description='الشعبة (A, B, C)'),
        'study_year': fields.Integer(required=True, description='السنة الدراسية (1-4)'),
        'study_type': fields.String(description='نوع الدراسة (morning, evening)')
    })
    
    # Room Models
    room_model = api.model('Room', {
        'id': fields.Integer(description='معرف القاعة'),
        'name': fields.String(required=True, description='اسم القاعة', example='A101'),
        'building': fields.String(required=True, description='اسم المبنى', example='مبنى A'),
        'floor': fields.Integer(required=True, description='رقم الطابق', example=1),
        'capacity': fields.Integer(description='السعة', example=30),
        'center_latitude': fields.Float(required=True, description='خط العرض'),
        'center_longitude': fields.Float(required=True, description='خط الطول'),
        'gps_polygon': fields.List(fields.List(fields.Float), description='مضلع GPS'),
        'ground_reference_altitude': fields.Float(description='ارتفاع مرجعي'),
        'floor_altitude': fields.Float(description='ارتفاع الطابق'),
        'ceiling_height': fields.Float(description='ارتفاع السقف')
    })
    
    # Attendance Models
    attendance_record_model = api.model('AttendanceRecord', {
        'local_id': fields.String(description='معرف محلي'),
        'lecture_id': fields.Integer(required=True, description='معرف المحاضرة'),
        'qr_session_id': fields.String(required=True, description='معرف جلسة QR'),
        'recorded_latitude': fields.Float(required=True, description='خط العرض المسجل'),
        'recorded_longitude': fields.Float(required=True, description='خط الطول المسجل'),
        'recorded_altitude': fields.Float(description='الارتفاع المسجل'),
        'check_in_time': fields.String(required=True, description='وقت تسجيل الدخول'),
        'location_verified': fields.Boolean(description='تم التحقق من الموقع'),
        'qr_verified': fields.Boolean(description='تم التحقق من QR'),
        'face_verified': fields.Boolean(description='تم التحقق من الوجه'),
        'device_info': fields.Raw(description='معلومات الجهاز')
    })
    
    # Response Models
    success_response_model = api.model('SuccessResponse', {
        'success': fields.Boolean(description='حالة النجاح'),
        'message': fields.String(description='رسالة النجاح'),
        'data': fields.Raw(description='البيانات المُعادة'),
        'timestamp': fields.String(description='وقت الاستجابة')
    })
    
    error_response_model = api.model('ErrorResponse', {
        'success': fields.Boolean(description='حالة النجاح (false)'),
        'error': fields.Nested(api.model('Error', {
            'code': fields.String(description='كود الخطأ'),
            'message': fields.String(description='رسالة الخطأ'),
            'details': fields.Raw(description='تفاصيل إضافية')
        })),
        'timestamp': fields.String(description='وقت الاستجابة')
    })
    
    # ============================================================================
    # NAMESPACES - تجميع APIs
    # ============================================================================
    
    # Authentication Namespace
    auth_ns = Namespace('auth', description='🔐 Authentication Operations - عمليات المصادقة')
    
    @auth_ns.route('/student-login')
    class StudentLogin(Resource):
        @auth_ns.expect(student_login_model)
        @auth_ns.marshal_with(success_response_model, code=200)
        @auth_ns.marshal_with(error_response_model, code=401)
        @auth_ns.doc('student_login')
        def post(self):
            """تسجيل دخول الطلاب بالرقم الجامعي والكود السري"""
            pass
    
    @auth_ns.route('/teacher-login')
    class TeacherLogin(Resource):
        @auth_ns.expect(teacher_login_model)
        @auth_ns.marshal_with(success_response_model, code=200)
        @auth_ns.doc('teacher_login')
        def post(self):
            """تسجيل دخول المدرسين باسم المستخدم وكلمة المرور"""
            pass
    
    @auth_ns.route('/refresh-token')
    class RefreshToken(Resource):
        @auth_ns.marshal_with(success_response_model, code=200)
        @auth_ns.doc('refresh_token', security='Bearer')
        def post(self):
            """تجديد الرمز المميز للوصول"""
            pass
    
    # Student Namespace
    student_ns = Namespace('student', description='👤 Student Operations - عمليات الطلاب')
    
    @student_ns.route('/sync-data')
    class SyncData(Resource):
        @student_ns.marshal_with(success_response_model, code=200)
        @student_ns.doc('sync_data', security='Bearer')
        def get(self):
            """تحميل جميع بيانات الطالب للعمل بدون انترنت"""
            pass
    
    @student_ns.route('/incremental-sync')
    class IncrementalSync(Resource):
        @student_ns.marshal_with(success_response_model, code=200)
        @student_ns.doc('incremental_sync', security='Bearer')
        @student_ns.param('last_sync', 'آخر وقت مزامنة', required=True)
        @student_ns.param('data_version', 'إصدار البيانات', required=False)
        def get(self):
            """تحديث البيانات المتغيرة فقط منذ آخر مزامنة"""
            pass
    
    @student_ns.route('/schedule')
    class StudentSchedule(Resource):
        @student_ns.marshal_with(success_response_model, code=200)
        @student_ns.doc('student_schedule', security='Bearer')
        @student_ns.param('academic_year', 'السنة الأكاديمية', required=False)
        @student_ns.param('semester', 'الفصل الدراسي', required=False)
        def get(self):
            """تحميل الجدول الشخصي للطالب"""
            pass
    
    # Rooms Namespace
    rooms_ns = Namespace('rooms', description='🏢 Rooms Operations - عمليات القاعات')
    
    @rooms_ns.route('/bulk-download')
    class RoomsBulkDownload(Resource):
        @rooms_ns.marshal_with(success_response_model, code=200)
        @rooms_ns.doc('rooms_bulk_download', security='Bearer')
        @rooms_ns.param('building', 'اسم المبنى', required=False)
        @rooms_ns.param('floor', 'رقم الطابق', required=False)
        @rooms_ns.param('include_inactive', 'تضمين غير النشطة', required=False, default=False)
        def get(self):
            """تحميل بيانات القاعات مع الإحداثيات الثلاثية"""
            pass
    
    # Admin Namespace
    admin_ns = Namespace('admin', description='👑 Admin Operations - عمليات الإدارة')
    
    @admin_ns.route('/students')
    class AdminStudents(Resource):
        @admin_ns.marshal_with(success_response_model, code=200)
        @admin_ns.doc('admin_get_students', security='Bearer')
        @admin_ns.param('page', 'رقم الصفحة', default=1)
        @admin_ns.param('limit', 'عدد العناصر لكل صفحة', default=20)
        @admin_ns.param('section', 'فلتر الشعبة', required=False)
        @admin_ns.param('study_year', 'فلتر السنة الدراسية', required=False)
        @admin_ns.param('search', 'البحث في الأسماء', required=False)
        def get(self):
            """عرض قائمة الطلاب مع فلاتر ووصفحات"""
            pass
    
    @admin_ns.route('/students/bulk-create')
    class AdminBulkCreateStudents(Resource):
        @admin_ns.marshal_with(success_response_model, code=201)
        @admin_ns.doc('admin_bulk_create_students', security='Bearer')
        def post(self):
            """إنشاء طلاب متعددين من ملف Excel أو مصفوفة JSON"""
            pass
    
    @admin_ns.route('/rooms')
    class AdminRooms(Resource):
        @admin_ns.expect(room_model)
        @admin_ns.marshal_with(success_response_model, code=201)
        @admin_ns.doc('admin_create_room', security='Bearer')
        def post(self):
            """إنشاء قاعة جديدة مع إحداثيات ثلاثية الأبعاد"""
            pass
    
    @admin_ns.route('/rooms/<int:room_id>')
    class AdminRoom(Resource):
        @admin_ns.expect(room_model)
        @admin_ns.marshal_with(success_response_model, code=200)
        @admin_ns.doc('admin_update_room', security='Bearer')
        def put(self, room_id):
            """تحديث معلومات قاعة محددة"""
            pass
    
    # Attendance Namespace
    attendance_ns = Namespace('attendance', description='✅ Attendance Operations - عمليات الحضور')
    
    @attendance_ns.route('/generate-qr/<int:lecture_id>')
    class GenerateQR(Resource):
        @attendance_ns.marshal_with(success_response_model, code=201)
        @attendance_ns.doc('generate_qr', security='Bearer')
        def post(self, lecture_id):
            """توليد رمز QR ديناميكي لمحاضرة محددة"""
            pass
    
    batch_upload_model = api.model('BatchUpload', {
        'attendance_records': fields.List(fields.Nested(attendance_record_model), required=True),
        'batch_options': fields.Raw(description='خيارات المعالجة الجماعية')
    })
    
    @attendance_ns.route('/batch-upload')
    class BatchUploadAttendance(Resource):
        @attendance_ns.expect(batch_upload_model)
        @attendance_ns.marshal_with(success_response_model, code=200)
        @attendance_ns.doc('batch_upload_attendance', security='Bearer')
        def post(self):
            """رفع سجلات حضور متعددة بشكل جماعي"""
            pass
    
    @attendance_ns.route('/resolve-conflicts')
    class ResolveConflicts(Resource):
        @attendance_ns.marshal_with(success_response_model, code=200)
        @attendance_ns.doc('resolve_conflicts', security='Bearer')
        def post(self):
            """حل تعارضات بيانات الحضور"""
            pass
    
    @attendance_ns.route('/sync-status')
    class SyncStatus(Resource):
        @attendance_ns.marshal_with(success_response_model, code=200)
        @attendance_ns.doc('sync_status', security='Bearer')
        @attendance_ns.param('since_date', 'منذ تاريخ', required=False)
        def get(self):
            """الحصول على حالة مزامنة بيانات الحضور"""
            pass
    
    # Reports Namespace
    reports_ns = Namespace('reports', description='📊 Reports Operations - عمليات التقارير')
    
    @reports_ns.route('/attendance/summary')
    class AttendanceSummary(Resource):
        @reports_ns.marshal_with(success_response_model, code=200)
        @reports_ns.doc('attendance_summary', security='Bearer')
        @reports_ns.param('start_date', 'تاريخ البداية', required=False)
        @reports_ns.param('end_date', 'تاريخ النهاية', required=False)
        @reports_ns.param('section', 'فلتر الشعبة', required=False)
        @reports_ns.param('subject_id', 'فلتر المادة', required=False)
        def get(self):
            """تقرير ملخص الحضور مع فلاتر متقدمة"""
            pass
    
    @reports_ns.route('/student/<int:student_id>')
    class StudentDetailedReport(Resource):
        @reports_ns.marshal_with(success_response_model, code=200)
        @reports_ns.doc('student_detailed_report', security='Bearer')
        @reports_ns.param('start_date', 'تاريخ البداية', required=False)
        @reports_ns.param('end_date', 'تاريخ النهاية', required=False)
        def get(self, student_id):
            """تقرير مفصل لطالب محدد"""
            pass
    
    export_model = api.model('ExportReport', {
        'report_type': fields.String(required=True, description='نوع التقرير'),
        'export_format': fields.String(required=True, description='صيغة التصدير (csv, excel, json)'),
        'filters': fields.Raw(description='فلاتر التقرير')
    })
    
    @reports_ns.route('/export')
    class ExportReport(Resource):
        @reports_ns.expect(export_model)
        @reports_ns.doc('export_report', security='Bearer')
        def post(self):
            """تصدير التقارير بصيغ مختلفة"""
            pass
    
    # Health Namespace
    health_ns = Namespace('health', description='🏥 Health Check Operations - فحص صحة النظام')
    
    @health_ns.route('/')
    class HealthCheck(Resource):
        @health_ns.marshal_with(success_response_model, code=200)
        @health_ns.doc('health_check')
        def get(self):
            """فحص شامل لصحة النظام"""
            pass
    
    @health_ns.route('/simple')
    class SimpleHealthCheck(Resource):
        @health_ns.marshal_with(success_response_model, code=200)
        @health_ns.doc('simple_health_check')
        def get(self):
            """فحص بسيط لصحة النظام"""
            pass
    
    # ============================================================================
    # REGISTER NAMESPACES
    # ============================================================================
    
    api.add_namespace(auth_ns, path='/auth')
    api.add_namespace(student_ns, path='/student')
    api.add_namespace(rooms_ns, path='/rooms')
    api.add_namespace(admin_ns, path='/admin')
    api.add_namespace(attendance_ns, path='/attendance')
    api.add_namespace(reports_ns, path='/reports')
    api.add_namespace(health_ns, path='/health')
    
    return api

# ============================================================================
# ERROR HANDLERS
# ============================================================================

def setup_swagger_error_handlers(api):
    """Setup error handlers for Swagger"""
    
    @api.errorhandler
    def default_error_handler(error):
        """Default error handler"""
        return {
            'success': False,
            'error': {
                'code': 'API_ERROR',
                'message': str(error)
            }
        }, 500
    
    @api.errorhandler(404)
    def not_found_error(error):
        """Not found error handler"""
        return {
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'المورد المطلوب غير موجود'
            }
        }, 404
    
    @api.errorhandler(401)
    def unauthorized_error(error):
        """Unauthorized error handler"""
        return {
            'success': False,
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'غير مصرح - يرجى تسجيل الدخول'
            }
        }, 401
    
    @api.errorhandler(403)
    def forbidden_error(error):
        """Forbidden error handler"""
        return {
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'ممنوع - صلاحيات غير كافية'
            }
        }, 403

# Export setup function
__all__ = ['setup_swagger_docs', 'setup_swagger_error_handlers']