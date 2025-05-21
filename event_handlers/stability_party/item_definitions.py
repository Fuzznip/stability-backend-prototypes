"""
Item definitions for Stability Party 3

This module contains both the item definitions and their handlers together.
Each item is registered with its corresponding handler function,
keeping the definition and functionality together for better maintenance.
"""

import uuid
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from event_handlers.stability_party.save_data import SaveData, save_team_data
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
    name="Shrink-Me Potion",
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

def weighted_die_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    # This is a placeholder for the weighted die handler
    # The actual implementation would depend on the game logic

    save_data.dice = [4]
    save_data.modifier = 2
    return {
        "message": f"used a Weighted Die! Your next roll will be increased by 2.",
        "modifier": save_data.modifier
    }

register_item(
    id="weighted_die",
    name="Rogue's Die",
    description="Your next roll will be between 3 and 6.",
    item_type="consumable",
    rarity="uncommon",
    base_price=30,
    handler_func=weighted_die_handler,
    uses=1,
    activation_type="active",
    data={}
)

def coin_pouch_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    # This is a placeholder for the coin pouch handler
    # The actual implementation would depend on the game logic

    gained_coins = random.randint(40, 80)
    save_data.coins += gained_coins
    return {
        "message": f"used a Coin Pouch. Received {gained_coins} coins!",
        "gained_coins": save_data.coins
    }

register_item(
    id="coin_pouch",
    name="Coin Pouch",
    description="Instantly gain 40-80 coins.",
    item_type="consumable",
    rarity="rare",
    base_price=55,
    handler_func=coin_pouch_handler,
    uses=1,
    activation_type="active",
    data={}
)

def mystery_box_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    available_items = get_items_by_rarity("common") + get_items_by_rarity("uncommon") + get_items_by_rarity("rare") + get_items_by_rarity("epic")
    selected_item_1 = random.choice(available_items)
    selected_item_2 = random.choice(available_items)

    def dialogue_generator(item: ItemDefinition) -> str:
        if item.rarity == "common":
            return f"Inside the box you find a **{item.name}**! Better luck nexte time!"
        elif item.rarity == "uncommon":
            return f"Inside the box you find a **{item.name}**! Excellent!"
        elif item.rarity == "rare":
            return f"Inside the box you find a **{item.name}**! Excellent!"
        elif item.rarity == "epic":
            return f"Inside the box you find a **{item.name}**! Amazing!"
        elif item.rarity == "legendary":
            return f"Inside the box you find a **{item.name}**! Amazing!"

    dialogue_1 = dialogue_generator(selected_item_1)
    dialogue_2 = dialogue_generator(selected_item_2)
    message = f"used a Mystery Box! Let's take a peek...\n\n{dialogue_1}\n{dialogue_2}"

    from event_handlers.stability_party.item_system import add_item_to_inventory
    add_item_to_inventory(event_id, team_id, selected_item_1.id)
    add_item_to_inventory(event_id, team_id, selected_item_2.id)

    return {
        "message": message,
        "items": [selected_item_1.id, selected_item_2.id]
    }

register_item(
    id="mystery_box",
    name="Mystery Box",
    description="Open a box to receive 2 random items.",
    item_type="consumable",
    rarity="rare",
    base_price=65,
    handler_func=mystery_box_handler,
    uses=1,
    activation_type="active",
    data={}
)

def double_dice_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    # This is a placeholder for the double dice handler
    # The actual implementation would depend on the game logic

    if save_data.dice:
        save_data.dice = [save_data.dice[0], save_data.dice[0]]
    else:
        save_data.dice = [4, 4]    
    
    return {
        "message": f"used Double Dice! Your next roll will be with two dice!",
        "dice": save_data.dice
    }

register_item(
    id="double_dice",
    name="Twinflame Staff",
    description="Your next roll will be with two dice.",
    item_type="consumable",
    rarity="rare",
    base_price=70,
    handler_func=double_dice_handler,
    uses=1,
    activation_type="active",
    data={}
)

def jewelry_box_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    if not save_data.dice:
        return { "error": "No rolls to select from." }
    from collections import Counter
    import itertools

    possible_values = []
    for i in range(len(save_data.dice), sum(save_data.dice) + 1):
        possible_value = i + save_data.modifier
        # For each possible value, calculate the probability of rolling that value
        # and add it to the list of possible values

        # Calculate the probability of rolling 'i' with the given dice

        dice = save_data.dice
        outcomes = list(itertools.product(*[range(1, d + 1) for d in dice]))
        total_outcomes = len(outcomes)
        value_counts = Counter(sum(roll) for roll in outcomes)
        probability = value_counts.get(i, 0) / total_outcomes if total_outcomes > 0 else 0
        
        possible_values.append({
            "name": f"Roll a {possible_value}",
            "description": f"Original Probability: {probability:.2%}",
            "value": str(possible_value),
        })

    return {
        "message": f"used a Jewelry Box! Select a value between {1 + save_data.modifier} and {sum(save_data.dice) + save_data.modifier}.",
        "options": possible_values
    }

