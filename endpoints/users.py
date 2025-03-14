from app import app, db
from helper.helpers import UUIDEncoder
from flask import request
from models.models import Users
import json


@app.route("/user/<id>", methods=['GET'])
def get_user_profile(id):
    Users.query.first()

    return json.dumps(db.session.query(Users, Users.discord_id, id).serialize(), cls=UUIDEncoder)

@app.route("/user/<id>", methods=['PUT'])
def update_user_profile(id):
    data = Users(request.get_json())
    if data is None:
        return "No JSON received", 400
    user = Users.query.filter_by(discord_id=id).first()
    user.runescape_name = data.runescape_name
    user.rank = data.rank
    user.progression_data = data.progression_data
    db.session.commit()
    return json.dumps(user.serialize(), cls=UUIDEncoder)

