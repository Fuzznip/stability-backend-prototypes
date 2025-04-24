from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from helper.helpers import Serializer
import uuid
import datetime
    
class SP3EventTeams(db.Model, Serializer):
    __tablename__ = 'sp3_event_teams'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id', ondelete="CASCADE"))  # Cascade delete
    team_name = db.Column(db.String, nullable=False)
    team_image = db.Column(db.String)
    team_members = db.Column(ARRAY(db.String))
    team_captain = db.Column(db.String)
    data = db.Column(JSONB, default={})

    def serialize(self):
        return Serializer.serialize(self)
    
class SP3Regions(db.Model, Serializer):
    __tablename__ = 'sp3_regions'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id', ondelete="CASCADE"))  # Cascade delete
    region_name = db.Column(db.String, nullable=False)
    region_description = db.Column(db.Text)
    region_image = db.Column(db.String)
    
    def serialize(self):
        return Serializer.serialize(self)
    
class SP3EventTiles(db.Model, Serializer):
    __tablename__ = 'sp3_event_tiles'  # Changed to avoid conflict
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
    
class SP3EventChallenges(db.Model, Serializer):
    __tablename__ = 'sp3_event_challenges'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id', ondelete="CASCADE"))  # Cascade delete
    challenge_name = db.Column(db.String, nullable=False)
    
    def serialize(self):
        return Serializer.serialize(self)
    
class SP3EventTasks(db.Model, Serializer):
    __tablename__ = 'sp3_event_tasks'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id', ondelete="CASCADE"))  # Cascade delete
    task_name = db.Column(db.String, nullable=False)
    task_description = db.Column(db.Text)
    task_image = db.Column(db.String)
    task_points = db.Column(db.Integer, nullable=False)
    task_type = db.Column(db.String, nullable=False)
    
    def serialize(self):
        return Serializer.serialize(self)
    
class SP3EventTriggers(db.Model, Serializer):
    __tablename__ = 'sp3_event_triggers'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id', ondelete="CASCADE"))  # Cascade delete
    trigger = db.Column(db.String, nullable=False)
    source = db.Column(db.String)
    type = db.Column(db.String, nullable=False)
    
    def serialize(self):
        return Serializer.serialize(self)
