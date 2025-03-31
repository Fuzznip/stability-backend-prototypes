import sys
import os

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from app import db
from models.models import Users, ClanPointsLog
from datetime import datetime
import logging

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(logs_dir, "weekly_points.log"))
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

if __name__ == "__main__":
    try:
        message = cron_test()
        print(message)
        exit(0)
    except Exception as e:
        logging.error(f"Error in cron test: {str(e)}", exc_info=True)
        print(f"Cron test failed: {str(e)}")
        exit(1)