def jewelry_box_selection_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any], selected_value: str) -> Dict[str, Any]:
    # This is a placeholder for the jewelry box selection handler
    # The actual implementation would depend on the game logic

    try:
        selected_value = int(selected_value)
    except ValueError:
        return { "error": "Invalid selection. Please select a valid number." }
    
    if selected_value < 1 or selected_value > sum(save_data.dice) + save_data.modifier:
        return { "error": f"Invalid selection. Please select a number between 1 and {sum(save_data.dice) + save_data.modifier}." }
    
    # Set the dice to the selected value
    save_data.dice = [1]
    save_data.modifier = selected_value - 1
    return {
        "message": f"used a Jewelry Box! Your next roll will be {selected_value}.",
        "dice": save_data.dice
    }

register_item(
    id="jewelry_box",
    name="Jewelry Box",
    description="Select a value between 1 and the sum of your dice rolls.",
    item_type="consumable",
    rarity="epic",
    base_price=100,
    handler_func=jewelry_box_handler,
    selection_func=jewelry_box_selection_handler,
    uses=1,
    activation_type="active",
    requires_selection=True,
    data={}
)

def bounty_target_teleport(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    from models.models import EventTeams
    from models.stability_party_3 import SP3EventTiles, SP3Regions
    team_id = uuid.UUID(team_id) # WHY DO I NEED THIS????
    teams = EventTeams.query.filter_by(event_id=event_id).all()
    available_teams = [team for team in teams if team.id != team_id]
    if not available_teams:
        return { "error": "No other teams available to teleport to." }
    
    options = []
    for team in available_teams:
        print(f"{team.id}{type(team.id)} VS {team_id}{type(team_id)}")
        available_team_name = team.name
        available_team_id = str(team.id)
        available_team_tile_id = uuid.UUID(team.data.get("currentTile"))
        tile = SP3EventTiles.query.filter_by(id=available_team_tile_id).first()
        tile_name = tile.name if tile else "Unknown Tile"
        region = SP3Regions.query.filter_by(id=tile.region_id).first()
        region_name = region.name if region else "Unknown Region"

        options.append({
            "name": available_team_name,
            "description": f"Current Tile: {tile_name} in {region_name}",
            "value": available_team_id
        })

    return {
        "message": f"used a Bounty Target Teleport! Select a team to teleport to.",
        "options": options
    }

def bounty_target_teleport_selection(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any], selected_value: str) -> Dict[str, Any]:
    # This is a placeholder for the bounty target teleport selection handler
    # The actual implementation would depend on the game logic

    try:
        selected_value = uuid.UUID(selected_value)
    except ValueError:
        return { "error": "Invalid team ID." }
    
    from models.models import EventTeams
    from models.stability_party_3 import SP3EventTiles, SP3EventTileChallengeMapping, SP3Regions
    selected_team = EventTeams.query.filter_by(id=selected_value).first()
    selected_team_save_data = SaveData.from_dict(selected_team.data)
    save_data.previousTile = save_data.currentTile
    save_data.currentTile = selected_team_save_data.currentTile
    save_data.islandId = selected_team_save_data.islandId
    
    # Check to see if the tile is a random tile or not
    tile = SP3EventTiles.query.filter_by(id=save_data.currentTile).first()
    if tile.data.get("category", "ANY") == "RANDOM":
        challenge_choices = SP3EventTileChallengeMapping.query.filter_by(tile_id=save_data.currentTile).all()
        save_data.currentChallenges = [random.choice(challenge_choices).challenge_id]

    region = SP3Regions.query.filter_by(id=tile.region_id).first()

    return {
        "message": f"used a Bounty Target Teleport! You have been teleported to team {selected_team.name}. You are now on tile {tile.name} on {region.name}.",
        "currentTile": str(save_data.currentTile)
    }

register_item(
    id="bounty_target_teleport",
    name="Bounty Target Teleport",
    description="Choose a team to warp to.",
    item_type="consumable",
    rarity="epic",
    base_price=90,
    handler_func=bounty_target_teleport,
    selection_func=bounty_target_teleport_selection,
    uses=1,
    activation_type="active",
    requires_selection=True,
    data={}
)

