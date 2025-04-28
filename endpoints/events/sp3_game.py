from app import app, db
from flask import request, jsonify
from models.models import Events, EventTeams, EventTeamMemberMappings
from models.stability_party_3 import SP3Regions, SP3EventTiles
from event_handlers.stability_party.stability_party_handler import SaveData, save_team_data
from sqlalchemy.orm.attributes import flag_modified
import uuid
import logging
import os
from datetime import datetime, timezone
from helper.helpers import ModelEncoder


@app.route("/events/<event_id>/teams/<team_id>/stats", methods=['GET'])
def get_team_stats(event_id, team_id):
    """Get the current stats for a team"""
    try:
        # Check if event exists and is a SP3 event
        event = Events.query.filter_by(id=event_id, type="STABILITY_PARTY").first()
        if not event:
            return jsonify({"error": "Event not found or not a Stability Party event"}), 404
        
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            return jsonify({"error": "Team not found or does not belong to this event"}), 404
        
        # Get team members
        members = EventTeamMemberMappings.query.filter_by(event_id=event_id, team_id=team_id).all()
        member_names = [member.username for member in members]
        
        # Get team stats
        save = SaveData.from_dict(team.data)
        
        # Find the current tile information
        current_tile = SP3EventTiles.query.filter_by(
            event_id=event_id, 
            tile_number=save.currentTile
        ).first()
        
        tile_info = None
        if current_tile:
            tile_info = {
                "id": str(current_tile.id),
                "type": current_tile.type,
                "name": current_tile.name,
                "description": current_tile.description
            }
        
        # Find the current island/region information
        current_region = SP3Regions.query.filter_by(
            event_id=event_id,
            id=save.islandId
        ).first()
        
        region_info = None
        if current_region:
            region_info = {
                "id": str(current_region.id),
                "name": current_region.name,
                "description": current_region.description
            }
        
        stats = {
            "team_name": team.name,
            "captain": str(team.captain),
            "members": member_names,
            "stars": save.stars,
            "coins": save.coins,
            "current_location": {
                "tile": save.currentTile,
                "tile_info": tile_info,
                "region": region_info
            },
            "tile_completed": save.isTileCompleted,
            "equipment": save.equipment,
            "buffs": save.buffs,
            "debuffs": save.debuffs,
            "items": save.itemList,
            "is_rolling": save.isRolling,
            "current_challenge": save.currentChallenge
        }
        
        return jsonify(stats), 200
    except Exception as e:
        logging.error(f"Error getting team stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/events/<event_id>/teams/<team_id>/tile-progress", methods=['GET'])
def get_team_tile_progress(event_id, team_id):
    """Get the current tile progress for a team"""
    try:
        # Check if event exists and is a SP3 event
        event = Events.query.filter_by(id=event_id, type="STABILITY_PARTY").first()
        if not event:
            return jsonify({"error": "Event not found or not a Stability Party event"}), 404
        
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            return jsonify({"error": "Team not found or does not belong to this event"}), 404
        
        # Get team data
        save = SaveData.from_dict(team.data)
        
        # Get current tile information
        current_tile = SP3EventTiles.query.filter_by(
            event_id=event_id, 
            tile_number=save.currentTile
        ).first()
        
        if not current_tile:
            return jsonify({"error": "Current tile information not found"}), 404
        
        # Get progress for the current tile
        current_tile_id = str(save.currentTile)
        tile_progress = save.tileProgress.get(current_tile_id, {})
        
        response = {
            "tile_number": save.currentTile,
            "tile_type": current_tile.type,
            "tile_name": current_tile.name,
            "tile_description": current_tile.description,
            "is_completed": save.isTileCompleted,
            "progress": tile_progress,
            "can_roll": save.isTileCompleted and not save.isRolling
        }
        
        return jsonify(response), 200
    except Exception as e:
        logging.error(f"Error getting tile progress: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/events/<event_id>/progress", methods=['GET'])
