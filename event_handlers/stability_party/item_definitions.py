"""
Item definitions for Stability Party 3

This module contains both the item definitions and their handlers together.
Each item is registered with its corresponding handler function,
keeping the definition and functionality together for better maintenance.
"""

import uuid
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple

# Dictionary to store all registered items
ITEM_REGISTRY = {}

# Dictionary to store item effect handlers
# Each handler is a function that takes (event_id, team_id, save_data, item_data) and returns a result dict
ITEM_HANDLERS = {}

class ItemDefinition:
    """Class representing an item definition"""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        item_type: str,
        rarity: str,
        base_price: int,
        image: str = None,
        uses: int = 1,
        activation_type: str = "active",
        activation_handler: str = None,
        requires_selection: bool = False,  # New flag for items requiring selection
        selection_handler: str = None,    # Handler for processing selections
        data: Dict[str, Any] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.item_type = item_type
        self.rarity = rarity
        self.base_price = base_price
        self.image = image
        self.uses = uses
        self.activation_type = activation_type
        self.activation_handler = activation_handler
        self.requires_selection = requires_selection
        self.selection_handler = selection_handler
        self.data = data or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the item definition to a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type,
            "rarity": self.rarity,
            "base_price": self.base_price,
            "image": self.image,
            "uses": self.uses,
            "activation_type": self.activation_type,
            "activation_handler": self.activation_handler,
            "requires_selection": self.requires_selection,
            "selection_handler": self.selection_handler,
            "data": self.data
        }

def register_item_handler(handler_name: str, handler_func: Callable) -> None:
    """
    Register a handler function for an item type
    
    Args:
        handler_name: The name of the handler
        handler_func: The function that implements the handler
    """
    ITEM_HANDLERS[handler_name] = handler_func
    logging.info(f"Registered item handler for type: {handler_name}")

def register_item(
    id: str,
    name: str,
    description: str,
    item_type: str,
    rarity: str,
    base_price: int,
    handler_func: Callable = None,
    selection_func: Callable = None,
    image: str = None,
    uses: int = 1,
    activation_type: str = "active",
    requires_selection: bool = False,
    data: Dict[str, Any] = None
) -> ItemDefinition:
    """
    Register an item in the item registry along with its handler function.
    
    Args:
        id: Unique identifier for the item
        name: Display name of the item
        description: Description text
        item_type: Type of item (consumable, equipment, etc.)
        rarity: Rarity level (common, uncommon, rare, epic, legendary)
        base_price: Base price in coins
        handler_func: The function that implements the item's effect
        image: URL or path to item image
        uses: Number of uses (1 for single-use items)
        activation_type: How item is activated (active, passive, triggered)
        data: Additional item-specific data
        
    Returns:
        The registered item definition
    """
    # If a handler is provided, register it with the item's ID as the handler name
    activation_handler = None
    selection_handler = None

    if handler_func:
        activation_handler = id
        register_item_handler(id, handler_func)

    if selection_func:
        selection_handler = id + "_selection"
        register_item_handler(selection_handler, selection_func)

    
    item = ItemDefinition(
        id=id,
        name=name,
        description=description,
        item_type=item_type,
        rarity=rarity,
        base_price=base_price,
        image=image,
        uses=uses,
        activation_type=activation_type,
        activation_handler=activation_handler,
        requires_selection=requires_selection,
        selection_handler=selection_func,
        data=data
    )
    
    ITEM_REGISTRY[id] = item
    logging.debug(f"Registered item: {name} (ID: {id})")
    return item

def get_item(item_id: str) -> Optional[ItemDefinition]:
    """Get an item from the registry by ID"""
    return ITEM_REGISTRY.get(item_id)

def get_all_items() -> List[ItemDefinition]:
    """Get all registered items"""
    return list(ITEM_REGISTRY.values())

def get_items_by_type(item_type: str) -> List[ItemDefinition]:
    """Get all items of a specific type"""
    return [item for item in ITEM_REGISTRY.values() if item.item_type == item_type]

def get_items_by_rarity(rarity: str) -> List[ItemDefinition]:
    """Get all items of a specific rarity"""
    return [item for item in ITEM_REGISTRY.values() if item.rarity == rarity]

def get_handler(handler_name: str) -> Optional[Callable]:
    """Get a handler function by name"""
    return ITEM_HANDLERS.get(handler_name)

# ==========================================================
# Define all items and their handlers below
# ==========================================================

# Movement Items
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