def genie_lamp_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    from models.models import Events
    from models.stability_party_3 import SP3EventTiles, SP3Regions

    # First, teleport to the star tile
    event = Events.query.filter_by(id=event_id).first()
    star_tile_ids = event.data.get("star_tiles", [])
    random_tile = random.choice(star_tile_ids)
    star_tile = SP3EventTiles.query.filter_by(id=random_tile).first()
    region = SP3Regions.query.filter_by(id=star_tile.region_id).first()
    save_data.previousTile = save_data.currentTile
    save_data.currentTile = random_tile
    save_data.islandId = star_tile.region_id
    save_data.currentChallenges = []
    save_data.isTileCompleted = False

    options = [
        {
            "name": "Buy the star",
            "description": f"Buy the star for 100 coins.",
            "value": "buy"
        },
        {
            "name": "Don't buy the star",
            "description": f"Leave the star and continue from here.",
            "value": "leave"
        }
    ]

    return {
        "message": f"used a Genie Lamp! You have been teleported to tile {star_tile.name} on {region.name}.",
        "options": options
    }

def genie_lamp_selection_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any], selected_value: str) -> Dict[str, Any]:
    # This is a placeholder for the genie lamp selection handler
    # The actual implementation would depend on the game logic

    from models.models import EventTeams, Events
    from models.stability_party_3 import SP3EventTiles, SP3Regions

    selected_team = EventTeams.query.filter_by(id=team_id).first()
    previous_tile_name = SP3EventTiles.query.filter_by(id=save_data.previousTile).first().name
    previous_region_name = SP3Regions.query.filter_by(id=save_data.islandId).first().name
    
    if selected_value == "buy":
        if save_data.coins < 100:
            return { "message": "Not enough coins to buy the star." }

        save_data.coins -= 100
        save_data.stars += 1

        # Move the star to another tile
        # Move the star to a new tile
        new_star_tile_id = None
        all_regions = SP3Regions.query.all()
        applicable_regions = []

        from event_handlers.stability_party.send_event_notification import send_event_notification
        from event_handlers.stability_party.stability_party_handler import is_region_populated, is_shop_tile, is_dock_tile, is_star_tile
        from sqlalchemy.orm.attributes import flag_modified
        from app import db

        for region in all_regions:
            if not is_region_populated(region.id):
                applicable_regions.append(region.id)
                
        applicable_region_tiles = SP3EventTiles.query.filter(
            SP3EventTiles.event_id == event_id,
            SP3EventTiles.region_id.in_(applicable_regions),
        ).all()

        # Filter out tiles that are shops, docks, or already have stars
        applicable_region_tiles = [tile for tile in applicable_region_tiles if not is_shop_tile(tile.id) and not is_dock_tile(tile.id) and not is_star_tile(tile.id)]
        logging.info(f"Applicable region tiles for star placement: {[tile.name for tile in applicable_region_tiles]}")
        if applicable_region_tiles:
            new_star_tile = random.choice(applicable_region_tiles)
            new_star_tile_id = new_star_tile.id
            logging.info(f"Star moved to tile {new_star_tile.name} (ID: {new_star_tile_id})")
        else:
            logging.error("No valid tiles available for star placement.")
            return {"error": "No valid tiles available for star placement"}, 400
        
        old_star_tile_id = save_data.currentTile
        event = Events.query.filter_by(id=event_id).first()
        star_tiles = event.data.get("star_tiles")
        star_tiles.remove(str(old_star_tile_id))
        star_tiles.append(str(new_star_tile_id))
        event.data["star_tiles"] = star_tiles
        flag_modified(event, "data")
        db.session.commit()

        team_name = EventTeams.query.filter_by(id=team_id).first().name
        old_star_tile = SP3EventTiles.query.filter_by(id=old_star_tile_id).first()
        old_star_tile_name = old_star_tile.name
        old_star_tile_region = SP3Regions.query.filter_by(id=old_star_tile.region_id).first().name
        new_star_tile = SP3EventTiles.query.filter_by(id=new_star_tile_id).first()
        new_star_tile_name = new_star_tile.name
        new_star_tile_region = SP3Regions.query.filter_by(id=new_star_tile.region_id).first().name
        send_event_notification(event_id, team_id, f"{team_name} has purchased a star!", f"{team_name} has purchased the star on {old_star_tile_name} on {old_star_tile_region}!\n\nThe star has been moved to {new_star_tile_name} on {new_star_tile_region}!")

        return {
            "message": f"used a Genie Lamp! They have teleported from {previous_tile_name} on {previous_region_name} to tile {old_star_tile_name} on {old_star_tile_region}.",
            "coins": save_data.coins,
            "isTileCompleted": save_data.isTileCompleted
        }
    elif selected_value == "leave":
        team_name = selected_team.name
        old_star_tile = SP3EventTiles.query.filter_by(id=save_data.previousTile).first()
        old_star_tile_name = old_star_tile.name
        old_star_tile_region = SP3Regions.query.filter_by(id=old_star_tile.region_id).first().name

        return {
            "message": f"used a Genie Lamp! They have teleported from {previous_tile_name} on {previous_region_name} to tile {old_star_tile_name} on {old_star_tile_region}.\n\nThe star has been left as-is."
        }
    else:
        return { "error": "Invalid selection." }