def get_event_progress(event_id):
    """Get the overall progress of the event including team standings"""
    try:
        # Check if event exists and is a SP3 event
        event = Events.query.filter_by(id=event_id, type="STABILITY_PARTY").first()
        if not event:
            return jsonify({"error": "Event not found or not a Stability Party event"}), 404
        
        # Calculate time until event end
        now = datetime.now(timezone.utc)
        time_remaining = None
        if event.end_time:
            end_time = event.end_time.replace(tzinfo=timezone.utc)
            time_delta = end_time - now
            time_remaining = max(0, time_delta.total_seconds())
        
        # Get all teams for this event
        teams = EventTeams.query.filter_by(event_id=event_id).all()
        
        # Prepare team standings
        standings = []
        for team in teams:
            save = SaveData.from_dict(team.data)
            
            # Get current tile information
            current_tile = SP3EventTiles.query.filter_by(
                event_id=event_id, 
                tile_number=save.currentTile
            ).first()
            
            # Get current region information  
            current_region = SP3Regions.query.filter_by(
                event_id=event_id,
                id=save.islandId
            ).first()
            
            region_name = current_region.name if current_region else "Unknown"
            tile_type = current_tile.type if current_tile else "Unknown"
            
            standings.append({
                "team_id": str(team.id),
                "team_name": team.name,
                "stars": save.stars,
                "coins": save.coins,
                "current_tile": save.currentTile,
                "current_region": region_name,
                "current_tile_type": tile_type,
                "tile_completed": save.isTileCompleted
            })
        
        # Sort by stars (descending) and then by coins (descending)
        standings.sort(key=lambda x: (x["stars"], x["coins"]), reverse=True)
        
        # Add ranking to each team
        for i, team in enumerate(standings):
            team["rank"] = i + 1
        
        # Get event regions/islands
        regions = SP3Regions.query.filter_by(event_id=event_id).all()
        region_info = []
        for region in regions:
            region_info.append({
                "id": str(region.id),
                "name": region.name,
                "description": region.description
            })
        
        response = {
            "event_id": event_id,
            "event_name": event.name,
            "event_description": event.description,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "time_remaining_seconds": time_remaining,
            "regions": region_info,
            "team_standings": standings,
            "total_teams": len(teams)
        }
        
        return jsonify(response), 200
    except Exception as e:
        logging.error(f"Error getting event progress: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/events/<event_id>/teams/<team_id>/roll", methods=['POST'])
def roll_dice(event_id, team_id):
    """Roll dice to move forward on the board"""
    try:
        # Check if event exists and is a SP3 event
        event = Events.query.filter_by(id=event_id, type="STABILITY_PARTY").first()
        if not event:
            return jsonify({"error": "Event not found or not a Stability Party event"}), 404
        
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            return jsonify({"error": "Team not found or does not belong to this event"}), 404
        
        # Load team data
        save = SaveData.from_dict(team.data)
        
        # Check if the current tile is completed
        if not save.isTileCompleted:
            return jsonify({"error": "Current tile must be completed before rolling"}), 400
        
        # Check if the team is already rolling
        if save.isRolling:
            return jsonify({"error": "Team is already in the process of rolling"}), 400
        
        # Get dice roll data from request (optional)
        data = request.get_json() or {}
        custom_roll = data.get("custom_roll", None)
        modifier = data.get("modifier", 0)
        
        # Generate random dice roll if not provided
        import random
        dice_count = data.get("dice_count", 2)  # Default to 2 dice
        dice_results = []
        
        if custom_roll is not None:
            dice_results = [int(custom_roll)]
        else:
            for _ in range(dice_count):
                dice_results.append(random.randint(1, 6))
        
        # Calculate total movement
        roll_total = sum(dice_results) + int(modifier)
        
        # Store previous tile and update current tile
        save.previousTile = save.currentTile
        save.currentTile = save.currentTile + roll_total
        
        # Update team state
        save.dice = dice_results
        save.modifier = modifier
        save.isRolling = True
        save.isTileCompleted = False  # New tile needs to be completed
        
        # Get the new tile information
        new_tile = SP3EventTiles.query.filter_by(
            event_id=event_id, 
            tile_number=save.currentTile
        ).first()
        
        new_tile_info = None
        if new_tile:
            new_tile_info = {
                "id": str(new_tile.id),
                "type": new_tile.type,
                "name": new_tile.name,
                "description": new_tile.description
            }
            
            # Check if we need to set island ID based on the tile
            if new_tile.island_id and new_tile.island_id != save.islandId:
                save.islandId = new_tile.island_id
        
        # Save the updated team data
        save_team_data(team, save)
        
        response = {
            "message": "Dice rolled successfully",
            "dice_results": dice_results,
            "modifier": modifier,
            "total_movement": roll_total,
            "previous_tile": save.previousTile,
            "new_tile": save.currentTile,
            "new_tile_info": new_tile_info
        }
        
        # Add special actions available based on the new tile type
        if new_tile:
            if new_tile.type == "SHOP":
                response["available_action"] = "shop"
            elif new_tile.type == "STAR_SPOT":
                response["available_action"] = "buy_star"
            elif new_tile.type == "DOCK":
                response["available_action"] = "charter_ship"
        
        return jsonify(response), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error rolling dice: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/events/<event_id>/teams/<team_id>/shop/item", methods=['POST'])
