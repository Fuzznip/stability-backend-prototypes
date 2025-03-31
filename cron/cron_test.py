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

def cron_test():
    """
    Test function to verify the cron job setup.
    Returns a success message.
    """
    logging.info("Running cron test")
    # You can add any test logic here, such as querying the database or performing calculations.
    # For now, we'll just log a message and return a success response.
    
    logging.info("Cron test completed successfully")
    return "Cron test completed successfully"
