from app import app, db
from helper.helpers import UUIDEncoder
from flask import request
from models.models import Webhook, Users, Announcements
import json


@app.route("/bot/rank-update", methods=['POST'])
def bot_rank_promotion():
    data = Webhook(**request.get_json())
    if data is None:
        return "No JSON received", 400
    user = Users.query.filter_by(discord_id=data.discord_id).first()
    user.rank = data.rank
    db.session.commit()
    return json.dumps(user.serialize(), cls=UUIDEncoder)


@app.route("/bot/announcement", methods=['POST'])
def bot_create_announcement():
    data = Announcements(request.get_json())
    if data is None:
        return "No JSON received", 400
    db.session.add(data)
    db.session.commit()
    return "Message \"{0}\" Created".format(data.message), 200

