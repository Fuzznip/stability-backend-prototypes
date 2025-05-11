from app import app, db
from flask import request, jsonify
from models.models import Events, EventTeams
from datetime import datetime, timezone
from helper.helpers import ModelEncoder
import json
import logging

@app.route("/events", methods=['GET'])
def get_events():
    """
    Get a list of events with optional filtering
    
    Query parameters:
    - status: Filter events by status ("active", "upcoming", "all")
    - after: ISO format datetime to filter events starting after this time
    """
    try:
        status = request.args.get('status', 'all')
        after_str = request.args.get('after')
        
        query = Events.query
        
        # Apply filters based on status
        now = datetime.now() # It's ok to be naive here, as we are not using timezone-aware datetimes in the database
        if status.lower() == 'active':
            # Return events that are currently active (start time in past, end time in future)
            query = query.filter(Events.start_time <= now, Events.end_time >= now)
        elif status.lower() == 'upcoming':
            # Return events that haven't started yet
            query = query.filter(Events.start_time > now)
        
        # Apply filter for events starting after a specific time
        if after_str:
            try:
                after_time = datetime.fromisoformat(after_str.replace('Z', '+00:00'))
                query = query.filter(Events.start_time >= after_time)
            except ValueError:
                return jsonify({"error": "Invalid datetime format for 'after' parameter. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
        
        # Order by start time
        events = query.order_by(Events.start_time).all()
            
        return json.dumps([event.serialize() for event in events], cls=ModelEncoder), 200
    except Exception as e:
        logging.error(f"Error getting events: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/events/<event_id>", methods=['GET'])
def get_event_by_id(event_id):
    """Get details for a specific event"""
    try:
        event = Events.query.filter_by(id=event_id).first()
        if not event:
            return jsonify({"error": "Event not found"}), 404
            
        event_data = event.serialize()
        
        # Add status field and time remaining
        now = datetime.now(timezone.utc)
        if event.start_time > now:
            event_data['status'] = 'upcoming'
        elif event.end_time < now:
            event_data['status'] = 'completed'
        else:
            event_data['status'] = 'active'
            time_delta = event.end_time - now
            event_data['time_remaining_seconds'] = max(0, time_delta.total_seconds())
            
        return json.dumps(event_data, cls=ModelEncoder), 200
    except Exception as e:
        logging.error(f"Error getting event: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/events/<event_id>/teams", methods=['GET'])
def get_event_teams(event_id):
    """Get teams for a specific event"""
    try:
        event = Events.query.filter_by(id=event_id).first()
        if not event:
            return jsonify({"error": "Event not found"}), 404
        
        teams = EventTeams.query.filter_by(event_id=event_id).all()
        if not teams:
            return jsonify({"error": "No teams found for this event"}), 404
        
        return json.dumps([team.serialize() for team in teams], cls=ModelEncoder), 200
    except Exception as e:
        logging.error(f"Error getting event teams: {str(e)}")
        return jsonify({"error": str(e)}), 500
