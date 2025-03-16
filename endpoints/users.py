from app import app, db
from helper.helpers import UUIDEncoder
from flask import request
from models.models import Users
import json


@app.route("/user/<id>", methods=['GET'])
def get_user_profile(id):
    return json.dumps(Users.query.filter_by(discord_id=id).first().serialize(), cls=UUIDEncoder)


@app.route("/user", methods=['POST'])
def create_user():
    data = Users(**request.get_json())
    if data is None:
        return "No JSON received", 400
    if Users.query.filter_by(discord_id=data.discord_id).first() is not None:
        return "Id already exists", 400
    data.id = None
    db.session.add(data)
    db.session.commit()
    return json.dumps(data.serialize(), cls=UUIDEncoder)


@app.route("/user/<id>", methods=['PUT'])
def update_user_profile(id):
    data = Users(**request.get_json())
    if data is None:
        return "No JSON received", 400
    user = Users.query.filter_by(discord_id=id).first()
    user.runescape_name = data.runescape_name
    user.rank = data.rank
    user.progression_data = data.progression_data
    db.session.commit()
    return json.dumps(user.serialize(), cls=UUIDEncoder)