register_item(
    id="genie_lamp",
    name="Genie's Lamp",
    description="Teleport to a random star tile and have a chance to buy it.",
    item_type="consumable",
    rarity="legendary",
    base_price=100,
    handler_func=genie_lamp_handler,
    selection_func=genie_lamp_selection_handler,
    uses=1,
    activation_type="active",
    requires_selection=True,
    data={}
)

def complete_current_tile_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    # This is a placeholder for the complete current tile handler
    # The actual implementation would depend on the game logic
    save_data.isTileCompleted = True
    save_data.dice = [4]

    from models.stability_party_3 import SP3EventTiles, SP3Regions
    
    tile_name = SP3EventTiles.query.filter_by(id=save_data.currentTile).first().name
    region_name = SP3Regions.query.filter_by(id=save_data.islandId).first().name

    return {
        "message": f"used a Complete Current Tile! They have completed the tile {tile_name} on {region_name}.",
        "isTileCompleted": True
    }

register_item(
    id="complete_current_tile",
    name="Turael Skip",
    description="Complete the current tile.",
    item_type="consumable",
    rarity="uncommon",
    base_price=20,
    handler_func=complete_current_tile_handler,
    uses=1,
    activation_type="active",
    data={}
)

def moonlight_moth_mix_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any]) -> Dict[str, Any]:
    from models.models import EventTeams
    from models.stability_party_3 import SP3EventTiles, SP3Regions
    team_id = uuid.UUID(team_id) # WHY DO I NEED THIS????
    teams = EventTeams.query.filter_by(event_id=event_id).all()
    available_teams = [team for team in teams if team.id != team_id]
    if not available_teams:
        return { "error": "No other teams available to select." }
    
    options = []
    for team in available_teams:
        print(f"{team.id}{type(team.id)} VS {team_id}{type(team_id)}")
        available_team_name = team.name
        available_team_id = str(team.id)
        available_team_coins = team.data.get("coins", 0)
        available_team_stars = team.data.get("stars", 0)

        options.append({
            "name": available_team_name,
            "description": f"{available_team_stars} stars, {available_team_coins} coins",
            "value": available_team_id
        })

    return {
        "message": f"used a Moonlight Moth Mix! Select an additional team to award 20 coins to.",
        "options": options
    }

def moonlight_moth_mix_selection_handler(event_id: uuid.UUID, team_id: uuid.UUID, save_data: SaveData, item_data: Dict[str, Any], selected_value: str) -> Dict[str, Any]:
    try:
        selected_value = uuid.UUID(selected_value)
    except ValueError:
        return { "error": "Invalid team ID." }
    
    from models.models import EventTeams
    team = EventTeams.query.filter_by(id=team_id).first()
    selected_team = EventTeams.query.filter_by(id=selected_value).first()
    selected_team_save_data = SaveData.from_dict(selected_team.data)
    save_data.coins += 20
    selected_team_save_data.coins += 20
    
    # We only need to save the selected team data since our team data will be saved automatically
    save_team_data(selected_team, selected_team_save_data)

    return {
        "message": f"used a Moonlight Moth Mix! 20 coins have been awarded to {team.name} (Now {save_data.coins} coins) and {selected_team.name} (Now {selected_team_save_data.coins} coins).",
    }

register_item(
    id="moonlight_moth_mix",
    name="Moonlight Moth Mix",
    description="Select another team. You will both receive 20 coins.",
    item_type="consumable",
    rarity="epic",
    base_price=0,
    handler_func=moonlight_moth_mix_handler,
    selection_func=moonlight_moth_mix_selection_handler,
    uses=1,
    activation_type="active",
    requires_selection=True,
    data={}
)
