"""
Base Model Class
الفئة الأساسية لجميع النماذج
"""

from datetime import datetime
from config.database import db

class BaseModel(db.Model):
    """Base model class with common fields and methods"""
    
    __abstract__ = True
    
    # Common fields for all models
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def save(self):
        """Save the model to database"""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self):
        """Delete the model from database"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def to_dict(self):
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    @classmethod
    def find_by_id(cls, id):
        """Find record by ID"""
        return cls.query.filter_by(id=id).first()
    
    @classmethod
    def find_all(cls):
        """Find all records"""
        return cls.query.all()
