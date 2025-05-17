from app import app
from helper.helpers import ModelEncoder
from models.models import Events, EventTriggers, EventTriggerMappings
import json
import logging
from datetime import datetime, timedelta, timezone

@app.route("/events/whitelist", methods=['GET'])
def get_item_whitelist():
    data = {
        "triggers": [],
        "killCountTriggers": [],
        "messageFilters": []
    }

    # Fetch all currently running events and events starting in the next 24 hours
    now = datetime.now(timezone.utc)
    next_24_hours = now + timedelta(hours=24)
    running_events = Events.query.filter(Events.start_time <= next_24_hours).filter(now < Events.end_time).all()

    if not running_events:
        return "No events found", 404
    
    event_ids = [event.id for event in running_events]
    trigger_mappings = EventTriggerMappings.query.filter(EventTriggerMappings.event_id.in_(event_ids)).all()
    trigger_ids = [mapping.trigger_id for mapping in trigger_mappings]
    triggers = EventTriggers.query.filter(EventTriggers.id.in_(trigger_ids)).all()

    triggerSet = set()
    messageFilterSet = set()
    killCountTriggerSet = set()

    for trigger in triggers:
        if trigger.type == "DROP":
            # Construct the key based on trigger and source
            triggerSet.add(f"{trigger.trigger}:{trigger.source}" if trigger.source else f"{trigger.trigger}")
        elif trigger.type == "KC":
            messageFilterSet.add(f"{trigger.trigger}")
            killCountTriggerSet.add(trigger.trigger)
        else:
            logging.warning(f"Unknown trigger type: {trigger.type}")
            pass

    data["triggers"] = list(triggerSet)
    data["killCountTriggers"] = list(killCountTriggerSet)
    data["messageFilters"] = list(messageFilterSet)
    return json.dumps(data, cls=ModelEncoder)
