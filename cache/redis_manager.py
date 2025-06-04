"""
Redis Cache Manager
إدارة التخزين المؤقت باستخدام Redis
"""

import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from config.database import redis_client

class RedisManager:
    """Redis cache manager for the application"""
    
    # Cache key prefixes
    PREFIXES = {
        'qr_session': 'qr:session:',
        'student_auth': 'auth:student:',
        'teacher_auth': 'auth:teacher:',
        'room_data': 'room:data:',
        'schedule_data': 'schedule:data:',
    }
    
    # Default TTL values (in seconds)
    TTL = {
        'qr_session': 300,      # 5 minutes
        'student_auth': 7200,   # 2 hours
        'teacher_auth': 7200,   # 2 hours
        'room_data': 86400,     # 24 hours
        'schedule_data': 43200, # 12 hours
    }
    
    @classmethod
    def _get_key(cls, prefix: str, identifier: str) -> str:
        """Generate Redis key with prefix"""
        return f"{cls.PREFIXES[prefix]}{identifier}"
    
    @classmethod
    def set_data(cls, prefix: str, identifier: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Set data in Redis cache"""
        try:
            key = cls._get_key(prefix, identifier)
            ttl = ttl or cls.TTL.get(prefix, 3600)
            
            # Serialize data
            if isinstance(data, (dict, list)):
                serialized_data = json.dumps(data, default=str)
            else:
                serialized_data = pickle.dumps(data)
                
            redis_client.setex(key, ttl, serialized_data)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

def test_redis_connection():
    """Test Redis connection and basic operations"""
    try:
        redis_client.ping()
        print("✅ Redis connection successful")
        
        # Test basic operations
        test_key = "test:connection"
        test_data = {"message": "Hello Redis", "timestamp": datetime.utcnow().isoformat()}
        
        redis_client.setex(test_key, 60, json.dumps(test_data))
        retrieved_data = redis_client.get(test_key)
        
        if retrieved_data:
            parsed_data = json.loads(retrieved_data)
            print(f"✅ Redis operations successful: {parsed_data['message']}")
            redis_client.delete(test_key)
            return True
        else:
            print("❌ Redis get operation failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False

def clear_all_cache():
    """Clear all application cache (use with caution)"""
    try:
        # Get all keys with our prefixes
        all_keys = []
        for prefix in RedisManager.PREFIXES.values():
            keys = redis_client.keys(f"{prefix}*")
            all_keys.extend(keys)
        
        if all_keys:
            redis_client.delete(*all_keys)
            print(f"✅ Cleared {len(all_keys)} cache entries")
        else:
            print("ℹ️ No cache entries to clear")
            
        return True
    except Exception as e:
        print(f"❌ Failed to clear cache: {e}")
        return False
