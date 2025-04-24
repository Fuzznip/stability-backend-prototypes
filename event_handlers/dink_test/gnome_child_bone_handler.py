from event_handlers.event_handler import EventSubmission, NotificationResponse, NotificationAuthor
from models.models import Events
import random

description_phrases = [
    "Guys, I think dink is working.",
    "I think that enemy got the point!",
    "Goodbye, my sweet child.",
    "Plugin check: ✅ Gnome check: ❌",
    "Testing successful. Please consider therapy.",
    "Plugin functioning. Gnome child voted off the island.",
    "Plugin confirmed. Gnome child… not so much.",
    "Gnome child has perished. Plugin operational. Morality… questionable.",
    "RIP Gnome Child. Cause of death: Science.",
    "Excellent, the plugin works. And you've failed the Turing test."
]

def gnome_child_bone_handler(data: EventSubmission) -> NotificationResponse:
    # Grab the 'Dink Testing' event
    event = Events.query.filter(Events.name=='Dink Testing').first()

    # Example logic for handling the event
    if data.trigger.lower() == "bones" and data.source.lower() == "gnome child":
        return NotificationResponse(
            threadId=event.thread_id,
            title=f"The Child has been Slain.",
            color=0xFF5733,  # Example color in hex format
            thumbnailImage="https://i.imgur.com/3UzSw0Q.png",
            author=NotificationAuthor(name=f"{data.rsn}"),
            description=random.choice(description_phrases)
        )
    return None
