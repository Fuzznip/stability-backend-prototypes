from app import db
from event_handlers.event_handler import EventSubmission, NotificationResponse, NotificationAuthor, NotificationField
from models.models import Events, EventTeams, EventTeamMemberMappings, EventChallenges, EventTasks, EventTriggers
from models.stability_party_3 import SP3Regions, SP3EventTiles, SP3EventTileChallengeMapping
from helper.jsonb import update_jsonb_field
import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.orm.attributes import flag_modified  # Add this import

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
    team: EventTeams

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

    tileProgress: dict[str, dict[str, int]]

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
            "tileProgress": {
                challenge_id: {task_id: progress for task_id, progress in tasks.items()}
                for challenge_id, tasks in self.tileProgress.items()
            },
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
        save_data.tileProgress = {
            challenge_id: {task_id: progress for task_id, progress in tasks.items()}
            for challenge_id, tasks in data.get("tileProgress", {}).items()
        }
        return save_data

def save_team_data(team: EventTeams, save: SaveData):
    # Convert the save data to a dictionary and store it in the database
    team.data = save.to_dict()
    logging.debug(f"Saving team data for team {team.id}: {team.data}")  # Log the data being saved

    # Explicitly mark the 'data' field as modified
    flag_modified(team, "data")

    # Commit the changes to the database
    db.session.add(team)  # Ensure the team object is added to the session
    db.session.commit()
    logging.debug(f"Team data saved successfully for team {team.id}")
    logging.debug(f"Team data after commit: {team.data}")  # Log the saved data for debugging

def get_team_challenges(save: SaveData) -> list[SP3EventTileChallengeMapping]:
    challenges: list[SP3EventTileChallengeMapping] = []
    teamChallenges = SP3EventTileChallengeMapping.query.filter(SP3EventTileChallengeMapping.tile_id == save.currentTile).all()
    for challenge in teamChallenges:
        challenges.append(challenge)

    return challenges

def is_challenge_completed(challenge: EventChallenges, task: EventTasks, save: SaveData) -> bool:
    challengeId = str(challenge.id)
    taskId = str(task.id)
    match challenge.type:
        case "OR":
            if save.tileProgress[challengeId][taskId] >= task.quantity:
                save.tileProgress[challengeId][taskId] -= task.quantity
                return True
        case "AND":
            tasks = challenge.tasks
            for taskId in tasks:
                task: EventTasks = EventTasks.query.filter(EventTasks.id == taskId).first()
                if save.tileProgress[challengeId][taskId] < task.quantity:
                    return False
                
            for taskId in tasks:
                task: EventTasks = EventTasks.query.filter(EventTasks.id == taskId).first()
                save.tileProgress[challengeId][taskId] -= task.quantity
            
            return True
        case "CUMULATIVE":
            logging.warning(f"Challenge {challengeId} is cumulative, but completion logic is not implemented")
            return False # TODO: Implement cumulative challenge logic

def create_region_challenge_notification(challenge: EventChallenges, event: Events, team: EventTeams, save: SaveData, submission: EventSubmission) -> NotificationResponse:
    return None

def create_tile_challenge_notification(challenge: SP3EventTileChallengeMapping, event: Events, team: EventTeams, save: SaveData, submission: EventSubmission) -> NotificationResponse:
    tile: SP3EventTiles = SP3EventTiles.query.filter(SP3EventTiles.id == save.currentTile).first()
    region: SP3Regions = SP3Regions.query.filter(SP3Regions.id == tile.region_id).first()
    if region is None or tile is None:
        logging.warning(f"Region or Tile not found for {challenge.region_id} or {save.currentTile}")
        return None

    save.coins += 10
    save.dice = [4] # TODO: Implement dice logic
    save.isTileCompleted = True

    fields = [
        NotificationField(name="Stars", value=save.stars, inline=True),
        NotificationField(name="Coins", value=save.coins, inline=True),
        NotificationField(name="Island", value=region.name, inline=True),
    ]

    return NotificationResponse(
        threadId=event.thread_id,
        title=f"{submission.rsn}: {submission.trigger} from {submission.source}",
        description=f"For completing a tile challenge, you have earned {10} coins and a {4} sided die!",
        color=0x992D22,
        author=NotificationAuthor(name=team.name, icon_url=team.image if team.image else None),
        fields=fields,
    )

