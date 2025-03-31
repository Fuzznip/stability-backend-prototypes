from app import db
from models.models import Users, ClanPointsLog
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/weekly_points.log")
    ]
)

def update_weekly_points():
    """
    Updates points for active members who have been in the clan for a multiple of 7 days.
    Returns the number of users who received points.
    """
    logging.info("Starting weekly points update")
    users = Users.query.all()
    count = 0
    
    for user in users:
        if user.is_active and user.is_member and user.join_date:
            # Calculate days since join
            today = datetime.now().date()
            join_date = user.join_date.date() if isinstance(user.join_date, datetime) else user.join_date
            days_since_join = (today - join_date).days
            
            # Check if it's a multiple of 7
            if days_since_join > 0:
                user.time_points = days_since_join // 7 * 10
                count += 1

                # Log the points
                log_entry = ClanPointsLog(user_id=user.discord_id, points=10, tag="Weekly Points")
                db.session.add(log_entry)
                
                logging.info(f"Added 10 points to user {user.discord_id} ({user.runescape_name}) - {days_since_join} days membership")
    
    db.session.commit()
    logging.info(f"Added weekly points to {count} users")
    return count

if __name__ == "__main__":
    try:
        count = update_weekly_points()
        print(f"Weekly points update successful: {count} users updated")
        exit(0)
    except Exception as e:
        logging.error(f"Error in weekly points update: {str(e)}", exc_info=True)
        print(f"Weekly points update failed: {str(e)}")
        exit(1)
