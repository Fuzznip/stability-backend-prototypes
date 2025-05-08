"""
Item registry for Stability Party 3

This module contains definitions for all standard items in the game.
Items are defined in code for easier maintenance and faster iteration.
"""

import uuid
import logging
from typing import Dict, List, Any, Optional

# Dictionary to store all registered items
ITEM_REGISTRY = {}

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
            "data": self.data
        }

def register_item(
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
    data: Dict[str, Any] = None
) -> ItemDefinition:
    """
    Register an item in the item registry.
    
    Args:
        id: Unique identifier for the item
        name: Display name of the item
        description: Description text
        item_type: Type of item (consumable, equipment, etc.)
        rarity: Rarity level (common, uncommon, rare, epic, legendary)
        base_price: Base price in coins
        image: URL or path to item image
        uses: Number of uses (1 for single-use items)
        activation_type: How item is activated (active, passive, triggered)
        activation_handler: Name of handler function for item effects
        data: Additional item-specific data
        
    Returns:
        The registered item definition
    """
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

# ==========================================================
# Define all standard items below
# ==========================================================

# Movement Items
register_item(
    id="dice_boost_small",
    name="Small Dice Boost",
    description="Adds +1 to your next dice roll",
    item_type="consumable",
    rarity="common",
    base_price=10,
    uses=1,
    activation_type="active",
    activation_handler="dice_modifier",
    data={"modifier_value": 1, "duration": 1}
)

register_item(
    id="dice_boost_medium",
    name="Medium Dice Boost",
    description="Adds +2 to your next dice roll",
    item_type="consumable",
    rarity="uncommon",
    base_price=20,
    uses=1,
    activation_type="active",
    activation_handler="dice_modifier",
    data={"modifier_value": 2, "duration": 1}
)

register_item(
    id="dice_boost_large",
    name="Large Dice Boost",
    description="Adds +3 to your next dice roll",
    item_type="consumable",
    rarity="rare",
    base_price=30,
    uses=1,
    activation_type="active",
    activation_handler="dice_modifier",
    data={"modifier_value": 3, "duration": 1}
)

register_item(
    id="extra_d4",
    name="Extra d4",
    description="Adds a d4 to your next roll",
    item_type="consumable",
    rarity="common",
    base_price=15,
    uses=1,
    activation_type="active",
    activation_handler="bonus_dice",
    data={"dice_sides": 4, "duration": 1}
)

register_item(
    id="extra_d6",
    name="Extra d6",
    description="Adds a d6 to your next roll",
    item_type="consumable", 
    rarity="uncommon",
    base_price=25,
    uses=1,
    activation_type="active",
    activation_handler="bonus_dice",
    data={"dice_sides": 6, "duration": 1}
)

register_item(
    id="extra_d8",
    name="Extra d8",
    description="Adds a d8 to your next roll",
    item_type="consumable",
    rarity="rare",
    base_price=35,
    uses=1,
    activation_type="active",
    activation_handler="bonus_dice",
    data={"dice_sides": 8, "duration": 1}
)

register_item(
    id="double_roll",
    name="Double Roll",
    description="Roll twice and take the higher result",
    item_type="consumable",
    rarity="epic",
    base_price=50,
    uses=1,
    activation_type="active",
    activation_handler="double_roll",
    data={}
)

# Currency Items
register_item(
    id="small_coin_pouch",
    name="Small Coin Pouch",
    description="Gain 10 coins",
    item_type="consumable",
    rarity="common",
    base_price=5,
    uses=1,
    activation_type="active",
    activation_handler="bonus_coins",
    data={"coin_amount": 10}
)

register_item(
    id="medium_coin_pouch",
    name="Medium Coin Pouch",
    description="Gain 25 coins",
    item_type="consumable",
    rarity="uncommon",
    base_price=15,
    uses=1,
    activation_type="active",
    activation_handler="bonus_coins",
    data={"coin_amount": 25}
)