def buy_item(event_id, team_id):
    """Buy an item from the item shop"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if "item_id" not in data:
            return jsonify({"error": "Missing required field: item_id"}), 400
        
        # Check if event exists and is a SP3 event
        event = Events.query.filter_by(id=event_id, type="STABILITY_PARTY").first()
        if not event:
            return jsonify({"error": "Event not found or not a Stability Party event"}), 404
        
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            return jsonify({"error": "Team not found or does not belong to this event"}), 404
        
        # Load team data
        save = SaveData.from_dict(team.data)
        
        # Check if the team is rolling (must have just landed on this tile)
        if not save.isRolling:
            return jsonify({"error": "Team must be in the middle of a roll to buy an item"}), 400
        
        # Check if the team is on a shop tile
        current_tile = SP3EventTiles.query.filter_by(
            event_id=event_id, 
            tile_number=save.currentTile
        ).first()
        
        if not current_tile or current_tile.type != "SHOP":
            return jsonify({"error": "Team must be on a shop tile to buy items"}), 400
        
        # Get item price from request
        item_id = data["item_id"]
        item_price = data.get("price", 10)  # Default price if not provided
        item_name = data.get("name", f"Item {item_id}")
        
        # Check if team has enough coins
        if save.coins < item_price:
            return jsonify({"error": f"Not enough coins. Required: {item_price}, Available: {save.coins}"}), 400
        
        # Add item to inventory and deduct coins
        new_item = {
            "id": item_id,
            "name": item_name,
            "description": data.get("description", ""),
            "purchased_at": datetime.now().isoformat()
        }
        save.itemList.append(new_item)
        save.coins -= item_price
        
        # Mark tile as completed if buying an item completes it
        save.isTileCompleted = True
        save.isRolling = False
        
        # Save the updated team data
        save_team_data(team, save)
        
        return jsonify({
            "message": "Item purchased successfully",
            "item": new_item,
            "remaining_coins": save.coins,
            "tile_completed": save.isTileCompleted
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error buying item: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/events/<event_id>/teams/<team_id>/shop/star", methods=['POST'])
def buy_star(event_id, team_id):
    """Buy a star from a star spot"""
    try:
        data = request.get_json() or {}
        
        # Get star price from request (default to 20 coins)
        star_price = data.get("price", 20)
        
        # Check if event exists and is a SP3 event
        event = Events.query.filter_by(id=event_id, type="STABILITY_PARTY").first()
        if not event:
            return jsonify({"error": "Event not found or not a Stability Party event"}), 404
        
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            return jsonify({"error": "Team not found or does not belong to this event"}), 404
        
        # Load team data
        save = SaveData.from_dict(team.data)
        
        # Check if the team is rolling (must have just landed on this tile)
        if not save.isRolling:
            return jsonify({"error": "Team must be in the middle of a roll to buy a star"}), 400
        
        # Check if the team is on a star spot tile
        current_tile = SP3EventTiles.query.filter_by(
            event_id=event_id, 
            tile_number=save.currentTile
        ).first()
        
        if not current_tile or current_tile.type != "STAR_SPOT":
            return jsonify({"error": "Team must be on a star spot tile to buy stars"}), 400
        
        # Check if team has enough coins
        if save.coins < star_price:
            return jsonify({"error": f"Not enough coins. Required: {star_price}, Available: {save.coins}"}), 400
        
        # Add star and deduct coins
        save.stars += 1
        save.coins -= star_price
        
        # Mark tile as completed
        save.isTileCompleted = True
        save.isRolling = False
        
        # Save the updated team data
        save_team_data(team, save)
        
        return jsonify({
            "message": "Star purchased successfully",
            "stars": save.stars,
            "remaining_coins": save.coins,
            "tile_completed": save.isTileCompleted
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error buying star: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/events/<event_id>/teams/<team_id>/dock/charter", methods=['POST'])
def charter_ship(event_id, team_id):
    """Charter a ship from a dock spot to travel to another island"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if "destination_island_id" not in data:
            return jsonify({"error": "Missing required field: destination_island_id"}), 400
        
        # Check if event exists and is a SP3 event
        event = Events.query.filter_by(id=event_id, type="STABILITY_PARTY").first()
        if not event:
            return jsonify({"error": "Event not found or not a Stability Party event"}), 404
        
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            return jsonify({"error": "Team not found or does not belong to this event"}), 404
        
        # Load team data
        save = SaveData.from_dict(team.data)
        
        # Check if the team is rolling (must have just landed on this tile)
        if not save.isRolling:
            return jsonify({"error": "Team must be in the middle of a roll to charter a ship"}), 400
        
        # Check if the team is on a dock tile
        current_tile = SP3EventTiles.query.filter_by(
            event_id=event_id, 
            tile_number=save.currentTile
        ).first()
        
        if not current_tile or current_tile.type != "DOCK":
            return jsonify({"error": "Team must be on a dock tile to charter a ship"}), 400
        
        # Get destination details
        destination_island_id = data["destination_island_id"]
        
        # Check if destination island exists
        destination_island = SP3Regions.query.filter_by(
            event_id=event_id, 
            id=destination_island_id
        ).first()
        
        if not destination_island:
            return jsonify({"error": "Destination island not found"}), 404
        
        # Get charter price from request (default to 10 coins)
        charter_price = data.get("price", 10)
        
        # Check if team has enough coins
        if save.coins < charter_price:
            return jsonify({"error": f"Not enough coins. Required: {charter_price}, Available: {save.coins}"}), 400
        
        # Find the starting tile of the destination island
        destination_tile = SP3EventTiles.query.filter_by(
            event_id=event_id, 
            island_id=destination_island_id,
            is_island_start=True
        ).first()
        
        if not destination_tile:
            return jsonify({"error": "Destination island starting tile not found"}), 404
        
        # Update team location and deduct coins
        save.previousTile = save.currentTile
        save.currentTile = destination_tile.tile_number
        save.islandId = destination_island_id
        save.coins -= charter_price
        
        # Reset rolling state and mark new tile as not completed
        save.isRolling = False
        save.isTileCompleted = False
        
        # Save the updated team data
        save_team_data(team, save)
        
        return jsonify({
            "message": "Ship chartered successfully",
            "previous_tile": save.previousTile,
            "destination_island": {
                "id": str(destination_island_id),
                "name": destination_island.name,
                "tile": save.currentTile
            },
            "remaining_coins": save.coins
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error chartering ship: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/events/<event_id>/teams/<team_id>/available-actions", methods=['GET'])
def get_available_actions(event_id, team_id):
    """Get available actions for a team based on their current position"""
    try:
        # Check if event exists and is a SP3 event
        event = Events.query.filter_by(id=event_id, type="STABILITY_PARTY").first()
        if not event:
            return jsonify({"error": "Event not found or not a Stability Party event"}), 404
        
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            return jsonify({"error": "Team not found or does not belong to this event"}), 404
        
        # Load team data
        save = SaveData.from_dict(team.data)
        
        # Get the current tile information
        current_tile = SP3EventTiles.query.filter_by(
            event_id=event_id, 
            tile_number=save.currentTile
        ).first()
        
        if not current_tile:
            return jsonify({"error": "Current tile information not found"}), 404
        
        # Determine available actions
        available_actions = []
        
        # If the tile is completed, they can roll
        if save.isTileCompleted and not save.isRolling:
            available_actions.append({
                "action": "roll",
                "description": "Roll dice to move forward"
            })
        
        # If they are in the middle of rolling and on a special tile
        if save.isRolling:
            if current_tile.type == "SHOP":
                available_actions.append({
                    "action": "buy_item",
                    "description": "Buy an item from the shop"
                })
            elif current_tile.type == "STAR_SPOT":
                available_actions.append({
                    "action": "buy_star",
                    "description": "Buy a star" 
                })
            elif current_tile.type == "DOCK":
                # Get available destinations
                regions = SP3Regions.query.filter_by(event_id=event_id).all()
                destinations = []
                for region in regions:
                    if region.id != save.islandId:  # Don't include current island
                        destinations.append({
                            "id": str(region.id),
                            "name": region.name
                        })
                
                if destinations:
                    available_actions.append({
                        "action": "charter_ship",
                        "description": "Charter a ship to another island",
                        "destinations": destinations
                    })
        
        # Return the available actions
        response = {
            "current_tile": {
                "number": save.currentTile,
                "type": current_tile.type,
                "name": current_tile.name,
                "description": current_tile.description
            },
            "is_completed": save.isTileCompleted,
            "is_rolling": save.isRolling,
            "available_actions": available_actions
        }
        
        return jsonify(response), 200
    except Exception as e:
        logging.error(f"Error getting available actions: {str(e)}")
        return jsonify({"error": str(e)}), 500