def create_coin_challenge_notification(challenge: EventChallenges, event: Events, team: EventTeams, save: SaveData, submission: EventSubmission) -> NotificationResponse:
    return None

def progress_challenge(challengeMapping: SP3EventTileChallengeMapping, event: Events, team: EventTeams, save: SaveData, submission: EventSubmission) -> NotificationResponse:
    challenge = EventChallenges.query.filter(EventChallenges.id == challengeMapping.challenge_id).first()
    if challenge is None:
        logging.debug(f"Challenge not found for {challenge.challenge_id}")
        return None
    
    for taskId in challenge.tasks:
        task: EventTasks = EventTasks.query.filter(EventTasks.id == taskId).first()
        for triggerId in task.triggers:
            trigger: EventTriggers = EventTriggers.query.filter(EventTriggers.id == triggerId).first()
            source = trigger.source
            if source is None or source == "":
                source = submission.source

            if trigger.trigger.lower() != submission.trigger.lower() or source.lower() != submission.source.lower():
                return None
            
            challengeId = str(challenge.id)
            if challengeId not in save.tileProgress:
                save.tileProgress[challengeId] = {}
            if taskId not in save.tileProgress[challengeId]:
                save.tileProgress[challengeId][taskId] = 0
            save.tileProgress[challengeId][taskId] = save.tileProgress.get(challengeId, {}).get(taskId, 0) + submission.quantity

            if save.tileProgress[challengeId][taskId] >= task.quantity:
                if is_challenge_completed(challenge, task, save):
                    print(f"Challenge {challengeId} completed for {submission.rsn}")
                    match challengeMapping.type:
                        case "REGION":
                            return create_region_challenge_notification(challengeMapping, event, team, save, submission)
                        case "TILE":
                            return create_tile_challenge_notification(challengeMapping, event, team, save, submission)
                        case "COIN":
                            return create_tile_challenge_notification(challengeMapping, event, team, save, submission)

                return None

def progress_team(event: Events, team: EventTeams, save: SaveData, submission: EventSubmission) -> list[NotificationResponse]:
    notifications: list[NotificationResponse] = []
    for challenge in get_team_challenges(save):
            notif = progress_challenge(challenge, event, team, save, submission)
            if notif is not None:
                notifications.append(notif)
    return notifications

def progress_event(event: Events, submission: EventSubmission) -> None:
    return None

def is_team_accepting_submissions(save: SaveData) -> bool:
    return not save.isTileCompleted

def is_game_accepting_submissions(event: Events) -> bool:
    # TODO: Implement logic to see if the global game state needs us to track something
    return False # For now, we will assume the global state is never accepting submissions

def get_team(eventId: uuid.UUID, rsn: str) -> EventTeams:
    team = EventTeamMemberMappings.query.filter(EventTeamMemberMappings.event_id == eventId).filter(EventTeamMemberMappings.username.ilike(rsn)).first()
    if team is None:
        return None
    return EventTeams.query.filter(EventTeams.id == team.team_id).first()

def stability_party_handler(submission: EventSubmission) -> list[NotificationResponse]:
    now = datetime.now(timezone.utc)
    # For now we will assume there is only one event of this type running at a time
    event = Events.query.filter(Events.start_time <= now).filter(Events.end_time >= now).filter(Events.type == "STABILITY_PARTY").first()

    team = get_team(event.id, submission.rsn)
    if team is None:
        logging.debug(f"Team not found for {submission.rsn} in event {event.id}")
        return None

    if is_game_accepting_submissions(event):
        progress_event(event, submission)

    save = SaveData.from_dict(team.data)

    if not is_team_accepting_submissions(save):
        logging.error(f"Team {team.id} is not accepting submissions")
        return None

    response = progress_team(event, team, save, submission)
    # log out the save data for debugging
    # print(f"Save Data: {save.to_dict()}")
    
    save_team_data(team, save)

    return response
