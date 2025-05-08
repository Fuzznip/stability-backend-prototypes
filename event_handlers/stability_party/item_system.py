"""
Item system for Stability Party 3

This module handles all item-related functionality including:
- Item creation and registration
- Item activation and effects
- Random shop item generation
- Team inventory management
"""

from app import db
import uuid
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Union

from models.models import Events, EventTeams
from event_handlers.stability_party.stability_party_handler import SaveData, save_team_data
from event_handlers.stability_party.item_registry import (
    ITEM_REGISTRY, get_item, get_all_items, get_items_by_type, get_items_by_rarity
)

# Dictionary to store item effect handlers
# Each handler is a function that takes (event_id, team_id, save_data, item_data) and returns a result dict
ITEM_HANDLERS = {}

# Item rarity weights for random selection
RARITY_WEIGHTS = {
    "common": 50,
    "uncommon": 30, 
    "rare": 15,
    "epic": 4,
    "legendary": 1
}

def register_item_handler(item_type: str):
    """
    Decorator to register an item handler function.
    
    Usage:
        @register_item_handler("health_potion")
        def health_potion_handler(event_id, team_id, save, item_data):
            # Implementation
            return {"message": "Health restored!"}
    """
    def decorator(func: Callable):
        ITEM_HANDLERS[item_type] = func
        logging.info(f"Registered item handler for type: {item_type}")
        return func
    return decorator

