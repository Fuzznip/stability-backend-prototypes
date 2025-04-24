from app import app, db
from helper.helpers import ModelEncoder
from models.models import Events
from models.stability_party_3 import SP3EventTriggers
import json
import logging
from datetime import datetime, timedelta, timezone

@app.route("/events/whitelist", methods=['GET'])
def get_item_whitelist():
    data = {
        "triggerDictionary": {},
        "messageFilters": {}
    }

    # Fetch all currently running events and events starting in the next 24 hours
    now = datetime.now(timezone.utc)
    next_24_hours = now + timedelta(hours=24)
    running_events = Events.query.filter(Events.start_time <= next_24_hours).filter(now < Events.end_time).all()

    if not running_events:
        return "No events found", 404

    for event in running_events:
        # Fetch all triggers referencing the event
        triggers = SP3EventTriggers.query.filter_by(event_id=event.id).all()

        for trigger in triggers:
            if trigger.type == "DROP":
                # Construct the key based on trigger and source
                key = f"{trigger.trigger}:{trigger.source}" if trigger.source else f"{trigger.trigger}"
                
                # Append the event thread id to the dictionary
                if key not in data["triggerDictionary"]:
                    data["triggerDictionary"][key] = []
                data["triggerDictionary"][key].append(event.thread_id)
            elif trigger.type == "KC":
                # Construct the key based on trigger and source
                key = f"{trigger.trigger}:{trigger.source}" if trigger.source else f"{trigger.trigger}"
                
                # Append the event thread id to the dictionary
                if key not in data["messageFilters"]:
                    data["messageFilters"][key] = []
                data["messageFilters"][key].append(event.thread_id)
            else:
                logging.warning(f"Unknown trigger type: {trigger.type} for event {event.id}")
                pass

    return json.dumps(data, cls=ModelEncoder)
