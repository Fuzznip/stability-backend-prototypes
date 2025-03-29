from app import app, db
from helper.helpers import ModelEncoder
from flask import request, jsonify
from models.models import Splits, Users
import json
from datetime import datetime

@app.route("/splits", methods=['POST'])
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

@app.route("/splits", methods=['GET'])
def get_splits():
    begin_date = request.args.get('begin_date')
    end_date = request.args.get('end_date')
    splits_query = Splits.query

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

    splits = splits_query.all()
    return jsonify([split.serialize() for split in splits])

