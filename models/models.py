from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from helper.helpers import Serializer
import uuid
import datetime


class Users(db.Model, Serializer):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discord_id = db.Column(db.String, unique=True, nullable=False)
    runescape_name = db.Column(db.String, nullable=False)
    previous_names = db.Column(ARRAY(db.String))
    is_member = db.Column(db.Boolean)
    rank = db.Column(db.String)
    rank_points = db.Column(db.Integer)
    progression_data = db.Column(JSONB)
    join_date = db.Column(db.DateTime)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)


class Leaderboard(db.Model, Serializer):
    __tablename__ = 'leaderboard'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.discord_id'))
    diary_points = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)


class Announcements(db.Model, Serializer):
    __tablename__ = 'announcements'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = db.Column(db.String, db.ForeignKey('users.discord_id'))
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    is_pinned = db.Column(db.Boolean)

    def serialize(self):
        return Serializer.serialize(self)


class Killcount(db.Model, Serializer):
    __tablename__ = 'killcount'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.discord_id'))
    boss_name = db.Column(db.String)
    kill_count = db.Column(db.Integer)
    personal_best = db.Column(db.String)
    scale = db.Column(db.Integer)
    group = db.Column(JSONB)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)


class Webhook:

    def __init__(self, discord_id, rank):
        self.discord_id = discord_id
        self.rank = rank


class Splits(db.Model, Serializer):
    __tablename__ = 'splits'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.discord_id'))
    item_name = db.Column(db.String, nullable=False)
    item_price = db.Column(db.Numeric, nullable=False)
    split_contribution = db.Column(db.Numeric, nullable=False)
    group_size = db.Column(db.Integer, nullable=False)
    screenshot_link = db.Column(db.String)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)

class ClanApplications(db.Model, Serializer):
    __tablename__ = 'applications'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String)
    runescape_name = db.Column(db.String, nullable=False)
    referral = db.Column(db.String)
    reason = db.Column(db.Text)
    goals = db.Column(db.Text)
    status = db.Column(db.String, default='Pending')
    verdict_reason = db.Column(db.Text)
    verdict_timestamp = db.Column(db.DateTime)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)

