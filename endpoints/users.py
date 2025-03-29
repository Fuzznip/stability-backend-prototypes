from app import app, db
from helper.helpers import ModelEncoder
from flask import request
from models.models import Users, Splits
import json
from datetime import datetime

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

@app.route("/users/<id>/splits", methods=['GET'])
def get_user_splits(id):
    if Users.query.filter_by(discord_id=id).first() is None:
        return "Could not find User", 404
    
    begin_date = request.args.get('begin_date')
    end_date = request.args.get('end_date')
    splits_query = Splits.query.filter_by(user_id=id)

    if begin_date:
        try:
            begin_date = datetime.strptime(begin_date, "%Y-%m-%d")
            splits_query = splits_query.filter(Splits.timestamp >= begin_date)
        except ValueError:
            return "Invalid begin_date format. Use YYYY-MM-DD.", 400
        
    if end_date:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            splits_query = splits_query.filter(Splits.timestamp <= end_date)
        except ValueError:
            return "Invalid end_date format. Use YYYY-MM-DD.", 400

    data = []
    splits = splits_query.all()
    for row in splits:
        data.append(row.serialize())
    return json.dumps(data, cls=ModelEncoder)

@app.route("/users/<id>/splits/total", methods=['GET'])
def get_user_total_splits(id):
    if Users.query.filter_by(discord_id=id).first() is None:
        return "Could not find User", 404
    
    begin_date = request.args.get('begin_date')
    end_date = request.args.get('end_date')
    splits_query = Splits.query.filter_by(user_id=id)

    if begin_date:
        try:
            begin_date = datetime.strptime(begin_date, "%Y-%m-%d")
            splits_query = splits_query.filter(Splits.timestamp >= begin_date)
        except ValueError:
            return "Invalid begin_date format. Use YYYY-MM-DD.", 400
        
    if end_date:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            splits_query = splits_query.filter(Splits.timestamp <= end_date)
        except ValueError:
            return "Invalid end_date format. Use YYYY-MM-DD.", 400
    data = 0
    splits = splits_query.all()
    for row in splits:
        data += row.split_contribution
    return json.dumps(data, cls=ModelEncoder)
