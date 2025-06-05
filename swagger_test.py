
from flask import Flask, jsonify
from datetime import datetime

try:
    from flask_restx import Api, Resource, fields
    
    app = Flask(__name__)
    api = Api(app, 
              title='Test API',
              description='Minimal Swagger Test',
              doc='/docs/')
    
    test_model = api.model('TestResponse', {
        'success': fields.Boolean(description='Success status'),
        'message': fields.String(description='Response message'),
        'timestamp': fields.String(description='Response timestamp')
    })
    
    @api.route('/test')
    class TestEndpoint(Resource):
        @api.marshal_with(test_model)
        def get(self):
            """Test endpoint to verify Swagger is working"""
            return {
                'success': True,
                'message': 'Swagger is working perfectly!',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Swagger Test Server',
            'swagger_url': '/docs/',
            'test_endpoint': '/test'
        })
    
    if __name__ == '__main__':
        print("🚀 Starting Swagger Test Server...")
        print("📚 Swagger UI: http://localhost:5001/docs/")
        print("🧪 Test endpoint: http://localhost:5001/test")
        app.run(debug=True, port=5001)

except ImportError as e:
    print(f"❌ Flask-RESTX not available: {e}")
    print("📦 Install with: pip install flask-restx")
