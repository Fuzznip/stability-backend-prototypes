from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from helper.helpers import Serializer
import uuid
    
class SP3Regions(db.Model, Serializer):
    __tablename__ = 'sp3_regions'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id', ondelete="CASCADE"))  # Cascade delete
    region_name = db.Column(db.String, nullable=False)
    region_description = db.Column(db.Text)
    region_image = db.Column(db.String)
    region_challenges = db.Column(ARRAY(db.String))
    
    
    def serialize(self):
        return Serializer.serialize(self)
    
class SP3EventTiles(db.Model, Serializer):
    __tablename__ = 'sp3_event_tiles'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id', ondelete="CASCADE"))  # Cascade delete
    tile_name = db.Column(db.String, nullable=False)
    tile_description = db.Column(db.Text)
    tile_image = db.Column(db.String)
    tile_points = db.Column(db.Integer, nullable=False)
    tile_type = db.Column(db.String, nullable=False)
    tile_challenges = db.Column(ARRAY(db.String))
    
    def serialize(self):
        return Serializer.serialize(self)
