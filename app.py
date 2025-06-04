"""
Main Application File
الملف الرئيسي للتطبيق - Windows Compatible
"""

from flask import Flask, jsonify
from config.database import DatabaseConfig

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(DatabaseConfig)
    
    # Initialize extensions
    DatabaseConfig.init_app(app)
    
    @app.route('/')
    def index():
        return "Smart Attendance System - Level 1: Database Foundation (Windows)"
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy", 
            "level": "Database Foundation",
            "platform": "Windows"
        })
    
    @app.route('/test')
    def test():
        """Test database connection"""
        try:
            db_status = DatabaseConfig.test_connection()
            redis_status = DatabaseConfig.test_redis()
            
            return jsonify({
                "database": "connected" if db_status else "disconnected",
                "redis": "connected" if redis_status else "disconnected",
                "overall": "healthy" if (db_status and redis_status) else "unhealthy"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Starting Flask application on Windows...")
    print("📍 Available endpoints:")
    print("   http://localhost:5000/ - Main page")
    print("   http://localhost:5000/health - Health check")
    print("   http://localhost:5000/test - Database test")
    app.run(debug=True, host='0.0.0.0', port=5000)
