"""
Account Lockout System
نظام قفل الحسابات
"""
from datetime import datetime, timedelta
from typing import Optional
import redis
from config.database import db


class AccountLockoutManager:
    """Manage account lockouts after failed login attempts"""
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.StrictRedis(
            host='localhost',
            port=6380,
            db=3,  # Use db=3 for lockouts
            decode_responses=True
        )
        
        # Configuration
        self.MAX_ATTEMPTS = 5
        self.LOCKOUT_DURATION = timedelta(minutes=15)
        self.ATTEMPT_WINDOW = timedelta(minutes=15)

    def _get_key(self, identifier: str) -> str:
        """Get Redis key for identifier"""
        return f"lockout:{identifier}"

    def record_failed_attempt(self, identifier: str) -> tuple[bool, Optional[int]]:
        """
        Record a failed login attempt
        Returns: (is_locked, remaining_attempts)
        """
        key = self._get_key(identifier)
        
        try:
            # Get current attempts
            attempts = self.redis_client.incr(key)
            
            # Set expiry on first attempt
            if attempts == 1:
                self.redis_client.expire(key, int(self.ATTEMPT_WINDOW.total_seconds()))
            
            # Check if account should be locked
            if attempts >= self.MAX_ATTEMPTS:
                self._lock_account(identifier)
                return True, 0
            
            return False, self.MAX_ATTEMPTS - attempts
            
        except Exception as e:
            print(f"❌ Failed to record attempt: {e}")
            return False, self.MAX_ATTEMPTS

    def _lock_account(self, identifier: str):
        """Lock an account"""
        lock_key = f"{self._get_key(identifier)}:locked"
        lock_until = datetime.utcnow() + self.LOCKOUT_DURATION
        
        self.redis_client.setex(
            lock_key,
            int(self.LOCKOUT_DURATION.total_seconds()),
            lock_until.isoformat()
        )
        
        # Log the lockout
        self._log_lockout(identifier)

    def is_locked(self, identifier: str) -> tuple[bool, Optional[datetime]]:
        """
        Check if account is locked
        Returns: (is_locked, unlock_time)
        """
        lock_key = f"{self._get_key(identifier)}:locked"
        
        try:
            lock_data = self.redis_client.get(lock_key)
            if lock_data:
                unlock_time = datetime.fromisoformat(lock_data)
                if datetime.utcnow() < unlock_time:
                    return True, unlock_time
            
            return False, None
            
        except Exception as e:
            print(f"❌ Failed to check lock status: {e}")
            return False, None

    def reset_attempts(self, identifier: str):
        """Reset failed attempts for successful login"""
        try:
            self.redis_client.delete(self._get_key(identifier))
            self.redis_client.delete(f"{self._get_key(identifier)}:locked")
        except Exception as e:
            print(f"❌ Failed to reset attempts: {e}")

    def get_attempts_count(self, identifier: str) -> int:
        """Get current number of failed attempts"""
        try:
            attempts = self.redis_client.get(self._get_key(identifier))
            return int(attempts) if attempts else 0
        except Exception:
            return 0

    def _log_lockout(self, identifier: str):
        """Log account lockout event"""
        try:
            from models import User
            
            # Find user
            user = None
            if '@' in identifier:
                user = User.query.filter_by(email=identifier).first()
            else:
                user = User.query.filter_by(username=identifier).first()
            
            if user:
                # Update user record
                user.last_lockout = datetime.utcnow()
                db.session.commit()
                
            # Log to audit system
            print(f"⚠️ Account locked: {identifier} at {datetime.utcnow()}")
            
        except Exception as e:
            print(f"❌ Failed to log lockout: {e}")
