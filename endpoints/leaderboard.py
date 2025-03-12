from app import app, db
from helper.helpers import UUIDEncoder
from flask import request
from models.models import Leaderboard
import json


@app.route("/leaderboard", methods=['GET'])
def get_leaderboard():
    data = []
    rows = Leaderboard.query.all()
    for row in rows:
        data.append(row.serialize())
    return data

# TODO: currently just updates single row of table based on passed in input, Should be pulling data from runelite
@app.route("/leaderboard/update", methods=['POST'])
def update_leaderboard_entry():
    data = Leaderboard(request.get_json())
    if data is None:
        return "No JSON received", 400
    leaderboard = Leaderboard.query.filter_by(user_id=data.user_id).first()
    leaderboard.stat_category = data.stat_category
    leaderboard.stat_value = data.stat_value
    leaderboard.timestamp = data.timestamp
    db.session.commit()
    return json.dumps(leaderboard.serialize(), cls=UUIDEncoder)

