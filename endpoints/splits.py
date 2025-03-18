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
    db.session.add(data)
    db.session.commit()
    return json.dumps(data.serialize(), cls=ModelEncoder)


@app.route("/split/<id>", methods=['GET'])
def get_user_splits(id):
    data = []
    splits = Splits.query.filter_by(user_id=id).all()
    if not splits:
        if Users.query.filter_by(discord_id=id).first() is None:
            return "Could not find User", 404
    for row in splits:
        data.append(row.serialize())
    return data


@app.route("/split/total/<id>", methods=['GET'])
def get_user_total_splits(id):
    if Users.query.filter_by(discord_id=id).first() is None:
        return "Could not find User", 404
    data = 0
    splits = Splits.query.filter_by(user_id=id).all()
    for row in splits:
        data += row.split_amount
    return str(data)