register_item(
    id="dice_boost_small",
    name="Small Dice Boost",
    description="Adds +1 to your next dice roll",
    item_type="consumable",
    rarity="common",
    base_price=10,
    handler_func=dice_modifier_handler,
    uses=1,
    activation_type="active",
    data={"modifier_value": 1, "duration": 1}
)

register_item(
    id="dice_boost_medium",
    name="Medium Dice Boost",
    description="Adds +2 to your next dice roll",
    item_type="consumable",
    rarity="uncommon",
    base_price=20,
    handler_func=dice_modifier_handler,
    uses=1,
    activation_type="active",
    data={"modifier_value": 2, "duration": 1}
)

register_item(
    id="dice_boost_large",
    name="Large Dice Boost",
    description="Adds +3 to your next dice roll",
    item_type="consumable",
    rarity="rare",
    base_price=30,
    handler_func=dice_modifier_handler,
    uses=1,
    activation_type="active",
    data={"modifier_value": 3, "duration": 1}
)

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

register_item(
    id="extra_d4",
    name="Extra d4",
    description="Adds a d4 to your next roll",
    item_type="consumable",
    rarity="common",
    base_price=15,
    handler_func=bonus_dice_handler,
    uses=1,
    activation_type="active",
    data={"dice_sides": 4, "duration": 1}
)

register_item(
    id="extra_d6",
    name="Extra d6",
    description="Adds a d6 to your next roll",
    item_type="consumable", 
    rarity="uncommon",
    base_price=25,
    handler_func=bonus_dice_handler,
    uses=1,
    activation_type="active",
    data={"dice_sides": 6, "duration": 1}
)

register_item(
    id="extra_d8",
    name="Extra d8",
    description="Adds a d8 to your next roll",
    item_type="consumable",
    rarity="rare",
    base_price=35,
    handler_func=bonus_dice_handler,
    uses=1,
    activation_type="active",
    data={"dice_sides": 8, "duration": 1}
)

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

register_item(
    id="double_roll",
    name="Double Roll",
    description="Roll twice and take the higher result",
    item_type="consumable",
    rarity="epic",
    base_price=50,
    handler_func=double_roll_handler,
    uses=1,
    activation_type="active",
    data={}
)

# Currency Items
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

register_item(
    id="small_coin_pouch",
    name="Small Coin Pouch",
    description="Gain 10 coins",
    item_type="consumable",
    rarity="common",
    base_price=5,
    handler_func=bonus_coins_handler,
    uses=1,
    activation_type="active",
    data={"coin_amount": 10}
)

register_item(
    id="medium_coin_pouch",
    name="Medium Coin Pouch",
    description="Gain 25 coins",
    item_type="consumable",
    rarity="uncommon",
    base_price=15,
    handler_func=bonus_coins_handler,
    uses=1,
    activation_type="active",
    data={"coin_amount": 25}
)

register_item(
    id="large_coin_pouch",
    name="Large Coin Pouch",
    description="Gain 50 coins",
    item_type="consumable",
    rarity="rare", 
    base_price=30,
    handler_func=bonus_coins_handler,
    uses=1,
    activation_type="active",
    data={"coin_amount": 50}
)

# Special Items
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

register_item(
    id="teleport_scroll",
    name="Teleport Scroll",
    description="Teleport to a random tile on the board",
    item_type="consumable",
    rarity="rare",
    base_price=40,
    handler_func=teleport_handler,
    uses=1,
    activation_type="active",
    data={}
)

def star_finder_handler(event_id, team_id, save, item_data):
    """Handler for star finder items"""
    return {
        "message": "The nearest star location has been revealed on your map!",
        "effect": {
            "star_revealed": True
        }
    }

register_item(
    id="star_finder",
    name="Star Finder",
    description="Reveals the location of the nearest star on the map",
    item_type="consumable",
    rarity="uncommon",
    base_price=20,
    handler_func=star_finder_handler,
    uses=1, 
    activation_type="active",
    data={}
)

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

register_item(
    id="star_discount",
    name="Star Discount",
    description="Your next star purchase is 50% off",
    item_type="consumable",
    rarity="rare",
    base_price=30,
    handler_func=star_discount_handler,
    uses=1,
    activation_type="active",
    data={"discount_percent": 50}
)

# Buff Items
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

