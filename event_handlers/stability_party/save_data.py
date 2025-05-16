from app import db
from models.models import EventTeams
from sqlalchemy.orm.attributes import flag_modified  # Add this import
import uuid
import logging

# Roll Progression System
class RollState:
    ACTION_TYPES = {
        "CONTINUE": "continue",
        "SHOP": "shop",
        "STAR": "star",
        "DOCK": "dock",
        "CROSSROAD": "crossroad",
        "COMPLETE": "complete",
        "FIRST_ROLL": "first_roll",     # Prompt for island choice
        "ISLAND_SELECTION": "island_selection" # Player has chosen starting island
    }
    
    def __init__(self, event_id, team_id, roll_total_for_turn, current_tile_id=None):
        self.event_id = event_id
        self.team_id = team_id
        self.starting_tile_id = current_tile_id # Tile where this specific movement sequence began
        self.current_tile_id = current_tile_id # Current tile in the movement sequence
        self.roll_total_for_turn = roll_total_for_turn # The total spaces this roll grants
        self.roll_remaining = roll_total_for_turn # Spaces left in this specific movement sequence
        self.dice_results_for_roll = [] # Actual dice values rolled for this turn
        self.modifier_for_roll = 0      # Modifier applied to this roll
        self.path_taken_this_turn = []  # Tiles visited in this movement sequence
        self.action_required = None     # e.g., "SHOP", "CROSSROAD", "COMPLETE"
        self.action_data = {}           # Data for the action (e.g., shop items, crossroad options)
    
    def to_dict(self):
        return {
            "event_id": str(self.event_id),
            "team_id": str(self.team_id),
            "starting_tile_id": str(self.starting_tile_id) if self.starting_tile_id else None,
            "current_tile_id": str(self.current_tile_id) if self.current_tile_id else None,
            "roll_total_for_turn": self.roll_total_for_turn,
            "roll_remaining": self.roll_remaining,
            "dice_results_for_roll": self.dice_results_for_roll,
            "modifier_for_roll": self.modifier_for_roll,
            "path_taken_this_turn": [str(tile_id) for tile_id in self.path_taken_this_turn],
            "action_required": self.action_required,
            "action_data": self.action_data
        }
    
    @staticmethod
    def from_dict(data: dict) -> "RollState":
        roll_state = RollState(
            event_id=uuid.UUID(data["event_id"]),
            team_id=uuid.UUID(data["team_id"]),
            roll_total_for_turn=data.get("roll_total_for_turn", 0),
            current_tile_id=uuid.UUID(data["current_tile_id"]) if data.get("current_tile_id") else None
        )
        roll_state.roll_remaining = data.get("roll_remaining", 0)
        roll_state.dice_results_for_roll = data.get("dice_results_for_roll", [])
        roll_state.modifier_for_roll = data.get("modifier_for_roll", 0)
        roll_state.path_taken_this_turn = [uuid.UUID(tile) for tile in data.get("path_taken_this_turn", [])]
        roll_state.action_required = data.get("action_required", None)
        roll_state.action_data = data.get("action_data", {})
        
        return roll_state
        
    def update_save_data(self, save):
        """Update the SaveData object with the current roll state"""
        save.roll_state = self
        
    @staticmethod
    def from_save_data(event_id, team_id, save_data: dict) -> "RollState":
        """Create a RollState from saved roll_state data"""
        if not save_data:
            return None
        return RollState.from_dict({
            "event_id": str(event_id),
            "team_id": str(team_id),
            **save_data
        })

class Equipment:
    helmet: str
    armor: str
    weapon: str
    jewelry: str
    cape: str

    def to_dict(self) -> dict:
        return {
            "helmet": self.helmet,
            "armor": self.armor,
            "weapon": self.weapon,
            "jewelry": self.jewelry,
            "cape": self.cape,
        }

    @staticmethod
    def from_dict(data: dict) -> "Equipment":
        if not data:
            data = {
                "helmet": "",
                "armor": "",
                "weapon": "",
                "jewelry": "",
                "cape": ""
            }
        equipment = Equipment()
        equipment.helmet = data.get("helmet", "")
        equipment.armor = data.get("armor", "")
        equipment.weapon = data.get("weapon", "")
        equipment.jewelry = data.get("jewelry", "")
        equipment.cape = data.get("cape", "")
        return equipment

