"""
JWT Authentication System
نظام المصادقة باستخدام JWT مع RS256
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g, current_app
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import uuid
import redis
import os

class JWTManager:
    """
    JWT Management with RS256 algorithm
    """
    def __init__(self, app=None):
        self.app = app
        self.private_key = None
        self.public_key = None
        self.blacklist_store = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize JWT Manager with Flask app"""
        self.app = app
        
        # JWT Configuration
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=2))
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30))
        app.config.setdefault('JWT_ALGORITHM', 'RS256')
        app.config.setdefault('JWT_PRIVATE_KEY_PATH', 'keys/private_key.pem')
        app.config.setdefault('JWT_PUBLIC_KEY_PATH', 'keys/public_key.pem')
        
        # Load or generate keys
        self._load_or_generate_keys()
        
        # Setup Redis for blacklist
        try:
            self.blacklist_store = redis.StrictRedis(
                host='localhost',
                port=6379,
                db=1,  # Use db=1 for blacklist
                decode_responses=True
            )
            self.blacklist_store.ping()
        except Exception as e:
            print(f"⚠️ Redis blacklist not available: {e}")
            self.blacklist_store = None

    def _load_or_generate_keys(self):
        """Load RSA keys or generate new ones"""
        private_key_path = self.app.config['JWT_PRIVATE_KEY_PATH']
        public_key_path = self.app.config['JWT_PUBLIC_KEY_PATH']
        
        # Create keys directory if not exists
        os.makedirs(os.path.dirname(private_key_path), exist_ok=True)
        
        try:
            # Try to load existing keys
            with open(private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            with open(public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(), backend=default_backend()
                )
            print("✅ Loaded existing RSA keys")
            
        except FileNotFoundError:
            # Generate new keys
            print("🔑 Generating new RSA keys...")
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            
            # Save private key
            with open(private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Save public key
            with open(public_key_path, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            
            self.private_key = private_key
            self.public_key = public_key
            print("✅ Generated and saved new RSA keys")

    def generate_tokens(self, user, device_fingerprint=None):
        """Generate access and refresh tokens"""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role.value,
            'device_fingerprint': device_fingerprint,
            'jti': str(uuid.uuid4()),  # JWT ID for blacklisting
            'iat': now,
            'exp': now + self.app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }
        
        # Add student-specific data
        if hasattr(user, 'get_student_profile'):
            student = user.get_student_profile()
            if student:
                access_payload['university_id'] = student.university_id
                access_payload['student_id'] = student.id
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'token_family': str(uuid.uuid4()),
            'jti': str(uuid.uuid4()),
            'iat': now,
            'exp': now + self.app.config['JWT_REFRESH_TOKEN_EXPIRES']
        }
        
        # Generate tokens
        access_token = jwt.encode(
            access_payload,
            self.private_key,
            algorithm=self.app.config['JWT_ALGORITHM']
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            self.private_key,
            algorithm=self.app.config['JWT_ALGORITHM']
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': int(self.app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
        }

    def decode_token(self, token):
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.app.config['JWT_ALGORITHM']]
            )
            
            # Check if token is blacklisted
            if self.blacklist_store and self.is_token_blacklisted(payload.get('jti')):
                return None, "Token has been revoked"
            
            return payload, None
            
        except jwt.ExpiredSignatureError:
            return None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return None, f"Invalid token: {str(e)}"

    def blacklist_token(self, jti, expires_at):
        """Add token to blacklist"""
        if self.blacklist_store:
            # Calculate TTL (time to live)
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            if ttl > 0:
                self.blacklist_store.setex(f"blacklist:{jti}", ttl, "1")
                return True
        return False

    def is_token_blacklisted(self, jti):
        """Check if token is blacklisted"""
        if self.blacklist_store and jti:
            return self.blacklist_store.exists(f"blacklist:{jti}")
        return False

jwt_manager = JWTManager()

def jwt_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ', 1)[1]
        
        # Decode token
        payload, error = jwt_manager.decode_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        # Set current user in g
        g.current_user_id = payload['user_id']
        g.current_user_role = payload['role']
        g.jwt_payload = payload
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current authenticated user"""
    from models import User
    if hasattr(g, 'current_user_id'):
        return User.query.get(g.current_user_id)
    return None
