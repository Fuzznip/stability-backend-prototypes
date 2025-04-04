from enum import Enum
from models.models import Users, ClanPointsLog, db
import datetime

class PointTag(Enum):
    DIARY = "diary"
    TIME = "time"
    SPLIT = "split"
    EVENT = "event"

def increment_clan_points(user_id, points, tag: PointTag, message=None):
    """
    Updates clan points for a user and logs the change in the ClanPointsLog.

    :param user_id: The ID of the user to update points for.
    :param points: The number of points to add (positive) or remove (negative).
    :param tag: The type of points being updated (diary, time, split, or event).
    """
    user = Users.query.filter_by(discord_id=user_id).first()
    if not user:
        raise ValueError("User not found")

    # Update the appropriate points field based on the tag
    if tag == PointTag.DIARY:
        user.diary_points += points
    elif tag == PointTag.TIME:
        user.time_points += points
    elif tag == PointTag.SPLIT:
        user.split_points += points
    elif tag == PointTag.EVENT:
        user.event_points += points
    else:
        raise ValueError("Invalid tag")
    
    user.rank_points += points

    # Log the points update in ClanPointsLog
    log_entry = ClanPointsLog(
        user_id=user_id,
        points=points,
        tag= message if message else tag.value,
        timestamp=datetime.datetime.now()
    )
    db.session.add(log_entry)

    # Commit the changes to the database
    db.session.commit()
