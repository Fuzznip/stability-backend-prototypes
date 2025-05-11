from app import app, db
from flask import request, jsonify
import logging
import os
import requests
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

load_dotenv()

@app.route("/channels/create-text", methods=['POST'])
def create_text_channel():
    """
    Create a new text channel in the Discord server
    
    Request body:
    {
        "category_name": str,     # Name of the category to place the channel under
        "channel_name": str,      # Name of the channel to create
        "view_roles": list[str],  # Roles that can view the channel
        "access_roles": list[str], # Roles that can send messages in the channel
        "token": str              # Discord bot API token
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["category_name", "channel_name", "token"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Build API URL
        url = os.getenv("DISCORD_BOT_API") + "/channels/create-text"
        
        # Prepare request payload
        json_data = {
            "category_name": data["category_name"],
            "channel_name": data["channel_name"],
            "view_roles": data.get("view_roles", []),
            "access_roles": data.get("access_roles", []),
            "token": data["token"]
        }
        
        # Make API request
        response = requests.post(url, json=json_data)
        response.raise_for_status()
        
        channel_data = response.json()
        
        return jsonify({
            "message": "Text channel created successfully",
            "channel_id": channel_data.get("id")
        }), 201
    except requests.exceptions.HTTPError as e:
        logging.error(f"Discord API error: {str(e)}")
        return jsonify({"error": f"Discord API error: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error creating text channel: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/channels/create-voice", methods=['POST'])
def create_voice_channel():
    """
    Create a new voice channel in the Discord server
    
    Request body:
    {
        "category_name": str,     # Name of the category to place the channel under
        "channel_name": str,      # Name of the channel to create
        "view_roles": list[str],  # Roles that can view the channel
        "access_roles": list[str], # Roles that can connect to the channel
        "token": str              # Discord bot API token
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["category_name", "channel_name", "token"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Build API URL
        url = os.getenv("DISCORD_BOT_API") + "/channels/create-voice"
        
        # Prepare request payload
        json_data = {
            "category_name": data["category_name"],
            "channel_name": data["channel_name"],
            "view_roles": data.get("view_roles", []),
            "access_roles": data.get("access_roles", []),
            "token": data["token"]
        }
        
        # Make API request
        response = requests.post(url, json=json_data)
        response.raise_for_status()
        
        channel_data = response.json()
        
        return jsonify({
            "message": "Voice channel created successfully",
            "channel_id": channel_data.get("id")
        }), 201
    except requests.exceptions.HTTPError as e:
        logging.error(f"Discord API error: {str(e)}")
        return jsonify({"error": f"Discord API error: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error creating voice channel: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/roles/create", methods=['POST'])
def create_role():
    """
    Create a new role in the Discord server
    
    Request body:
    {
        "role_name": str,         # Name of the role to create
        "color": Optional[str],   # Hex color code, e.g., "FF0000" for red
        "hoist": Optional[bool],  # Whether the role should be displayed separately
        "mentionable": Optional[bool], # Whether the role can be mentioned
        "permissions": Optional[int], # Permission integer
        "token": str              # Discord bot API token
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if "role_name" not in data or "token" not in data:
            return jsonify({"error": "Missing required fields: role_name and token are required"}), 400
        
        # Build API URL
        url = os.getenv("DISCORD_BOT_API") + "/roles/create"
        
        # Prepare request payload
        json_data = {
            "role_name": data["role_name"],
            "token": data["token"]
        }
        
        # Add optional fields
        optional_fields = ["color", "hoist", "mentionable", "permissions"]
        for field in optional_fields:
            if field in data:
                json_data[field] = data[field]
        
        # Make API request
        response = requests.post(url, json=json_data)
        response.raise_for_status()
        
        role_data = response.json()
        
        return jsonify({
            "message": "Role created successfully",
            "role_id": role_data.get("id")
        }), 201
    except requests.exceptions.HTTPError as e:
        logging.error(f"Discord API error: {str(e)}")
        return jsonify({"error": f"Discord API error: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error creating role: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/roles/delete", methods=['DELETE'])
def delete_role():
    """
    Delete a role from the Discord server
    
    Request body:
    {
        "role_name": str,  # Name of the role to delete
        "token": str       # Discord bot API token
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if "role_name" not in data or "token" not in data:
            return jsonify({"error": "Missing required fields: role_name and token are required"}), 400
        
        # Build API URL
        url = os.getenv("DISCORD_BOT_API") + "/roles/delete"
        
        # Prepare request payload
        json_data = {
            "role_name": data["role_name"],
            "token": data["token"]
        }
        
        # Make API request
        response = requests.delete(url, json=json_data)
        response.raise_for_status()
        
        return jsonify({
            "message": "Role deleted successfully"
        }), 200
    except requests.exceptions.HTTPError as e:
        logging.error(f"Discord API error: {str(e)}")
        return jsonify({"error": f"Discord API error: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error deleting role: {str(e)}")
        return jsonify({"error": str(e)}), 500