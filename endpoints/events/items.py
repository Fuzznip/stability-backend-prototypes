"""
Item endpoints for the Stability Party 3 game.

This module provides API endpoints for:
- Getting team items
- Using/activating items
- Shop item management
"""

from app import app
from flask import Blueprint, jsonify, request
import logging
import uuid

from app import db
from models.models import Events, EventTeams
from event_handlers.stability_party.item_system import get_team_items, use_item, complete_item_activation

@app.route('/events/<event_id>/teams/<team_id>/items/inventory', methods=['GET'])
def get_team_inventory(event_id, team_id):
    """
    Get all items owned by a team.
    
    Path Parameters:
    - event_id: UUID of the event
    - team_id: UUID of the team
    
    Returns:
    - JSON array of team's items with details
    """
    try:
        # Validate UUIDs
        try:
            event_uuid = uuid.UUID(event_id)
            team_uuid = uuid.UUID(team_id)
        except ValueError:
            return jsonify({"error": "Invalid UUID format"}), 400
            
        # Check if event exists
        event = Events.query.filter_by(id=event_uuid).first()
        if not event:
            return jsonify({"error": "Event not found"}), 404
            
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_uuid, event_id=event_uuid).first()
        if not team:
            return jsonify({"error": "Team not found or does not belong to this event"}), 404
            
        # Get items
        items = get_team_items(team_id, event_id)
        
        return jsonify({
            "team_name": team.name,
            "item_count": len(items),
            "items": items
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting team inventory: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/events/<event_id>/teams/<team_id>/items/use', methods=['POST'])
def use_team_item(event_id, team_id):
    """
    Use/activate an item from the team's inventory.
    
    Path Parameters:
    - event_id: UUID of the event
    - team_id: UUID of the team
    
    Request Body:
    - item_index: Index of the item in the team's inventory
    
    Returns:
    - JSON with result of the item activation
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or "item_index" not in data:
            return jsonify({"error": "Missing required field: item_index"}), 400
            
        item_index = data.get("item_index")
        
        # Validate UUIDs
        try:
            event_uuid = uuid.UUID(event_id)
            team_uuid = uuid.UUID(team_id)
        except ValueError:
            return jsonify({"error": "Invalid UUID format"}), 400
            
        # Check if event exists
        event = Events.query.filter_by(id=event_uuid).first()
        if not event:
            return jsonify({"error": "Event not found"}), 404
            
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_uuid, event_id=event_uuid).first()
        if not team:
            return jsonify({"error": "Team not found or does not belong to this event"}), 404
            
        # Use the item
        result = use_item(event_id, team_id, item_index)
        
        if not result.get("success", False):
            return jsonify(result), 400
            
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Error using team item: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e), "success": False}), 500
    
@app.route('/events/<event_id>/teams/<team_id>/items/selection', methods=['POST'])
def complete_item_selection(event_id, team_id):
    """
    Complete a two-stage item activation by submitting the selected option
    
    Path Parameters:
    - event_id: UUID of the event
    - team_id: UUID of the team
    
    Request Body:
    - selection: The selected option (could be a string, number, object, etc.)
    
    Returns:
    - JSON with result of the item activation
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or "selection" not in data:
            return jsonify({"error": "Missing required field: selection"}), 400
            
        # Validate UUIDs
        try:
            event_uuid = uuid.UUID(event_id)
            team_uuid = uuid.UUID(team_id)
        except ValueError:
            return jsonify({"error": "Invalid UUID format"}), 400
            
        # Check if event exists
        event = Events.query.filter_by(id=event_uuid).first()
        if not event:
            return jsonify({"error": "Event not found"}), 404
            
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_uuid, event_id=event_uuid).first()
        if not team:
            return jsonify({"error": "Team not found or does not belong to this event"}), 404
            
        # Complete the item activation with the selection
        result = complete_item_activation(event_id, team_id, data)
        
        if not result.get("success", False):
            return jsonify(result), 400
            
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Error processing item selection: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e), "success": False}), 500
