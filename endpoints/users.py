from app import app, db
from helper.helpers import ModelEncoder
from flask import request
from models.models import Users, Splits, ClanPointsLog
from models.models import ClanApplications, RankApplications, TierApplications, DiaryApplications, TimeSplitApplications
import json
from datetime import datetime

@app.route("/users", methods=['GET'])
def get_users():
    users = Users.query.all()
    data = []
    for row in users:
        data.append(row.serialize())
    return json.dumps(data, cls=ModelEncoder)

@app.route("/users", methods=['POST'])
def create_user():
    data = Users(**request.get_json())
    if data is None:
        return "No JSON received", 400
    user = Users.query.filter_by(discord_id=data.discord_id).first()
    if user is not None and user.is_active:
        return "Id already exists", 400
    
    if user is not None and not user.is_active:
        user.runescape_name = data.runescape_name
        user.previous_names = data.previous_names
        user.is_member = data.is_member if data.is_member is not None else False
        user.rank = data.rank
        user.rank_points = data.rank_points
        user.progression_data = data.progression_data
        user.achievements = data.achievements
        user.join_date = data.join_date
        user.timestamp = datetime.now()
        user.is_active = True
        user.diary_points = data.diary_points
        user.event_points = data.event_points
        user.time_points = data.time_points
    else:
        db.session.add(data)
    db.session.commit()
    return json.dumps(data.serialize(), cls=ModelEncoder)

@app.route("/users/<id>", methods=['GET'])
def get_user_profile(id):
    user = Users.query.filter_by(discord_id=id).first()
    if user is None:
        user = Users.query.filter(Users.runescape_name.ilike(id)).first()
        if user is None:
            return "Could not find User", 404
    
    if not user.is_active:
        return "Could not find User", 404
    
    return json.dumps(user.serialize(), cls=ModelEncoder)

@app.route("/users/<id>", methods=['PUT'])
def update_user_profile(id):
    data = Users(**request.get_json())
    if data is None:
        return "No JSON received", 400
    user = Users.query.filter_by(discord_id=id).first()
    if user is None or not user.is_active:
        return "Could not find User", 404
    user.runescape_name = data.runescape_name
    user.rank = data.rank
    user.progression_data = data.progression_data
    db.session.commit()
    return json.dumps(user.serialize(), cls=ModelEncoder)

@app.route("/users/<id>", methods=['DELETE'])
def delete_user(id):
    user = Users.query.filter_by(discord_id=id).first()
    if user is None or not user.is_active:
        return "Could not find User", 404
    
    # Don't actually delete the user, just set them to inactive
    user.is_active = False

    # Find all pending applications for this user and delete them
    applications = ClanApplications.query.filter_by(user_id=id).all()
    for application in applications:
        db.session.delete(application)

    applications = RankApplications.query.filter_by(user_id=id).all()
    for application in applications:
        db.session.delete(application)

    applications = TierApplications.query.filter_by(user_id=id).all()
    for application in applications:
        db.session.delete(application)

    applications = DiaryApplications.query.filter_by(user_id=id).all()
    for application in applications:
        db.session.delete(application)

    applications = TimeSplitApplications.query.filter_by(user_id=id).all()
    for application in applications:
        db.session.delete(application)

    db.session.commit()
    return json.dumps("User deleted successfully", cls=ModelEncoder), 200

@app.route("/users/<id>/rename", methods=['PUT'])
def rename_user(id):
    data = Users(**request.get_json())
    if data is None:
        return "No JSON received", 400
    # Ensure the given name is not taken by another user
    existing_user = Users.query.filter_by(runescape_name=data.runescape_name).first()
    if existing_user and existing_user.discord_id != id:
        return "Runescape name already taken", 400
    user = Users.query.filter_by(discord_id=id).first()
    if user is None or not user.is_active:
        return "Could not find User", 404

    # Check if the name is in use by another user
    existing_user = Users.query.filter_by(runescape_name=data.runescape_name).first()
    if existing_user is not None and existing_user.discord_id != id:
        return "Name is already in use", 400

    if not user.previous_names:
        user.previous_names = []
    else:
        # Remove blank entries from previous names
        user.previous_names = [name for name in user.previous_names if name]

    user.previous_names.append(user.runescape_name)
    user.previous_names = list(set(user.previous_names))  # Remove duplicates
    user.runescape_name = data.runescape_name
    
    # Remove new name from previous names if it exists
    if user.runescape_name in user.previous_names:
        user.previous_names.remove(user.runescape_name)

    db.session.commit()
    return json.dumps(user.serialize(), cls=ModelEncoder)

@app.route("/users/<id>/splits", methods=['GET'])
def get_user_splits(id):
    user = Users.query.filter_by(discord_id=id).first()
    if user is None or not user.is_active:
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
    user = Users.query.filter_by(discord_id=id).first()
    if user is None or not user.is_active:
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

@app.route("/users/<id>/diary/applications", methods=['GET'])
def get_user_diary_applications(id):
    user = Users.query.filter_by(discord_id=id).first()
    if user is None or not user.is_active:
        return "Could not find User", 404
    
    # Separate Pending and Accepted/Rejected applications
    pending_applications = DiaryApplications.query.filter_by(user_id=id, status="Pending").order_by(DiaryApplications.timestamp.desc()).all()
    other_applications = DiaryApplications.query.filter_by(user_id=id).filter(DiaryApplications.status != "Pending").order_by(DiaryApplications.verdict_timestamp.desc()).all()
    
    # Combine the results
    applications = pending_applications + other_applications
    
    data = []
    for row in applications:
        data.append(row.serialize())
    return json.dumps(data, cls=ModelEncoder)

@app.route("/users/<id>/pointlog", methods=['GET'])
def get_user_point_log(id):
    data = []
    rows = ClanPointsLog.query.filter_by(user_id=id).order_by(ClanPointsLog.timestamp.desc()).all()
    for row in rows:
        data.append(row.serialize())
    return data
