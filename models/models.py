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
    alt_names = db.Column(ARRAY(db.String))
    is_member = db.Column(db.Boolean)
    rank = db.Column(db.String)
    rank_points = db.Column(db.Integer)
    progression_data = db.Column(JSONB)
    achievements = db.Column(ARRAY(db.String))
    join_date = db.Column(db.DateTime)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    is_active = db.Column(db.Boolean, default=True)
    diary_points = db.Column(db.Integer, default=0)
    event_points = db.Column(db.Integer, default=0)
    time_points = db.Column(db.Integer, default=0)
    split_points = db.Column(db.Integer, default=0)
    settings = db.Column(JSONB, default={})

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

class Splits(db.Model, Serializer):
    __tablename__ = 'splits'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.discord_id'))
    item_name = db.Column(db.String, nullable=False)
    item_price = db.Column(db.Numeric, nullable=False)
    item_id = db.Column(db.String, nullable=False)
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

class ClanRanks(db.Model, Serializer):
    __tablename__ = 'clan_ranks'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rank_name = db.Column(db.String, nullable=False)
    rank_minimum_points = db.Column(db.Integer, nullable=False)
    rank_minimum_days = db.Column(db.Integer, nullable=False)
    rank_order = db.Column(db.Integer, nullable=False)
    rank_icon = db.Column(db.String)
    rank_color = db.Column(db.String)
    rank_description = db.Column(db.Text)
    rank_requirements = db.Column(ARRAY(db.String))

    def serialize(self):
        return Serializer.serialize(self)

class RaidTiers(db.Model, Serializer):
    __tablename__ = 'raid_tiers'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tier_name = db.Column(db.String, nullable=False)
    tier_order = db.Column(db.Integer, nullable=False)
    tier_icon = db.Column(db.String)
    tier_color = db.Column(db.String)
    tier_description = db.Column(db.Text)
    tier_requirements = db.Column(db.Text)
    tier_points = db.Column(db.Integer, nullable=False)

    def serialize(self):
        return Serializer.serialize(self)

class Achievements(db.Model, Serializer):
    __tablename__ = 'achievements'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.discord_id'))
    achievement_name = db.Column(db.String, nullable=False)
    achievement_points = db.Column(db.Integer, nullable=False)
    achievement_color = db.Column(db.String)
    achievement_image = db.Column(db.String)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)

class RankApplications(db.Model, Serializer):
    __tablename__ = 'rank_applications'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String)
    runescape_name = db.Column(db.String, nullable=False)
    desired_rank = db.Column(db.String, nullable=False)
    proof = db.Column(db.String)
    status = db.Column(db.String, default='Pending')
    verdict_reason = db.Column(db.Text)
    verdict_timestamp = db.Column(db.DateTime)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)

class TierApplications(db.Model, Serializer):
    __tablename__ = 'tier_applications'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String)
    runescape_name = db.Column(db.String, nullable=False)
    desired_tier = db.Column(db.String, nullable=False)
    proof = db.Column(db.String)
    status = db.Column(db.String, default='Pending')
    verdict_reason = db.Column(db.Text)
    verdict_timestamp = db.Column(db.DateTime)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)

class BossDictionary(db.Model, Serializer):
    __tablename__ = 'boss_dictionary'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, nullable=False)
    shorthand = db.Column(db.String, nullable=False)
    icon = db.Column(db.String)

    def serialize(self):
        return Serializer.serialize(self)

class TimeSplitApplications(db.Model, Serializer):
    __tablename__ = 'time_splits'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.discord_id'))
    boss_name = db.Column(db.String, nullable=False)
    split = db.Column(db.String, nullable=False)
    players = db.Column(ARRAY(db.String))
    scale = db.Column(db.String)
    proof = db.Column(db.String)
    verification_status = db.Column(db.String, default='Pending')
    verification_reason = db.Column(db.Text)
    verification_timestamp = db.Column(db.DateTime)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)

class DiaryTasks(db.Model, Serializer):
    __tablename__ = 'diary_content'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diary_name = db.Column(db.String, nullable=False)
    diary_shorthand = db.Column(db.String)
    boss_name = db.Column(db.String)
    scale = db.Column(db.String)
    diary_description = db.Column(db.Text)
    diary_time = db.Column(db.String)
    diary_points = db.Column(db.Integer, nullable=False)

    def serialize(self):
        return Serializer.serialize(self)

class DiaryApplications(db.Model, Serializer):
    __tablename__ = 'diary_applications'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.discord_id'))
    runescape_name = db.Column(db.String, nullable=False)
    diary_name = db.Column(db.String, nullable=False)
    diary_shorthand = db.Column(db.String, nullable=False)
    party = db.Column(ARRAY(db.String))
    party_ids = db.Column(ARRAY(db.String))
    time_split = db.Column(db.String)
    proof = db.Column(db.String)
    status = db.Column(db.String, default='Pending')
    target_diary_id = db.Column(UUID(as_uuid=True), db.ForeignKey('diary_content.id'))
    verdict_reason = db.Column(db.Text)
    verdict_timestamp = db.Column(db.DateTime)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)
    
class DiaryCompletionLog(db.Model, Serializer):
    __tablename__ = 'diary_log'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.discord_id'))
    diary_id = db.Column(UUID(as_uuid=True), db.ForeignKey('diary_content.id'))
    diary_category_shorthand = db.Column(db.String)
    party = db.Column(ARRAY(db.String))
    party_ids = db.Column(ARRAY(db.String))
    proof = db.Column(db.String)
    time_split = db.Column(db.String)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)

class ClanPointsLog(db.Model, Serializer):
    __tablename__ = 'clan_points_log'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String, db.ForeignKey('users.discord_id'))
    points = db.Column(db.Numeric, nullable=False)
    tag = db.Column(db.String)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def serialize(self):
        return Serializer.serialize(self)
