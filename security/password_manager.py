"""
Password Security System
نظام أمان كلمات المرور
"""
import bcrypt
import re
import secrets
import string
from passlib.context import CryptContext


class PasswordManager:
    """Advanced password management with bcrypt"""

    # Password context with bcrypt
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=12  # 12 rounds for good security/performance balance
    )

    # Password requirements
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True

    @classmethod
    def validate_password_strength(cls, password):
        """Validate password meets security requirements"""
        errors = []

        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")

        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if cls.REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        return len(errors) == 0, errors

    @classmethod
    def hash_password(cls, password):
        """Hash password with bcrypt"""
        # Validate password strength
        is_valid, errors = cls.validate_password_strength(password)
        if not is_valid:
            raise ValueError(f"Weak password: {', '.join(errors)}")

        # Hash password
        return cls.pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain_password, hashed_password):
        """Verify password against hash"""
        try:
            return cls.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    @classmethod
    def needs_rehash(cls, hashed_password):
        """Check if password hash needs to be updated"""
        return cls.pwd_context.needs_update(hashed_password)

    @classmethod
    def generate_secure_password(cls, length=12):
        """Generate a secure random password"""
        # Define character sets
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*"

        # Ensure at least one character from each required set
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]

        # Fill the rest with random characters
        all_chars = uppercase + lowercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))

        # Shuffle the password
        secrets.SystemRandom().shuffle(password)

        return ''.join(password)

    @classmethod
    def generate_secret_code(cls, length=8):
        """Generate alphanumeric secret code for students"""
        characters = string.ascii_uppercase + string.digits
        # Avoid confusing characters
        characters = characters.replace('O', '').replace('0', '')
        characters = characters.replace('I', '').replace('1', '')

        return ''.join(secrets.choice(characters) for _ in range(length))
