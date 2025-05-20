import uuid
import logging
import requests
from models.models import Events, EventTeams

def send_event_notification(event_id: uuid, team_id: uuid, title: str, message: str) -> None:
    event = Events.query.filter_by(id=event_id).first()
    team = EventTeams.query.filter_by(id=team_id).first()
    webhook = event.data.get("webhook")
    if webhook:
        # Placeholder for sending a notification to the event's webhook
        logging.info(f"Sending notification to {webhook}: {title} - {message}")
        image_url = team.image if team.image else "https://i.imgur.com/SBTOvfk.png"

        data = {
            "embeds": [
                {
                    "title": title,
                    "description": f"{team.name} has {message}",
                    "color": 0x992D22,  # Example color
                    "thumbnail": {
                        "url": image_url
                    },
                }
            ]
        }

        requests.post(webhook, json=data)
    else:
        logging.warning(f"No webhook URL found for event {event.id}. Cannot send notification.")
        return