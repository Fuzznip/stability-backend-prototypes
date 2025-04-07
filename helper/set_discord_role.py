import requests
import os
from dotenv import load_dotenv
load_dotenv()

def add_discord_role(user, role):
    """
    Adds the discord role for a user
    """
    if user is None or not user.is_active:
        return "Could not find User", 404
    
    user_id = user.discord_id
    token = os.getenv("DISCORD_BOT_API_TOKEN")

    url = os.getenv("DISCORD_BOT_API") + f"/roles/{user_id}/add"
    json = {
        "role": role,
        "token": token
    }
    requests.post(url, json=json)

def remove_discord_role(user, role):
    """
    Removes the discord role for a user
    """
    if user is None or not user.is_active:
        return "Could not find User", 404
    
    user_id = user.discord_id
    token = os.getenv("DISCORD_BOT_API_TOKEN")

    url = os.getenv("DISCORD_BOT_API") + f"/roles/{user_id}/remove"
    json = {
        "role": role,
        "token": token
    }
    requests.post(url, json=json)