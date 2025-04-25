from app import db
from event_handlers.event_handler import EventSubmission, NotificationResponse, NotificationAuthor, NotificationField
from models.models import Events, EventTeams, EventTeamMemberMappings
from models.stability_party_3 import SP3Regions, SP3EventTiles, SP3EventTileChallengeMapping
from helper.jsonb import load_jsonb, save_jsonb
import uuid
import json
from datetime import datetime, timezone

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
        equipment = Equipment()
        equipment.helmet = data.get("helmet", "")
        equipment.armor = data.get("armor", "")
        equipment.weapon = data.get("weapon", "")
        equipment.jewelry = data.get("jewelry", "")
        equipment.cape = data.get("cape", "")
        return equipment

class SaveData:
    previousTile: int
    currentTile: int
    stars: int
    coins: int
    islandId: int
    itemList: list[int]
    equipment: Equipment

    dice: list[int]
    modifier: int

    isTileCompleted: bool
    isRolling: bool
    currentChallenge: uuid.UUID

    buffs: list[str]
    debuffs: list[str]

    textChannelId: str
    voiceChannelId: str

    tileProgress: dict[uuid.UUID, dict[str, int]]

    def to_dict(self) -> dict:
        return {
            "previousTile": self.previousTile,
            "currentTile": self.currentTile,
            "stars": self.stars,
            "coins": self.coins,
            "islandId": self.islandId,
            "itemList": self.itemList,
            "equipment": self.equipment.to_dict() if self.equipment else None,
            "dice": self.dice,
            "modifier": self.modifier,
            "isTileCompleted": self.isTileCompleted,
            "isRolling": self.isRolling,
            "currentChallenge": str(self.currentChallenge) if self.currentChallenge else None,
            "buffs": self.buffs,
            "debuffs": self.debuffs,
            "textChannelId": self.textChannelId,
            "voiceChannelId": self.voiceChannelId,
            "tileProgress": self.tileProgress,
        }

    @staticmethod
    def from_dict(data: dict) -> "SaveData":
        save_data = SaveData()
        save_data.previousTile = data.get("previousTile", 0)
        save_data.currentTile = data.get("currentTile", 0)
        save_data.stars = data.get("stars", 0)
        save_data.coins = data.get("coins", 0)
        save_data.islandId = data.get("islandId", 0)
        save_data.itemList = data.get("itemList", [])
        save_data.equipment = Equipment.from_dict(data.get("equipment", {}))
        save_data.dice = data.get("dice", [])
        save_data.modifier = data.get("modifier", 0)
        save_data.isTileCompleted = data.get("isTileCompleted", False)
        save_data.isRolling = data.get("isRolling", False)
        save_data.currentChallenge = uuid.UUID(data["currentChallenge"]) if data.get("currentChallenge") else None
        save_data.buffs = data.get("buffs", [])
        save_data.debuffs = data.get("debuffs", [])
        save_data.textChannelId = data.get("textChannelId", "")
        save_data.voiceChannelId = data.get("voiceChannelId", "")
        save_data.tileProgress = data.get("tileProgress", {})
        return save_data

def save_team_data(team: EventTeams, save: SaveData):
    # Convert the save data to a dictionary and store it in the database
    team.data = json.dumps(save.to_dict())
    # Commit the changes to the database
    db.session.commit()

def get_team_challenges(save: SaveData) -> list[tuple[uuid.UUID, str]]:
    challenges: set[tuple[uuid.UUID, str]] = set()
    teamChallenges = SP3EventTileChallengeMapping.query.filter(SP3EventTileChallengeMapping.tile_id == save.currentTile).all()
    challenge: SP3EventTileChallengeMapping
    for challenge in teamChallenges:
        challenges.add((challenge.challenge_id, challenge.type))

    return challenges

def progress_team(event: Events, save: SaveData, data: EventSubmission) -> NotificationResponse:
    for challenge, type in get_team_challenges(save):
        match type:
            case "REGION":
                progress_challenge(challenge, event, save, data)
                pass
            case "TILE":
                progress_challenge(challenge, event, save, data)
                pass
            case "COIN":
                progress_challenge(challenge, event, save, data)
                pass

def progress_event(event: Events, data: EventSubmission) -> None:
    return None

def is_team_accepting_submissions(save: SaveData) -> bool:
    return save.isTileCompleted or save.isRolling

def is_game_accepting_submissions(event: Events) -> bool:
    # TODO: Implement logic to see if the global game state needs us to track something
    return False # For now, we will assume the global state is never accepting submissions

def get_team(eventId: uuid.UUID, rsn: str) -> EventTeams:
    team = EventTeamMemberMappings.query.filter(EventTeamMemberMappings.event_id == eventId).filter(EventTeamMemberMappings.username.ilike(rsn)).first()
    if team is None:
        return None
    return team

def stability_party_handler(data: EventSubmission) -> NotificationResponse:
    now = datetime.now(timezone.utc)
    event = Events.query.filter(Events.start_time <= now).filter(Events.end_time >= now).filter(Events.type == "STABILITY_PARTY").all()

    # For now we will assume there is only one event of this type running at a time
    if event.type != "STABILITY_PARTY":
        return None

    team = get_team(event.id, data.rsn)
    if team is None:
        return None

    if is_game_accepting_submissions(event):
        progress_event(event, data)

    save = SaveData.from_dict(load_jsonb(team.data))

    # log out the save data for debugging
    print(f"Save Data: {save.to_dict()}")
    if not is_team_accepting_submissions(save):
        return None

    return progress_team(event, save, data)
