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
    equipment: Equipment

    dice: list[int]
    modifier: int

    isTileCompleted: bool
    isRolling: bool

    buffs: list[str]
    debuffs: list[str]

    textChannelId: str
    voiceChannelId: str

    tileProgress: dict[str, dict[str, int]]

    def to_dict(self) -> dict:
        return {
            "previousTile": str(self.previousTile),
            "currentTile": str(self.currentTile),
            "stars": self.stars,
            "coins": self.coins,
            "islandId": str(self.islandId),
            "itemList": self.itemList,
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
        logging.error(f"Region or Tile not found for {challenge.region_id} or {save.currentTile}")
        return None

    save.coins += 10 # TODO: Implement coin logic
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
        description=f"For completing the tile: {tile.name}, you have earned {10} coins and a {4} sided die!",
        color=0x992D22,
        author=NotificationAuthor(name=f"{team.name}: {tile.name} ({region.name})", icon_url=team.image if team.image else None),
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

    if event is None:
        logging.debug(f"No active event found.")
        return None

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

# Roll Progression System

class RollState:
    """Represents the state of a roll progression"""
    ACTION_TYPES = {
        "CONTINUE": "continue",        # Continue roll to next tile
        "SHOP": "shop",                # Interact with shop
        "STAR": "star",                # Buy a star
        "DOCK": "dock",                # Charter to another island
        "CROSSROAD": "crossroad",      # Choose a path at a crossroad
        "COMPLETE": "complete"         # Roll is complete
    }
    
    def __init__(self, event_id, team_id, roll_total, current_tile_id=None):
        self.event_id = event_id
        self.team_id = team_id
        self.starting_tile_id = current_tile_id
        self.current_tile_id = current_tile_id
        self.roll_total = roll_total
        self.roll_remaining = roll_total
        self.dice_results = []
        self.modifier = 0
        self.path_taken = []
        self.action_required = None
        self.action_data = {}
    
    def to_dict(self):
        """Convert the roll state to a dictionary for response"""
        return {
            "event_id": str(self.event_id),
            "team_id": str(self.team_id),
            "starting_tile_id": str(self.starting_tile_id) if self.starting_tile_id else None,
            "current_tile_id": str(self.current_tile_id) if self.current_tile_id else None,
            "roll_total": self.roll_total,
            "roll_remaining": self.roll_remaining,
            "dice_results": self.dice_results,
            "modifier": self.modifier,
            "path_taken": [str(tile_id) for tile_id in self.path_taken],
            "action_required": self.action_required,
            "action_data": self.action_data
        }

def roll_dice_progression(event_id, team_id, data=None, action_type=None, action_choice=None):
    """
    Master function for handling dice roll progression.
    
    This function is used for both:
    1. Initiating a new dice roll 
    2. Continuing a roll in progress when making choices
    
    Parameters:
    - event_id: The ID of the event
    - team_id: The ID of the team
    - data: Optional JSON data from client (for initial roll or action choices)
    - action_type: Type of action when continuing a roll (shop, star, dock, crossroad)
    - action_choice: The specific choice made for an action
    
    Returns:
    - A tuple with (response_object, status_code)
    """
    try:
        logging.info(f"Roll progression started - event_id: {event_id}, team_id: {team_id}, action_type: {action_type}")
        logging.debug(f"Roll progression input data: {data}")
        
        # Check if event exists and is a SP3 event
        event = Events.query.filter_by(id=event_id, type="STABILITY_PARTY").first()
        if not event:
            logging.error(f"Event not found or not a SP3 event: {event_id}")
            return {"error": "Event not found or not a Stability Party event"}, 404
        
        # Check if team exists and belongs to this event
        team = EventTeams.query.filter_by(id=team_id, event_id=event_id).first()
        if not team:
            logging.error(f"Team not found for event: team_id={team_id}, event_id={event_id}")
            return {"error": "Team not found or does not belong to this event"}, 404
        
        # Load team data
        save = SaveData.from_dict(team.data)
        logging.debug(f"Current team state: currentTile={save.currentTile}, isRolling={save.isRolling}, isTileCompleted={save.isTileCompleted}")
        
        # Initialize response
        response = {}
        
        # Check if this is a new roll or continuing an existing roll
        if action_type is None:
            logging.info(f"Initiating new roll for team {team_id}")
            # This is a new roll request
            if not save.isTileCompleted:
                logging.error(f"Cannot roll - current tile not completed: team={team_id}, tile={save.currentTile}")
                return {"error": "Current tile must be completed before rolling"}, 400
            
            if save.isRolling:
                logging.error(f"Cannot roll - team is already rolling: team={team_id}")
                return {"error": "Team is already in the process of rolling"}, 400
            
            # Process dice roll
            roll_state = _initiate_new_roll(event_id, team_id, save, data)
            logging.info(f"New roll initiated: total={roll_state.roll_total}, dice={roll_state.dice_results}, modifier={roll_state.modifier}")
            
            # Handle first tile movement
            logging.debug(f"Processing first movement for team {team_id}")
            response = _process_next_move(event_id, team_id, save, roll_state)
            
            # Save the updated team data
            logging.debug(f"Saving updated team data after initial roll: team={team_id}, currentTile={save.currentTile}")
            save_team_data(team, save)
            
            return response, 200
        else:
            # Continuing an existing roll with an action
            logging.info(f"Continuing roll with action: {action_type} for team {team_id}")
            
            if not save.isRolling:
                logging.error(f"Cannot continue roll - no roll in progress: team={team_id}")
                return {"error": "No roll in progress"}, 400
            
            # Get current tile information
            current_tile = SP3EventTiles.query.filter_by(id=save.currentTile).first()
            if not current_tile:
                logging.error(f"Current tile not found: team={team_id}, tile_id={save.currentTile}")
                return {"error": "Current tile not found"}, 404
            
            # Process the action based on type
            logging.info(f"Processing action {action_type} at tile {current_tile.name} (ID: {current_tile.id})")
            
            if action_type == RollState.ACTION_TYPES["SHOP"]:
                logging.debug(f"Handling shop action for team {team_id}")
                response = _handle_shop_action(event_id, team_id, save, data)
            elif action_type == RollState.ACTION_TYPES["STAR"]:
                logging.debug(f"Handling star action for team {team_id}")
                response = _handle_star_action(event_id, team_id, save, data)
            elif action_type == RollState.ACTION_TYPES["DOCK"]:
                logging.debug(f"Handling dock action for team {team_id}")
                response = _handle_dock_action(event_id, team_id, save, data)
            elif action_type == RollState.ACTION_TYPES["CROSSROAD"]:
                logging.debug(f"Handling crossroad action for team {team_id}")
                response = _handle_crossroad_action(event_id, team_id, save, data)
            elif action_type == RollState.ACTION_TYPES["CONTINUE"]:
                logging.debug(f"Continuing roll progression for team {team_id}")
                # Create a roll state from the saved data
                roll_state = RollState(event_id, team_id, save.dice[0] if save.dice else 0)
                roll_state.roll_remaining = data.get("roll_remaining", 0) if data else 0
                roll_state.current_tile_id = save.currentTile
                logging.debug(f"Created roll state from saved data: remaining={roll_state.roll_remaining}, current_tile={roll_state.current_tile_id}")
                
                # Continue movement
                response = _process_next_move(event_id, team_id, save, roll_state)
            else:
                logging.error(f"Unknown action type received: {action_type}")
                return {"error": f"Unknown action type: {action_type}"}, 400
            
            # Save the updated team data
            logging.debug(f"Saving updated team data after action {action_type}: team={team_id}, currentTile={save.currentTile}")
            save_team_data(team, save)
            
            return response, 200
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in roll progression: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500

def _initiate_new_roll(event_id, team_id, save, data):
    """Handle the initial dice roll and set up the roll state"""
    logging.info(f"Initiating new roll for team {team_id}")
    
    # Default values
    dice_array = save.dice
    modifier = save.modifier

    # Generate random dice roll if not provided
    import random
    dice_results = []

    logging.debug(f"Dice array: {dice_array}, Modifier: {modifier}")
    for dice in dice_array:
        dice_roll = random.randint(1, dice)
        dice_results.append(dice_roll)
        logging.debug(f"Generated die roll: {dice_roll}")
    
    # Calculate total movement
    try:
        roll_total = sum(dice_results) + int(modifier)
        logging.debug(f"Calculated total movement: sum({dice_results})={sum(dice_results)} + modifier({modifier}) = {roll_total}")
    except (ValueError, TypeError):
        # Fallback if modifier is invalid
        roll_total = sum(dice_results)
        modifier = 0
        logging.warning(f"Invalid modifier value, falling back to sum of dice only: {roll_total}")
    
    # Create roll state
    roll_state = RollState(event_id, team_id, roll_total, save.currentTile)
    roll_state.dice_results = dice_results
    roll_state.modifier = modifier
    logging.debug(f"Created roll state: total={roll_total}, remaining={roll_state.roll_remaining}, current_tile={roll_state.current_tile_id}")
    
    # Update team state
    save.previousTile = save.currentTile
    save.isRolling = True
    save.isTileCompleted = False  # New tile needs to be completed
    logging.info(f"Updated team state: dice={save.dice}, modifier={save.modifier}, previousTile={save.previousTile}, isRolling={save.isRolling}")
    
    return roll_state

def _process_next_move(event_id, team_id, save, roll_state):
    """Process movement to the next tile in the roll sequence"""
    logging.info(f"Processing next move for team {team_id} - Remaining moves: {roll_state.roll_remaining}")
    
    # If no moves left, complete the roll
    if roll_state.roll_remaining <= 0:
        logging.debug(f"No moves remaining, completing roll for team {team_id}")
        return _complete_roll(event_id, team_id, save, roll_state)
    
    # Get current tile
    current_tile = SP3EventTiles.query.filter_by(id=save.currentTile).first()
    if not current_tile:
        logging.error(f"Current tile not found: {save.currentTile}")
        return {"error": "Current tile not found"}
    
    logging.debug(f"Current tile: {current_tile.name} (ID: {current_tile.id})")
    
    # Track this tile in the path
    roll_state.path_taken.append(save.currentTile)
    logging.debug(f"Updated path taken: {roll_state.path_taken}")
    
    # Get next possible tiles
    next_tiles = current_tile.data.get("nextTiles", [])
    logging.debug(f"Next tiles available: {next_tiles}")

    # Check for crossroads (multiple next tiles)
    if len(next_tiles) > 1:
        logging.info(f"Crossroad detected with {len(next_tiles)} options at tile {current_tile.id}")
        return _handle_crossroad(event_id, team_id, save, roll_state, next_tiles)
    
    # If there's only one path, move to that tile
    if len(next_tiles) == 1:
        next_tile_id = next_tiles[0]
        logging.info(f"Moving to next tile: {next_tile_id}")
        
        # Move to the next tile
        save.currentTile = next_tile_id
        roll_state.current_tile_id = save.currentTile
        roll_state.roll_remaining -= 1
        logging.debug(f"Updated roll state: remaining={roll_state.roll_remaining}, current_tile={roll_state.current_tile_id}")
        
        # Check for special tiles that need interaction
        return _check_for_special_tile(event_id, team_id, save, roll_state)
    else:
        logging.warning(f"No next tiles found for tile {current_tile.id}, completing roll")
        # No next tile - end of the board?
        return _complete_roll(event_id, team_id, save, roll_state)

def is_star_tile(tile_id):
    """Check if the tile is a star tile"""
    tile = SP3EventTiles.query.filter_by(id=tile_id).first()
    if tile:
        event = Events.query.filter_by(id=tile.event_id).first()
        if event:
            star_list = event.data.get("star_tiles", [])
            if tile_id in star_list:
                logging.debug(f"Tile {tile_id} is a star tile")
                return True
            else:
                logging.debug(f"Tile {tile_id} is not a star tile")
                return False
            
    return False

def is_dock_tile(tile_id):
    """Check if the tile is a dock tile"""
    tile = SP3EventTiles.query.filter_by(id=tile_id).first()
    if tile:
        isDock = tile.data.get("isDock", False)
        if isDock:
            logging.debug(f"Tile {tile_id} is a dock tile")
            return True
        else:
            logging.debug(f"Tile {tile_id} is not a dock tile")
            return False
            
    return False

def is_shop_tile(tile_id):
    """Check if the tile is a shop tile"""
    tile = SP3EventTiles.query.filter_by(id=tile_id).first()
    if tile:
        isShop = tile.data.get("isShop", False)
        if isShop:
            logging.debug(f"Tile {tile_id} is a shop tile")
            return True
        else:
            logging.debug(f"Tile {tile_id} is not a shop tile")
            return False
            
    return False

def _check_for_special_tile(event_id, team_id, save, roll_state):
    """Check if the current tile is a special tile that needs interaction"""
    logging.info(f"Checking for special tile interaction for team {team_id} at tile {save.currentTile}")
    
    current_tile = SP3EventTiles.query.filter_by(id=save.currentTile).first()
    if not current_tile:
        logging.error(f"Current tile not found: {save.currentTile}")
        return {"error": "Current tile not found"}
    
    logging.debug(f"Current tile details: name={current_tile.name}, id={current_tile.id}")
    
    # Get info about the tile
    tile_info = {
        "id": str(current_tile.id),
        "name": current_tile.name,
        "description": current_tile.description
    }
    
    # Check if we need to set island ID based on the tile
    if current_tile.region_id and current_tile.region_id != save.islandId:
        logging.info(f"Updating team island ID from {save.islandId} to {current_tile.region_id}")
        save.islandId = current_tile.region_id
    
    # Check if this is a special tile that requires an action
    if is_shop_tile(current_tile.id):
        logging.info(f"Special tile detected: SHOP - Preparing shop interaction")
        return _prepare_shop_interaction(event_id, team_id, save, roll_state, current_tile)
    elif is_star_tile(current_tile.id):
        logging.info(f"Special tile detected: STAR_SPOT - Preparing star interaction")
        return _prepare_star_interaction(event_id, team_id, save, roll_state, current_tile)
    elif is_dock_tile(current_tile.id):
        logging.info(f"Special tile detected: DOCK - Preparing dock interaction")
        return _prepare_dock_interaction(event_id, team_id, save, roll_state, current_tile)
    else:
        logging.info(f"Regular tile no special interaction required")
        
        # Regular tile, continue movement automatically if there are moves left
        if roll_state.roll_remaining > 0:
            logging.debug(f"Moves remaining: {roll_state.roll_remaining}, automatically continuing to next tile")
            
            # Add current tile to the response for client information
            roll_state.path_taken.append(save.currentTile)
            
            # Automatically continue to the next tile
            return _process_next_move(event_id, team_id, save, roll_state)
        else:
            logging.debug("No moves remaining, completing roll")
            # No more moves left, finalize the roll
            return _complete_roll(event_id, team_id, save, roll_state)
    
    return roll_state.to_dict()

def _handle_crossroad(event_id, team_id, save, roll_state, next_tiles):
    """Handle a crossroads where players must choose a path"""
    logging.info(f"Handling crossroad for team {team_id} with {len(next_tiles)} options")
    
    current_tile = SP3EventTiles.query.filter_by(id=save.currentTile).first()
    logging.debug(f"Current tile at crossroad: {current_tile.name} (ID: {current_tile.id})")
    
    # Prepare options for the player to choose
    path_options = []
    for tile_id in next_tiles:
        next_tile = SP3EventTiles.query.filter_by(id=tile_id).first()
        if next_tile:
            logging.debug(f"Adding path option: {next_tile.name} (ID: {next_tile.id})")
            path_options.append({
                "id": str(next_tile.id),
                "name": next_tile.name,
                "description": next_tile.description,
            })
        else:
            logging.warning(f"Next tile not found for ID {tile_id}")
    
    # Update roll state to require crossroad choice
    roll_state.action_required = RollState.ACTION_TYPES["CROSSROAD"]
    roll_state.action_data = {
        "message": "You've reached a crossroad! Choose which path to take:",
        "current_tile": {
            "id": str(current_tile.id),
            "name": current_tile.name,
            "description": current_tile.description
        },
        "options": path_options,
        "moves_remaining": roll_state.roll_remaining
    }
    logging.info(f"Crossroad prepared with {len(path_options)} options, waiting for player choice")
    
    return roll_state.to_dict()

def _handle_crossroad_action(event_id, team_id, save, data):
    """Process a choice made at a crossroad"""
    logging.info(f"Processing crossroad choice for team {team_id}")
    logging.debug(f"Choice data: {data}")
    
    if not data or "next_tile_id" not in data:
        logging.error("Missing required field: next_tile_id")
        return {"error": "Missing required field: next_tile_id"}
    
    next_tile_id = data["next_tile_id"]
    logging.debug(f"Selected next tile ID: {next_tile_id}")
    
    next_tile = SP3EventTiles.query.filter_by(id=next_tile_id).first()
    if not next_tile:
        logging.error(f"Selected tile not found: {next_tile_id}")
        return {"error": "Selected tile not found"}
    
    logging.info(f"Moving to selected tile: {next_tile.name} (ID: {next_tile_id})")
    
    # Update team position
    save.currentTile = next_tile_id
    
    # Create roll state with the remaining moves
    moves_remaining = data.get("moves_remaining", 0)
    logging.debug(f"Creating roll state with {moves_remaining} moves remaining")
    roll_state = RollState(event_id, team_id, 0)
    roll_state.current_tile_id = save.currentTile
    roll_state.roll_remaining = moves_remaining - 1
    
    # Process the new tile
    logging.debug(f"Checking for special tile interactions after crossroad choice")
    return _check_for_special_tile(event_id, team_id, save, roll_state)

def _prepare_shop_interaction(event_id, team_id, save, roll_state, current_tile):
    """Prepare shop interaction data"""
    logging.info(f"Preparing shop interaction for team {team_id} at tile {current_tile.id}")
    
    # Import item system here to avoid circular imports
    from event_handlers.stability_party.item_system import generate_shop_inventory
    
    # Get shop tier from tile data (default to 1)
    shop_tier = current_tile.data.get("shopTier", 1)
    item_count = current_tile.data.get("itemCount", 3)
    logging.debug(f"Shop tier: {shop_tier}, Item count: {item_count}")
    
    # Generate random items for the shop
    available_items = generate_shop_inventory(event_id, shop_tier, item_count)
    logging.debug(f"Generated {len(available_items)} shop items")
    
    # Set action to shop interaction
    roll_state.action_required = RollState.ACTION_TYPES["SHOP"]
    roll_state.action_data = {
        "message": f"You've landed on {current_tile.name}! Would you like to buy something?",
        "current_tile": {
            "id": str(current_tile.id),
            "name": current_tile.name,
            "description": current_tile.description,
        },
        "available_items": available_items,
        "coins": save.coins,
        "moves_remaining": roll_state.roll_remaining
    }
    logging.info(f"Shop interaction prepared for team {team_id} with {len(available_items)} items. Team has {save.coins} coins.")
    
    return roll_state.to_dict()

def _handle_shop_action(event_id, team_id, save, data):
    """Process a shop purchase"""
    logging.info(f"Processing shop action for team {team_id}")
    logging.debug(f"Shop action data: {data}")
    
    # Import item system here to avoid circular imports
    from event_handlers.stability_party.item_system import add_item_to_inventory
    
    # Check if player is skipping the shop
    if data and data.get("skip", False):
        logging.info(f"Team {team_id} is skipping the shop")
        # Create roll state with the remaining moves
        moves_remaining = data.get("moves_remaining", 0)
        roll_state = RollState(event_id, team_id, 0)
        roll_state.current_tile_id = save.currentTile
        roll_state.roll_remaining = moves_remaining
        logging.debug(f"Created roll state with {moves_remaining} moves remaining")
        
        # Continue the roll
        if roll_state.roll_remaining > 0:
            logging.debug(f"Continuing roll with {roll_state.roll_remaining} moves remaining")
            return _process_next_move(event_id, team_id, save, roll_state)
        else:
            logging.debug("No moves remaining, completing roll")
            return _complete_roll(event_id, team_id, save, roll_state)
    
    # Validate required fields for purchase
    if not data or "item_id" not in data:
        logging.error("Missing required field: item_id")
        return {"error": "Missing required field: item_id"}, 400
    
    item_id = data["item_id"]
    item_price = data.get("price", 10)
    item_name = data.get("name", f"Item {item_id}")
    logging.info(f"Team {team_id} is attempting to purchase item {item_name} (ID: {item_id}) for {item_price} coins")
    
    # Check if team has enough coins
    if save.coins < item_price:
        logging.warning(f"Team {team_id} doesn't have enough coins: required={item_price}, available={save.coins}")
        return {"error": f"Not enough coins. Required: {item_price}, Available: {save.coins}"}
    
    # Add item to inventory and deduct coins
    add_success = add_item_to_inventory(str(event_id), str(team_id), item_id)
    
    if not add_success:
        logging.error(f"Failed to add item {item_id} to inventory")
        return {"error": "Failed to add item to inventory"}
    
    # Deduct coins (add_item_to_inventory doesn't handle this)
    save.coins -= item_price
    logging.info(f"Item {item_name} purchased successfully. Team {team_id} now has {save.coins} coins")
    
    # Create response
    response = {
        "message": "Item purchased successfully",
        "item_id": item_id,
        "remaining_coins": save.coins
    }
    
    # Check if there are remaining moves
    moves_remaining = data.get("moves_remaining", 0)
    roll_state = RollState(event_id, team_id, 0)
    roll_state.current_tile_id = save.currentTile
    roll_state.roll_remaining = moves_remaining
    logging.debug(f"Created roll state with {moves_remaining} moves remaining after purchase")
    
    # Continue the roll or complete it
    if roll_state.roll_remaining > 0:
        logging.debug(f"Continuing roll with {roll_state.roll_remaining} moves remaining")
        response.update(_process_next_move(event_id, team_id, save, roll_state))
    else:
        logging.debug("No moves remaining, completing roll")
        response.update(_complete_roll(event_id, team_id, save, roll_state))
    
    return response

def _prepare_star_interaction(event_id, team_id, save, roll_state, current_tile):
    """Prepare star purchase interaction"""
    logging.info(f"Preparing star interaction for team {team_id} at tile {current_tile.id}")
    
    # Default star price
    star_price = 20
    logging.debug(f"Star price set to {star_price} coins")
    
    # Set action to star purchase
    roll_state.action_required = RollState.ACTION_TYPES["STAR"]
    roll_state.action_data = {
        "message": f"You've landed on {current_tile.name}! Would you like to buy a star for {star_price} coins?",
        "current_tile": {
            "id": str(current_tile.id),
            "name": current_tile.name,
            "description": current_tile.description,
        },
        "star_price": star_price,
        "coins": save.coins,
        "current_stars": save.stars,
        "moves_remaining": roll_state.roll_remaining
    }
    logging.info(f"Star purchase interaction prepared for team {team_id}. Team has {save.coins} coins and {save.stars} stars.")
    
    return roll_state.to_dict()

def _handle_star_action(event_id, team_id, save, data):
    """Process a star purchase"""
    logging.info(f"Processing star purchase action for team {team_id}")
    logging.debug(f"Star purchase data: {data}")
    
    # Check if player is skipping the star purchase
    if data and data.get("skip", False):
        logging.info(f"Team {team_id} is skipping star purchase")
        # Create roll state with the remaining moves
        moves_remaining = data.get("moves_remaining", 0)
        roll_state = RollState(event_id, team_id, 0)
        roll_state.current_tile_id = save.currentTile
        roll_state.roll_remaining = moves_remaining
        logging.debug(f"Created roll state with {moves_remaining} moves remaining")
        
        # Continue the roll
        if roll_state.roll_remaining > 0:
            logging.debug(f"Continuing roll with {roll_state.roll_remaining} moves remaining")
            return _process_next_move(event_id, team_id, save, roll_state)
        else:
            logging.debug("No moves remaining, completing roll")
            return _complete_roll(event_id, team_id, save, roll_state)
    
    # Get star price (default to 20 coins)
    star_price = data.get("star_price", 20) if data else 20
    logging.debug(f"Star price: {star_price} coins")
    
    # Check if team has enough coins
    if save.coins < star_price:
        logging.warning(f"Team {team_id} doesn't have enough coins: required={star_price}, available={save.coins}")
        return {"error": f"Not enough coins. Required: {star_price}, Available: {save.coins}"}
    
    # Add star and deduct coins
    save.stars += 1
    save.coins -= star_price
    logging.info(f"Star purchased successfully. Team {team_id} now has {save.stars} stars and {save.coins} coins")
    
    # Create response
    response = {
        "message": "Star purchased successfully",
        "stars": save.stars,
        "remaining_coins": save.coins
    }
    
    # Check if there are remaining moves
    moves_remaining = data.get("moves_remaining", 0) if data else 0
    roll_state = RollState(event_id, team_id, 0)
    roll_state.current_tile_id = save.currentTile
    roll_state.roll_remaining = moves_remaining
    logging.debug(f"Created roll state with {moves_remaining} moves remaining after star purchase")
    
    # Continue the roll or complete it
    if roll_state.roll_remaining > 0:
        logging.debug(f"Continuing roll with {roll_state.roll_remaining} moves remaining")
        response.update(_process_next_move(event_id, team_id, save, roll_state))
    else:
        logging.debug("No moves remaining, completing roll")
        response.update(_complete_roll(event_id, team_id, save, roll_state))
    
    return response

def _prepare_dock_interaction(event_id, team_id, save, roll_state, current_tile):
    """Prepare dock/charter ship interaction"""
    logging.info(f"Preparing dock interaction for team {team_id} at tile {current_tile.id}")
    
    # Get available destinations
    regions = SP3Regions.query.filter_by(event_id=event_id).all()
    destinations = []
    
    for region in regions:
        if region.id != save.islandId:  # Don't include current island
            logging.debug(f"Adding destination option: {region.name} (ID: {region.id})")
            destinations.append({
                "id": str(region.id),
                "name": region.name,
                "description": region.description
            })
    
    # Default charter price
    charter_price = 10
    logging.debug(f"Charter price set to {charter_price} coins")
    
    # Set action to dock/charter
    roll_state.action_required = RollState.ACTION_TYPES["DOCK"]
    roll_state.action_data = {
        "message": f"You've landed on {current_tile.name}! Would you like to charter a ship to another island?",
        "current_tile": {
            "id": str(current_tile.id),
            "name": current_tile.name,
            "description": current_tile.description,
        },
        "charter_price": charter_price,
        "destinations": destinations,
        "coins": save.coins,
        "moves_remaining": roll_state.roll_remaining
    }
    
    logging.info(f"Dock interaction prepared for team {team_id} with {len(destinations)} destinations. Team has {save.coins} coins.")
    return roll_state.to_dict()

def _handle_dock_action(event_id, team_id, save, data):
    """Process a charter ship action"""
    logging.info(f"Processing dock/charter action for team {team_id}")
    logging.debug(f"Charter action data: {data}")
    
    # Check if player is skipping the charter
    if data and data.get("skip", False):
        logging.info(f"Team {team_id} is skipping charter")
        # Create roll state with the remaining moves
        moves_remaining = data.get("moves_remaining", 0)
        roll_state = RollState(event_id, team_id, 0)
        roll_state.current_tile_id = save.currentTile
        roll_state.roll_remaining = moves_remaining
        logging.debug(f"Created roll state with {moves_remaining} moves remaining")
        
        # Continue the roll
        if roll_state.roll_remaining > 0:
            logging.debug(f"Continuing roll with {roll_state.roll_remaining} moves remaining")
            return _process_next_move(event_id, team_id, save, roll_state)
        else:
            logging.debug("No moves remaining, completing roll")
            return _complete_roll(event_id, team_id, save, roll_state)
    
    # Validate required fields
    if not data or "destination_island_id" not in data:
        logging.error("Missing required field: destination_island_id")
        return {"error": "Missing required field: destination_island_id"}
    
    destination_island_id = data["destination_island_id"]
    logging.debug(f"Destination island ID: {destination_island_id}")
    
    # Check if destination island exists
    destination_island = SP3Regions.query.filter_by(
        event_id=event_id, 
        id=destination_island_id
    ).first()
    
    if not destination_island:
        logging.error(f"Destination island not found: {destination_island_id}")
        return {"error": "Destination island not found"}
    
    logging.debug(f"Destination island found: {destination_island.name}")
    
    # Get charter price (default to 10 coins)
    charter_price = data.get("charter_price", 10)
    logging.debug(f"Charter price: {charter_price} coins")
    
    # Check if team has enough coins
    if save.coins < charter_price:
        logging.warning(f"Team {team_id} doesn't have enough coins: required={charter_price}, available={save.coins}")
        return {"error": f"Not enough coins. Required: {charter_price}, Available: {save.coins}"}
    
    # Find the starting tile of the destination island
    destination_tile = SP3EventTiles.query.filter_by(
        event_id=event_id, 
        island_id=destination_island_id,
        is_island_start=True
    ).first()
    
    if not destination_tile:
        logging.error(f"Destination island starting tile not found for island {destination_island_id}")
        return {"error": "Destination island starting tile not found"}
    
    logging.debug(f"Destination starting tile found: {destination_tile.name} (ID: {destination_tile.id})")
    
    # Update team location and deduct coins
    save.previousTile = save.currentTile
    save.currentTile = destination_tile.id
    save.islandId = destination_island_id
    save.coins -= charter_price
    logging.info(f"Ship chartered successfully. Team {team_id} moved to island {destination_island.name}, tile {destination_tile.name}")
    logging.debug(f"Team now has {save.coins} coins remaining")
    
    # When chartering, we end the roll (use up all remaining moves)
    response = {
        "message": "Ship chartered successfully",
        "previous_tile": str(save.previousTile),
        "destination_island": {
            "id": str(destination_island_id),
            "name": destination_island.name
        },
        "destination_tile": {
            "id": str(destination_tile.id),
            "name": destination_tile.name,
            "description": destination_tile.description
        },
        "remaining_coins": save.coins
    }
    
    # Complete the roll since chartering ends the movement
    logging.debug(f"Completing roll after chartering ship")
    roll_state = RollState(event_id, team_id, 0)
    roll_state.current_tile_id = save.currentTile
    roll_state.roll_remaining = 0
    
    complete_response = _complete_roll(event_id, team_id, save, roll_state)
    response.update(complete_response)
    
    return response

def _complete_roll(event_id, team_id, save, roll_state):
    """Complete the roll and finalize the state"""
    logging.info(f"Completing roll for team {team_id}")
    
    # Get final tile information 
    current_tile = SP3EventTiles.query.filter_by(id=save.currentTile).first()
    
    if current_tile:
        logging.debug(f"Final tile: {current_tile.name} (ID: {current_tile.id})")
        tile_info = {
            "id": str(current_tile.id),
            "name": current_tile.name,
            "description": current_tile.description
        }
    else:
        logging.warning(f"Final tile not found: {save.currentTile}")
        tile_info = {"id": str(save.currentTile), "name": "Unknown Tile"}
    
    # Set final state
    save.isRolling = False
    logging.info(f"Roll completed for team {team_id}. Final tile: {tile_info['name']} (ID: {tile_info['id']})")
    
    # We don't set isTileCompleted to True here because the player still needs to complete 
    # the challenge on this tile before being allowed to roll again
    
    # Create response
    roll_state.action_required = RollState.ACTION_TYPES["COMPLETE"]
    roll_state.action_data = {
        "message": "Roll completed. You've reached your destination!",
        "current_tile": tile_info,
        "dice_results": roll_state.dice_results,
        "modifier": roll_state.modifier,
        "total_movement": roll_state.roll_total,
        "path_taken": roll_state.path_taken
    }
    
    return roll_state.to_dict()
