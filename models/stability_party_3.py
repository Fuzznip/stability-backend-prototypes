from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from helper.helpers import Serializer
import uuid
    
class SP3Regions(db.Model, Serializer):
    __tablename__ = 'sp3_regions'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id', ondelete="CASCADE"))  # Cascade delete
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String)
    challenges = db.Column(ARRAY(db.String))
    coordinates = db.Column(JSONB)  # Store coordinates as JSONB for flexibility
    data = db.Column(JSONB)  # Store additional data as JSONB for flexibility
    
    def serialize(self):
        return Serializer.serialize(self)
    
class SP3EventTiles(db.Model, Serializer):
    __tablename__ = 'sp3_event_tiles'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id', ondelete="CASCADE"))  # Cascade delete
    region_id = db.Column(UUID(as_uuid=True), db.ForeignKey('sp3_regions.id', ondelete="CASCADE"))  # Cascade delete
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String)
    points = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String, nullable=False)
    coordinates = db.Column(JSONB)  # Store coordinates as JSONB for flexibility
    data = db.Column(JSONB)  # Store additional data as JSONB for flexibility
    
    def serialize(self):
        return Serializer.serialize(self)
    
class SP3EventTileChallengeMapping(db.Model, Serializer):
    __tablename__ = 'sp3_event_tile_challenge_mapping'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tile_id = db.Column(UUID(as_uuid=True), db.ForeignKey('sp3_event_tiles.id', ondelete="CASCADE"))  # Cascade delete
    challenge_id = db.Column(UUID(as_uuid=True), db.ForeignKey('challenges.id', ondelete="CASCADE"))  # Cascade delete
    type = db.Column(db.String, nullable=False)  # Type of challenge (e.g., "TILE", "ISLAND", "COIN")
    data = db.Column(JSONB)  # Store challenge-specific data as JSONB for flexibility

    def serialize(self):
        return Serializer.serialize(self)
