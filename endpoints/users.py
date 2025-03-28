from app import app, db
from helper.helpers import ModelEncoder
from flask import request
from models.models import Users, Splits
import json

@app.route("/users", methods=['GET'])
def get_users():
    data = []
    users = Users.query.all()
    for row in users:
        data.append(row.serialize())
    return data

@app.route("/users", methods=['POST'])
def create_user():
    data = Users(**request.get_json())
    if data is None:
        return "No JSON received", 400
    if Users.query.filter_by(discord_id=data.discord_id).first() is not None:
        return "Id already exists", 400
    data.id = None
    db.session.add(data)
    db.session.commit()
    return json.dumps(data.serialize(), cls=ModelEncoder)

@app.route("/users/<id>", methods=['GET'])
def get_user_profile(id):
    user = Users.query.filter_by(discord_id=id).first()
    if user is None:
        return "Could not find User", 404
    return json.dumps(user.serialize(), cls=ModelEncoder)

@app.route("/users/<id>", methods=['PUT'])
def update_user_profile(id):
    data = Users(**request.get_json())
    if data is None:
        return "No JSON received", 400
    user = Users.query.filter_by(discord_id=id).first()
    user.runescape_name = data.runescape_name
    user.rank = data.rank
    user.progression_data = data.progression_data
    db.session.commit()
    return json.dumps(user.serialize(), cls=ModelEncoder)

@app.route("/users/<id>", methods=['DELETE'])
def delete_user(id):
    user = Users.query.filter_by(discord_id=id).first()
    if user is None:
        return "Could not find User", 404
    db.session.delete(user)
    db.session.commit()
    return "User deleted", 200

@app.route("/users/<id>/splits", methods=['GET'])
def get_user_splits(id):
    data = []
    splits = Splits.query.filter_by(user_id=id).all()
    if not splits:
        if Users.query.filter_by(discord_id=id).first() is None:
            return "Could not find User", 404
    for row in splits:
        data.append(row.serialize())
    return data

@app.route("/users/<id>/splits/total/", methods=['GET'])
def get_user_total_splits(id):
    if Users.query.filter_by(discord_id=id).first() is None:
        return "Could not find User", 404
    data = 0
    splits = Splits.query.filter_by(user_id=id).all()
    for row in splits:
        data += row.split_contribution
    return str(data)