def get_item_by_id(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Get an item by ID - tries the code registry first, falls back to database
    
    Args:
        item_id: The item identifier
        
    Returns:
        Item data or None if not found
    """
    try:
        # First try to get from registry (items defined in code)
        registry_item = get_item(item_id)
        if registry_item:
            return registry_item.to_dict()
            
        return None
    except Exception as e:
        logging.error(f"Error fetching item {item_id}: {str(e)}")
        return None

def get_team_items(team_id: str, event_id: str) -> List[Dict[str, Any]]:
    """Get all items owned by a team"""
    try:
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            logging.error(f"Team not found: {team_id}")
            return []
        
        save = SaveData.from_dict(team.data)
        item_details = []
        
        for item_entry in save.itemList:
            item_id = item_entry.get("id")
            item = get_item_by_id(item_id)
            if item:
                # Merge the base item data with any instance-specific data
                item_data = {
                    "id": item_id,
                    "name": item["name"],
                    "description": item["description"],
                    "image": item["image"],
                    "item_type": item["item_type"],
                    "rarity": item["rarity"],
                    "uses_remaining": item_entry.get("uses_remaining", item["uses"]),
                    "purchased_at": item_entry.get("purchased_at"),
                    "activation_type": item["activation_type"],
                    "can_be_activated": item["activation_type"] == "active" and item_entry.get("uses_remaining", item["uses"]) > 0
                }
                item_details.append(item_data)
        
        return item_details
    except Exception as e:
        logging.error(f"Error getting team items: {str(e)}")
        return []

def generate_shop_inventory(event_id: str, shop_tier: int = 1, item_count: int = 5) -> List[Dict[str, Any]]:
    """
    Generate a random selection of items for a shop based on shop tier.
    
    Parameters:
    - event_id: The event these items belong to
    - shop_tier: The tier/level of the shop (higher tiers have better items)
    - item_count: Number of items to generate
    
    Returns:
    - List of item dictionaries for the shop
    """
    try:
        # Get all available items from registry
        all_items = [item.to_dict() for item in get_all_items()]
        
        if not all_items:
            logging.warning(f"No items found for shop generation")
            return []
        
        # Prepare empty result list
        shop_items = []
        
        # Adjust weights based on shop tier
        tier_weights = RARITY_WEIGHTS.copy()
        if shop_tier > 1:
            # Decrease common chance, increase rare+ chances for higher tier shops
            tier_weights["common"] = max(10, 50 - (shop_tier * 10))
            tier_weights["uncommon"] = 30 + (shop_tier * 2)
            tier_weights["rare"] = 15 + (shop_tier * 5)
            tier_weights["epic"] = 4 + (shop_tier * 2)
            tier_weights["legendary"] = 1 + shop_tier
            
        logging.debug(f"Shop tier {shop_tier} rarity weights: {tier_weights}")
        
        # Group items by rarity
        items_by_rarity = {}
        for item in all_items:
            rarity = item["rarity"].lower()
            if rarity not in items_by_rarity:
                items_by_rarity[rarity] = []
            items_by_rarity[rarity].append(item)
        
        # Select random items based on rarity weights
        for _ in range(item_count):
            # Determine rarity based on weights
            rarities = list(tier_weights.keys())
            weights = list(tier_weights.values())
            selected_rarity = random.choices(rarities, weights=weights, k=1)[0]
            
            # If no items of this rarity, try another
            if selected_rarity not in items_by_rarity or not items_by_rarity[selected_rarity]:
                # Try all rarities from highest to lowest
                for rarity in sorted(items_by_rarity.keys(), 
                                     key=lambda r: ["common", "uncommon", "rare", "epic", "legendary"].index(r), 
                                     reverse=True):
                    if items_by_rarity[rarity]:
                        selected_rarity = rarity
                        break
                else:
                    # Skip if still no items found
                    continue
            
            # Select random item of chosen rarity
            item = random.choice(items_by_rarity[selected_rarity])
            
            # Calculate price with some randomness
            base_price = item["base_price"]
            price_variance = random.uniform(0.8, 1.2)  # 20% variance
            final_price = int(base_price * price_variance)
            
            # Add item to shop inventory
            shop_items.append({
                "id": str(item["id"]),
                "name": item["name"],
                "description": item["description"],
                "image": item["image"],
                "item_type": item["item_type"],
                "rarity": item["rarity"],
                "price": final_price
            })
            
        return shop_items
    except Exception as e:
        logging.error(f"Error generating shop inventory: {str(e)}")
        return []

def add_item_to_inventory(event_id: str, team_id: str, item_id: str) -> bool:
    """
    Add an item to a team's inventory
    
    Parameters:
    - event_id: Event ID
    - team_id: Team ID
    - item_id: Item ID to add
    
    Returns:
    - Success flag
    """
    try:
        # Get team and save data
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            logging.error(f"Team not found: {team_id}")
            return False
        
        save = SaveData.from_dict(team.data)
        
        # Get item details from registry or database
        item = get_item_by_id(item_id)
        if not item:
            logging.error(f"Item not found: {item_id}")
            return False
            
        # Create inventory item entry
        item_entry = {
            "id": item_id,
            "name": item["name"],
            "description": item["description"],
            "item_type": item["item_type"],
            "rarity": item["rarity"],
            "uses_remaining": item["uses"],
            "purchased_at": datetime.now().isoformat(),
            "activation_handler": item["activation_handler"]
        }
        
        # Add to inventory
        save.itemList.append(item_entry)
        logging.info(f"Added item {item['name']} (ID: {item_id}) to team {team_id} inventory")
        
        # Save changes
        save_team_data(team, save)
        return True
    
    except Exception as e:
        logging.error(f"Error adding item to inventory: {str(e)}")
        return False

def use_item(event_id: str, team_id: str, item_index: int) -> Dict[str, Any]:
    """
    Use/activate an item from a team's inventory
    
    Parameters:
    - event_id: Event ID
    - team_id: Team ID
    - item_index: Index of the item in the team's inventory
    
    Returns:
    - Result dictionary with success flag and messages
    """
    try:
        # Get team and save data
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            logging.error(f"Team not found: {team_id}")
            return {"success": False, "message": "Team not found"}
        
        save = SaveData.from_dict(team.data)
        
        # Check if item index is valid
        if item_index < 0 or item_index >= len(save.itemList):
            logging.error(f"Invalid item index: {item_index}")
            return {"success": False, "message": "Item not found in inventory"}
        
        # Get item from inventory
        item_entry = save.itemList[item_index]
        item_id = item_entry.get("id")
        
        # Get full item details from registry or database
        item = get_item_by_id(item_id)
        if not item:
            logging.error(f"Item not found in registry or database: {item_id}")
            return {"success": False, "message": "Item not found in registry"}
        
        # Check if item can be used (has uses remaining)
        uses_remaining = item_entry.get("uses_remaining", item["uses"])
        if uses_remaining <= 0:
            logging.warning(f"Item {item['name']} has no uses remaining")
            return {"success": False, "message": "This item has no uses remaining"}
        
        # Check if item has an activation handler
        handler_name = item["activation_handler"]
        if not handler_name or handler_name not in ITEM_HANDLERS:
            logging.error(f"No handler found for item type: {handler_name}")
            return {"success": False, "message": "This item cannot be activated"}
        
        # Call the item handler function
        handler = ITEM_HANDLERS[handler_name]
        result = handler(event_id, team_id, save, item_entry)
        
        # Update uses remaining
        save.itemList[item_index]["uses_remaining"] = uses_remaining - 1
        
        # Remove item if no uses remaining
        if save.itemList[item_index]["uses_remaining"] <= 0 and item["uses"] > 0:  # Only remove consumables, not unlimited use items
            logging.info(f"Item {item['name']} used up, removing from inventory")
            if "remove_on_use" not in result or result["remove_on_use"]:
                save.itemList.pop(item_index)
            
        # Save changes
        save_team_data(team, save)
        
        # Return result
        return {
            "success": True, 
            "message": result.get("message", f"{item['name']} used successfully!"),
            "effect": result.get("effect", {}),
            "item_name": item["name"]
        }
        
    except Exception as e:
        logging.error(f"Error using item: {str(e)}")
        return {"success": False, "message": f"Error using item: {str(e)}"}

#
# Sample Item Handlers
#

@register_item_handler("dice_modifier")
def dice_modifier_handler(event_id, team_id, save, item_data):
    """Handler for dice modifier items"""
    data = item_data.get("data", {})
    modifier_value = data.get("modifier_value", 1)
    duration = data.get("duration", 1)
    
    # Apply modifier
    save.modifier += modifier_value
    
    return {
        "message": f"Dice roll modifier increased by {modifier_value} for your next {duration} rolls!",
        "effect": {
            "modifier_value": modifier_value,
            "duration": duration
        }
    }

@register_item_handler("bonus_coins")
def bonus_coins_handler(event_id, team_id, save, item_data):
    """Handler for bonus coin items"""
    data = item_data.get("data", {})
    coin_amount = data.get("coin_amount", 10)
    
    # Add coins
    save.coins += coin_amount
    
    return {
        "message": f"You gained {coin_amount} coins!",
        "effect": {
            "coin_amount": coin_amount
        }
    }

@register_item_handler("bonus_dice")
def bonus_dice_handler(event_id, team_id, save, item_data):
    """Handler for bonus dice items"""
    data = item_data.get("data", {})
    dice_sides = data.get("dice_sides", 6)
    duration = data.get("duration", 1)
    
    # Add a die to the team's dice array
    save.dice.append(dice_sides)
    
    return {
        "message": f"Added a d{dice_sides} to your next roll!",
        "effect": {
            "dice_sides": dice_sides,
            "duration": duration
        }
    }

@register_item_handler("double_roll")
def double_roll_handler(event_id, team_id, save, item_data):
    """Handler for double roll items"""
    # Set a flag for the roll handler to roll twice
    save.data = save.data or {}
    save.data["double_roll"] = True
    
    return {
        "message": "Your next roll will be rolled twice, taking the better result!",
        "effect": {
            "double_roll": True
        }
    }

@register_item_handler("teleport")
def teleport_handler(event_id, team_id, save, item_data):
    """Handler for teleport items"""
    # Logic for teleport would be implemented here
    # For now, just a placeholder
    return {
        "message": "You teleported to a random location on the board!",
        "effect": {
            "teleported": True
        }
    }

@register_item_handler("star_finder")
def star_finder_handler(event_id, team_id, save, item_data):
    """Handler for star finder items"""
    return {
        "message": "The nearest star location has been revealed on your map!",
        "effect": {
            "star_revealed": True
        }
    }

@register_item_handler("star_discount")
def star_discount_handler(event_id, team_id, save, item_data):
    """Handler for star discount items"""
    data = item_data.get("data", {})
    discount = data.get("discount_percent", 50)
    
    # Set discount in team data
    save.data = save.data or {}
    save.data["star_discount"] = discount
    
    return {
        "message": f"Your next star purchase will be {discount}% off!",
        "effect": {
            "star_discount": discount
        }
    }

@register_item_handler("buff")
def buff_handler(event_id, team_id, save, item_data):
    """Handler for buff items"""
    data = item_data.get("data", {})
    buff_type = data.get("buff_type", "strength")
    buff_duration = data.get("buff_duration", 3)
    
    # Add buff to team
    if buff_type not in save.buffs:
        save.buffs.append(buff_type)
    
    # Store duration in team data
    save.data = save.data or {}
    if "buff_durations" not in save.data:
        save.data["buff_durations"] = {}
    save.data["buff_durations"][buff_type] = buff_duration
    
    return {
        "message": f"Applied {buff_type} buff for {buff_duration} turns!",
        "effect": {
            "buff_type": buff_type,
            "buff_duration": buff_duration
        }
    }

@register_item_handler("equipment_passive")
def equipment_passive_handler(event_id, team_id, save, item_data):
    """Handler for equipment passive effects"""
    data = item_data.get("data", {})
    slot = data.get("slot")
    
    if not slot:
        return {"message": "Equipment slot not specified", "success": False}
    
    # Equip the item in the proper slot
    if not save.equipment:
        # Initialize equipment if needed
        from event_handlers.stability_party.stability_party_handler import Equipment
        save.equipment = Equipment.from_dict({})
    
    # Get current item in that slot
    old_item = None
    if slot == "helmet":
        old_item = save.equipment.helmet
        save.equipment.helmet = item_data["id"]
    elif slot == "armor":
        old_item = save.equipment.armor
        save.equipment.armor = item_data["id"]
    elif slot == "weapon":
        old_item = save.equipment.weapon
        save.equipment.weapon = item_data["id"]
    elif slot == "jewelry":
        old_item = save.equipment.jewelry
        save.equipment.jewelry = item_data["id"]
    elif slot == "cape":
        old_item = save.equipment.cape
        save.equipment.cape = item_data["id"]
    
    # If replacing an item, add old item back to inventory
    if old_item:
        # Find old item in registry/DB and add back to inventory
        old_item_data = get_item_by_id(old_item)
        if old_item_data:
            old_item_entry = {
                "id": old_item,
                "name": old_item_data["name"],
                "description": old_item_data["description"],
                "item_type": old_item_data["item_type"],
                "rarity": old_item_data["rarity"],
                "uses_remaining": old_item_data["uses"],
                "activation_handler": old_item_data["activation_handler"]
            }
            save.itemList.append(old_item_entry)
    
    # Apply stat bonuses from equipment
    stat_bonuses = data.get("stat_bonus", {})
    
    # Store equipment bonuses in save data
    save.data = save.data or {}
    if "equipment_bonuses" not in save.data:
        save.data["equipment_bonuses"] = {}
    
    # Add this item's bonuses
    for stat, value in stat_bonuses.items():
        if stat not in save.data["equipment_bonuses"]:
            save.data["equipment_bonuses"][stat] = 0
        save.data["equipment_bonuses"][stat] += value
    
    # For specific stats like movement, apply directly
    if "movement" in stat_bonuses:
        save.modifier += stat_bonuses["movement"]
    
    return {
        "message": f"Equipped {item_data['name']} in {slot} slot!",
        "effect": {
            "equipped": True,
            "slot": slot,
            "bonuses": stat_bonuses
        },
        "remove_on_use": True  # Remove from inventory since it's now equipped
    }

@register_item_handler("magic_lamp")
def magic_lamp_handler(event_id, team_id, save, item_data):
    """Handler for magic lamp item (teleport to any tile)"""
    # In a real implementation, this would show UI for choosing a destination
    # For now, just a placeholder
    return {
        "message": "You can now choose any tile on the board to teleport to!",
        "effect": {
            "choose_teleport": True
        }
    }

@register_item_handler("star_stealer")
def star_stealer_handler(event_id, team_id, save, item_data):
    """Handler for star stealer item (steal star from another team)"""
    # In a real implementation, this would show UI for choosing a team
    # For now, just a placeholder
    return {
        "message": "You can now choose a team to steal a star from!",
        "effect": {
            "choose_team": True
        }
    }