from app import app, db
from helper.helpers import ModelEncoder
from flask import request
from models.models import Splits, Users
import json


@app.route("/split", methods=['POST'])
def create_split():
    data = Splits(**request.get_json())
    if data is None:
        return "No JSON received", 400
    user = Users.query.filter_by(discord_id=data.user_id).first()
    if user is None:
        return "Could not find User", 404
    data.id = None
    data.split_contribution = (data.item_price / data.group_size) * (data.group_size - 1)
    db.session.add(data)
    db.session.commit()
    return json.dumps(data.serialize(), cls=ModelEncoder)