register_item(
    id="strength_buff",
    name="Strength Potion",
    description="Gain a strength buff for 3 turns",
    item_type="consumable",
    rarity="uncommon",
    base_price=20,
    handler_func=buff_handler,
    uses=1,
    activation_type="active", 
    data={"buff_type": "strength", "buff_duration": 3}
)

register_item(
    id="speed_buff",
    name="Speed Potion",
    description="Gain a speed buff for 3 turns",
    item_type="consumable",
    rarity="uncommon", 
    base_price=20,
    handler_func=buff_handler,
    uses=1,
    activation_type="active",
    data={"buff_type": "speed", "buff_duration": 3}
)

register_item(
    id="luck_buff",
    name="Luck Potion",
    description="Gain a luck buff for 3 turns",
    item_type="consumable", 
    rarity="uncommon",
    base_price=20,
    handler_func=buff_handler,
    uses=1,
    activation_type="active",
    data={"buff_type": "luck", "buff_duration": 3}
)

# Equipment Items
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
        old_item_data = get_item(old_item)
        if old_item_data:
            old_item_entry = {
                "id": old_item,
                "name": old_item_data.name,
                "description": old_item_data.description,
                "item_type": old_item_data.item_type,
                "rarity": old_item_data.rarity,
                "uses_remaining": old_item_data.uses,
                "activation_handler": old_item_data.activation_handler
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

register_item(
    id="explorer_boots",
    name="Explorer's Boots",
    description="Increases movement speed by 1",
    item_type="equipment",
    rarity="rare",
    base_price=50,
    handler_func=equipment_passive_handler,
    uses=0,  # Equipment has unlimited uses
    activation_type="passive",
    data={"slot": "cape", "stat_bonus": {"movement": 1}}
)

register_item(
    id="lucky_charm",
    name="Lucky Charm",
    description="Increases luck when landing on special tiles",
    item_type="equipment",
    rarity="epic", 
    base_price=75,
    handler_func=equipment_passive_handler,
    uses=0,  # Equipment has unlimited uses
    activation_type="passive",
    data={"slot": "jewelry", "stat_bonus": {"luck": 1}}
)

register_item(
    id="royal_crown",
    name="Royal Crown",
    description="Makes you look fancy and gives a 10% discount in shops",
    item_type="equipment",
    rarity="legendary",
    base_price=100,
    handler_func=equipment_passive_handler,
    uses=0,  # Equipment has unlimited uses
    activation_type="passive",
    data={"slot": "helmet", "stat_bonus": {"shop_discount": 0.1}}
)

# Legendary Items
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

register_item(
    id="magic_lamp",
    name="Magic Lamp",
    description="Grants three wishes! (Actually just teleports you to any tile on the board)",
    item_type="consumable",
    rarity="legendary",
    base_price=100,
    handler_func=magic_lamp_handler,
    uses=3,
    activation_type="active",
    data={}
)

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

register_item(
    id="star_stealer",
    name="Star Stealer",
    description="Steal a star from another team",
    item_type="consumable", 
    rarity="legendary",
    base_price=120,
    handler_func=star_stealer_handler,
    uses=1,
    activation_type="active",
    data={}
)

def osmumten_fang_handler(event_id, team_id, save, item_data):
    """Handler for Osmumten's Fang item (choose exactly what number to roll)"""
    # In a real implementation, this would show UI for choosing a number
    # For now, just a placeholder
    return {
        "message": "You can now choose exactly what number to roll!",
        "effect": {
            "choose_number": True
        }
    }

def osmumten_fang_selection_handler(event_id, team_id, save, item_data):
    """Handler for selecting a number with Osmumten's Fang"""
    # In a real implementation, this would process the selected number
    # For now, just a placeholder
    selected_number = item_data.get("selected_option", 1)

    save.dice = []
    save.modifier = selected_number
    
    return {
        "message": f"You chose to roll a {selected_number}!",
        "effect": {
            "selected_number": selected_number
        }
    }

register_item(
    id="osmumten_fang",
    name="Osmumten's Fang",
    description="Choose exactly what number to roll",
    item_type="consumable",
    rarity="legendary",
    base_price=150,
    handler_func=osmumten_fang_handler,
    uses=1,
    activation_type="active",
    data={}
)

def teleport_tablet_handler(event_id, team_id, save, item_data):
    """Handler for teleport tablet item (teleport to another team's location)"""
    # In a real implementation, this would show UI for choosing a team
    # For now, just a placeholder
    return {
        "message": "You can now choose a team to teleport to!",
        "effect": {
            "choose_team": True
        }
    }