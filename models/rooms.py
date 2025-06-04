"""
ROOMS Model
نموذج القاعات ثلاثية الأبعاد مع GPS
"""

from config.database import db
from .base import BaseModel
from enum import Enum
import json

class RoomTypeEnum(Enum):
    """Room type enumeration"""
    CLASSROOM = 'classroom'
    LAB = 'lab'
    AUDITORIUM = 'auditorium'

class Room(BaseModel):
    """Room model with 3D coordinates and GPS polygon"""
    
    __tablename__ = 'rooms'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Information
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)  # A101, B205
    building = db.Column(db.String(100), nullable=False, index=True)
    floor = db.Column(db.Integer, nullable=False, index=True)
    room_type = db.Column(db.Enum(RoomTypeEnum), default=RoomTypeEnum.CLASSROOM)
    capacity = db.Column(db.Integer, default=30)
    
    # GPS Coordinates (Geographic)
    center_latitude = db.Column(db.Numeric(10, 8), nullable=False)
    center_longitude = db.Column(db.Numeric(11, 8), nullable=False)
    gps_polygon = db.Column(db.JSON, nullable=False)  # Array of polygon points
    
    # Altitude Coordinates (Vertical)
    ground_reference_altitude = db.Column(db.Numeric(8, 3), nullable=False)
    floor_altitude = db.Column(db.Numeric(8, 3), nullable=False)
    ceiling_height = db.Column(db.Numeric(5, 2), nullable=False)
    barometric_pressure_reference = db.Column(db.Numeric(8, 2), nullable=True)
    
    # Additional Information
    wifi_ssid = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def set_rectangular_polygon(self, center_lat, center_lng, width_meters=10, height_meters=8):
        """Set a rectangular GPS polygon around the center point"""
        # Convert meters to approximate degrees (rough calculation)
        lat_offset = width_meters / 111000  # 1 degree ≈ 111km
        lng_offset = height_meters / (111000 * abs(center_lat))  # Adjust for latitude
        
        polygon_points = [
            [center_lat + lat_offset, center_lng - lng_offset],  # Top-left
            [center_lat + lat_offset, center_lng + lng_offset],  # Top-right
            [center_lat - lat_offset, center_lng + lng_offset],  # Bottom-right
            [center_lat - lat_offset, center_lng - lng_offset],  # Bottom-left
            [center_lat + lat_offset, center_lng - lng_offset]   # Close polygon
        ]
        
        self.gps_polygon = polygon_points
    
    def is_point_inside_polygon(self, latitude, longitude):
        """Check if a point is inside the room's GPS polygon"""
        try:
            from shapely.geometry import Point, Polygon
            point = Point(latitude, longitude)
            polygon = Polygon(self.gps_polygon)
            return polygon.contains(point)
        except ImportError:
            # Fallback to simple distance check if shapely not available
            return self.distance_from_center(latitude, longitude) <= 10  # 10 meters
    
    def distance_from_center(self, latitude, longitude):
        """Calculate distance from center in meters"""
        import math
        
        lat1, lng1 = float(self.center_latitude), float(self.center_longitude)
        lat2, lng2 = latitude, longitude
        
        # Haversine formula
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlng/2) * math.sin(dlng/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = 6371000 * c  # Earth radius in meters
        
        return distance
    
    def is_altitude_match(self, student_altitude, tolerance=2.0):
        """Check if student altitude matches room floor"""
        min_altitude = float(self.floor_altitude) - tolerance
        max_altitude = float(self.floor_altitude) + float(self.ceiling_height) + tolerance
        return min_altitude <= student_altitude <= max_altitude
    
    def to_dict_with_gps(self):
        """Convert to dictionary including GPS data"""
        data = super().to_dict()
        data['room_type'] = self.room_type.value if self.room_type else None
        data['center_latitude'] = float(self.center_latitude)
        data['center_longitude'] = float(self.center_longitude)
        data['floor_altitude'] = float(self.floor_altitude)
        data['ceiling_height'] = float(self.ceiling_height)
        return data
    
    @classmethod
    def find_by_name(cls, name):
        """Find room by name"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_by_building_and_floor(cls, building, floor):
        """Get rooms by building and floor"""
        return cls.query.filter_by(building=building, floor=floor, is_active=True).all()
    
    @classmethod
    def get_active_rooms(cls):
        """Get all active rooms"""
        return cls.query.filter_by(is_active=True).all()
    
    def __repr__(self):
        return f'<Room {self.name} - {self.building} Floor {self.floor}>'