register_item(
    id="large_coin_pouch",
    name="Large Coin Pouch",
    description="Gain 50 coins",
    item_type="consumable",
    rarity="rare", 
    base_price=30,
    uses=1,
    activation_type="active",
    activation_handler="bonus_coins",
    data={"coin_amount": 50}
)

# Special Items
register_item(
    id="teleport_scroll",
    name="Teleport Scroll",
    description="Teleport to a random tile on the board",
    item_type="consumable",
    rarity="rare",
    base_price=40,
    uses=1,
    activation_type="active",
    activation_handler="teleport",
    data={}
)

register_item(
    id="star_finder",
    name="Star Finder",
    description="Reveals the location of the nearest star on the map",
    item_type="consumable",
    rarity="uncommon",
    base_price=20,
    uses=1, 
    activation_type="active",
    activation_handler="star_finder",
    data={}
)

register_item(
    id="star_discount",
    name="Star Discount",
    description="Your next star purchase is 50% off",
    item_type="consumable",
    rarity="rare",
    base_price=30,
    uses=1,
    activation_type="active",
    activation_handler="star_discount",
    data={"discount_percent": 50}
)

# Buff Items
register_item(
    id="strength_buff",
    name="Strength Potion",
    description="Gain a strength buff for 3 turns",
    item_type="consumable",
    rarity="uncommon",
    base_price=20,
    uses=1,
    activation_type="active", 
    activation_handler="buff",
    data={"buff_type": "strength", "buff_duration": 3}
)

register_item(
    id="speed_buff",
    name="Speed Potion",
    description="Gain a speed buff for 3 turns",
    item_type="consumable",
    rarity="uncommon", 
    base_price=20,
    uses=1,
    activation_type="active",
    activation_handler="buff",
    data={"buff_type": "speed", "buff_duration": 3}
)

register_item(
    id="luck_buff",
    name="Luck Potion",
    description="Gain a luck buff for 3 turns",
    item_type="consumable", 
    rarity="uncommon",
    base_price=20,
    uses=1,
    activation_type="active",
    activation_handler="buff",
    data={"buff_type": "luck", "buff_duration": 3}
)

# Equipment Items
register_item(
    id="explorer_boots",
    name="Explorer's Boots",
    description="Increases movement speed by 1",
    item_type="equipment",
    rarity="rare",
    base_price=50,
    uses=0,  # Equipment has unlimited uses
    activation_type="passive",
    activation_handler="equipment_passive",
    data={"slot": "cape", "stat_bonus": {"movement": 1}}
)

register_item(
    id="lucky_charm",
    name="Lucky Charm",
    description="Increases luck when landing on special tiles",
    item_type="equipment",
    rarity="epic", 
    base_price=75,
    uses=0,  # Equipment has unlimited uses
    activation_type="passive",
    activation_handler="equipment_passive",
    data={"slot": "jewelry", "stat_bonus": {"luck": 1}}
)

register_item(
    id="royal_crown",
    name="Royal Crown",
    description="Makes you look fancy and gives a 10% discount in shops",
    item_type="equipment",
    rarity="legendary",
    base_price=100,
    uses=0,  # Equipment has unlimited uses
    activation_type="passive",
    activation_handler="equipment_passive",
    data={"slot": "helmet", "stat_bonus": {"shop_discount": 0.1}}
)

# Legendary Items
register_item(
    id="magic_lamp",
    name="Magic Lamp",
    description="Grants three wishes! (Actually just teleports you to any tile on the board)",
    item_type="consumable",
    rarity="legendary",
    base_price=100,
    uses=3,
    activation_type="active",
    activation_handler="magic_lamp",
    data={}
)

register_item(
    id="star_stealer",
    name="Star Stealer",
    description="Steal a star from another team",
    item_type="consumable", 
    rarity="legendary",
    base_price=120,
    uses=1,
    activation_type="active",
    activation_handler="star_stealer",
    data={}
)