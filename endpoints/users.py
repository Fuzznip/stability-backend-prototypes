from app import app, db
from helper.helpers import ModelEncoder
from helper.time_utils import parse_time_to_seconds
from flask import request
from models.models import Users, Splits, DiaryTasks, DiaryCompletionLog
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
    
    if not user.is_active:
        user.runescape_name = data.runescape_name
        user.previous_names = data.previous_names
        user.is_member = data.is_member
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

@app.route("/users/<id>/diary/apply", methods=['POST'])
def apply_for_diary(id):
    data = DiaryApplications(**request.get_json())
    if data is None:
        return "No JSON received", 400
    user = Users.query.filter_by(discord_id=id).first()
    if user is None or not user.is_active:
        return "Could not find User", 404
    diary = DiaryTasks.query.filter_by(diary_shorthand=data.diary_shorthand).all()
    if diary is None or len(diary) == 0:
        return "Could not find Diary", 404
    
    data.user_id = user.discord_id
    data.runescape_name = user.runescape_name

    if diary[0].scale is not None:
        try:
            if len(data.party) != int(diary[0].scale):
                return "Party size does not match diary group scale", 400
        except TypeError:
            return "Party was not provided", 400
    
    if diary[0].diary_time is not None:
        # Find the fastest diary time that the application beats
        fastest_time = None
        succeeded_task = None
        
        # Parse application time
        data_time_seconds = parse_time_to_seconds(data.time_split)
        if not data_time_seconds:
            return "No time split provided for timed diary task", 400
            
        for task in diary:
            # Parse task time
            task_time_seconds = parse_time_to_seconds(task.diary_time)
            
            # Compare times in seconds
            if data_time_seconds < task_time_seconds:
                if fastest_time is None or task_time_seconds < fastest_time:
                    fastest_time = task_time_seconds
                    succeeded_task = task

        if succeeded_task is None:
            return "Diary time is not fast enough", 400
        
        data.target_diary_id = succeeded_task.id
        data.party_ids = []
        for member in data.party:
            # search case insensitive
            member = member.lower()
            # find user by runescape name
            user = Users.query.filter(Users.runescape_name.ilike(member)).first()
            if user is None or not user.is_active:
                data.party_ids.append("")
            else:
                data.party_ids.append(user.discord_id)
        
        db.session.add(data)
        db.session.commit()
        
        return json.dumps(succeeded_task.serialize(), cls=ModelEncoder), 201
    else: # If the diary is not timed, it is a one-off task
        # Check if the user has already completed the diary
        diary_completion = DiaryCompletionLog.query.filter_by(user_id=user.discord_id, diary_id=str(diary[0].id)).first()
        if diary_completion is not None:
            return "Diary already completed", 400
        
        # Check if the user has already applied for the diary
        diary_application = DiaryApplications.query.filter_by(user_id=user.discord_id, target_diary_id=diary[0].id).first()
        if diary_application is not None and diary_application.status == "Pending":
            return "Diary application already pending", 400
        
    data.target_diary_id = diary[0].id
    db.session.add(data)
    db.session.commit()

    return json.dumps(diary[0].serialize(), cls=ModelEncoder), 201
