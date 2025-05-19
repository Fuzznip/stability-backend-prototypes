"""
Item definitions for Stability Party 3

This module contains both the item definitions and their handlers together.
Each item is registered with its corresponding handler function,
keeping the definition and functionality together for better maintenance.
"""

import uuid
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from event_handlers.stability_party.save_data import SaveData
import random

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

def lightness_boots_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    save_data.modifier += 1
    return {
        "message": f"used Boots of Lightness! Their next roll will be increased by 1.",
        "modifier": save_data.modifier
    }

register_item(
    id="boots_of_lightness",
    name="Boots of Lightness",
    description="Adds +1 to your next dice roll",
    item_type="consumable",
    rarity="common",
    base_price=10,
    handler_func=lightness_boots_handler,
    uses=1,
    activation_type="active",
    data={}
)

def mini_dice_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    save_data.dice = [3]

    # This is a placeholder for the mini dice handler
    # The actual implementation would depend on the game logic
    return {
        "message": f"used Mini Dice! Your next roll will be between 1 and 3.",
        "dice": save_data.dice
    }

register_item(
    id="mini_dice",
    name="Mini Dice",
    description="Your next roll will be between 1 and 3.",
    item_type="consumable",
    rarity="common",
    base_price=15,
    handler_func=mini_dice_handler,
    uses=1,
    activation_type="active",
    data={}
)
    
def npc_contact_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    available_items = get_items_by_rarity("common") + get_items_by_rarity("uncommon") + get_items_by_rarity("rare")
    npc_names = ["Duradel", "Turael", "Dark Mage", "Bert the Sandman", "Advisor Ghrim", "Amy", "Watson"]

    # Randomly select an item and an NPC
    selected_item = random.choice(available_items)
    selected_npc = random.choice(npc_names)
    npc_dialogue = [
        f"{selected_npc}: 'I have a gift for you!'",
        f"{selected_npc}: 'Take this {selected_item.name}!'",
        f"{selected_npc}: 'Use it wisely!'"
    ]
    from event_handlers.stability_party.item_system import add_item_to_inventory
    add_item_to_inventory(event_id, team_id, selected_item.id)

    # This is a placeholder for the NPC contact handler
    # The actual implementation would depend on the game logic
    return {
        "message": f"used NPC Contact! {selected_npc} has delivered a {selected_item.name}!\n\n{random.choice(npc_dialogue)}",
    }

register_item(
    id="npc_contact",
    name="NPC Contact",
    description="Contact an NPC for help. You will be given a random item within their power.",
    item_type="consumable",
    rarity="uncommon",
    base_price=20,
    handler_func=npc_contact_handler,
    uses=1,
    activation_type="active",
    data={}
)

def sailing_ticket_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    # This is a placeholder for the sailing ticket handler
    # The actual implementation would depend on the game logic

    save_data.buffs.append({
        "type": "sailing_ticket",
        "uses": 1
    })

    return {
        "message": f"used a Sailing Ticket! The next travel will be free.",
    }

register_item(
    id="sailing_ticket",
    name="Sailing Ticket",
    description="Allows you to travel for free once.",
    item_type="consumable",
    rarity="uncommon",
    base_price=20,
    handler_func=sailing_ticket_handler,
    uses=1,
    activation_type="active",
    data={}
)