class SaveData:
    team: EventTeams

    previousTile: uuid.UUID
    currentTile: uuid.UUID
    stars: int
    coins: int
    islandId: uuid.UUID
    itemList: list[dict]
    pendingItemActivation: dict
    equipment: Equipment

    dice: list[int]
    modifier: int

    isTileCompleted: bool
    isRolling: bool

    buffs: list[dict]
    debuffs: list[dict]

    textChannelId: str
    voiceChannelId: str

    tileProgress: dict[str, dict[str, int]]
    
    roll_state: RollState | None = None  # Optional roll state for tracking current roll

    def to_dict(self) -> dict:
        path_taken = []
        if hasattr(self, 'path_taken_this_turn') and self.path_taken_this_turn:
            path_taken = [str(tile_id) for tile_id in self.path_taken_this_turn]
            
        return {
            "previousTile": str(self.previousTile) if self.previousTile else None,
            "currentTile": str(self.currentTile) if self.currentTile else None,
            "stars": self.stars,
            "coins": self.coins,
            "islandId": str(self.islandId) if self.islandId else None,
            "itemList": self.itemList,
            "pendingItemActivation": self.pendingItemActivation,
            "equipment": self.equipment.to_dict() if self.equipment else None,
            "dice": self.dice,
            "modifier": self.modifier,
            "isTileCompleted": self.isTileCompleted,
            "isRolling": self.isRolling,
            "buffs": self.buffs,
            "debuffs": self.debuffs,
            "textChannelId": self.textChannelId,
            "voiceChannelId": self.voiceChannelId,
            "tileProgress": {
                challenge_id: {task_id: progress for task_id, progress in tasks.items()}
                for challenge_id, tasks in self.tileProgress.items()
            },
            "roll_state": self.roll_state.to_dict() if self.roll_state else None,
        }
    
    @staticmethod
    def from_dict(data: dict) -> "SaveData":
        save_data = SaveData()
        save_data.previousTile = uuid.UUID(data["previousTile"]) if data.get("previousTile") else None
        save_data.currentTile = uuid.UUID(data["currentTile"]) if data.get("currentTile") else None
        save_data.stars = data.get("stars", 0)
        save_data.coins = data.get("coins", 0)
        save_data.islandId = uuid.UUID(data["islandId"]) if data.get("islandId") else None
        save_data.itemList = data.get("itemList", [])
        save_data.pendingItemActivation = data.get("pendingItemActivation", {})
        save_data.equipment = Equipment.from_dict(data.get("equipment", {}) if "equipment" in data else {})
        save_data.dice = data.get("dice", [])
        save_data.modifier = data.get("modifier", 0)
        save_data.isTileCompleted = data.get("isTileCompleted", False)
        save_data.isRolling = data.get("isRolling", False)
        save_data.buffs = data.get("buffs", [])
        save_data.debuffs = data.get("debuffs", [])
        save_data.textChannelId = data.get("textChannelId", "")
        save_data.voiceChannelId = data.get("voiceChannelId", "")
        save_data.tileProgress = {
            challenge_id: {task_id: progress for task_id, progress in tasks.items()}
            for challenge_id, tasks in data.get("tileProgress", {}).items()
        }
        
        save_data.roll_state = RollState.from_save_data(
            event_id=data.get("event_id"),
            team_id=data.get("team_id"),
            save_data=data.get("roll_state", {})
        ) if "roll_state" in data else None
        
        return save_data

# Ensure save_team_data is correctly flagging modifications and committing
def save_team_data(team: EventTeams, save: SaveData):
    team.data = save.to_dict()
    logging.debug(f"Preparing to save team data for team {team.id}: {team.data}")
    flag_modified(team, "data")
    try:
        db.session.commit()
        logging.debug(f"Team data saved successfully for team {team.id}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving team data for team {team.id}: {e}", exc_info=True)
        raise
