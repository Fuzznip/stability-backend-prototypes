from app import app, db
from helper.helpers import ModelEncoder
from helper.time_utils import parse_time_to_seconds
from flask import request
from models.models import ClanApplications, Users
from models.models import DiaryApplications, DiaryTasks, ClanPointsLog, DiaryCompletionLog
from helpers.clan_points_helper import increment_clan_points, PointTag
import json, datetime
import logging

@app.route("/applications", methods=['GET'])
def get_applications():
    params = request.args
    filter = params.get('filter')
    if filter is not None:
        applications = ClanApplications.query.filter_by(status=filter).all()
    else:
        applications = ClanApplications.query.all()
    data = []
    for row in applications:
        data.append(row.serialize())
    return data

@app.route("/applications", methods=['POST'])
def create_application():
    data = ClanApplications(**request.get_json())
    if data is None:
        return "No JSON received", 400
    application = ClanApplications.query.filter_by(user_id=data.user_id).first()
    if application is not None:
        if application.status == "Pending":
            return "Application already exists and is pending", 400
        elif application.status == "Accepted":
            user = Users.query.filter_by(discord_id=data.user_id).first()
            if user and user.is_member and user.is_active:
                return "User is already a member", 400
            else:
                application.status = "Pending"
                application.verdict_timestamp = None
                application.verdict_reason = None
                db.session.commit()
                return "Application status updated to pending", 200
        elif application.status == "Rejected":
            if (datetime.datetime.now() - application.verdict_timestamp).days < 30:
                return "User has been rejected less than 30 days ago", 400

    data.id = None
    db.session.add(data)

    user = Users()
    user.discord_id = data.user_id
    user.runescape_name = data.runescape_name
    user.rank = "Applicant"
    user.rank_points = 0
    user.is_member = False
    user.is_active = True
    user.diary_points = 0
    user.event_points = 0
    user.time_points = 0
    db.session.add(user)

    db.session.commit()
    return json.dumps(data.serialize(), cls=ModelEncoder)

@app.route("/applications/<id>", methods=['GET'])
def get_application(id):
    application = ClanApplications.query.filter_by(id=id).first()
    if application is None:
        return "Could not find Application", 404
    return json.dumps(application.serialize(), cls=ModelEncoder)

@app.route("/applications/<id>", methods=['PUT'])
def update_application(id):
    data = ClanApplications(**request.get_json())
    if data is None:
        return "No JSON received", 400
    application = ClanApplications.query.filter_by(id=id).first()
    if application is None:
        return "Could not find Application", 404
    application.runescape_name = data.runescape_name
    application.referral = data.referral
    application.reason = data.reason
    application.goals = data.goals

    db.session.commit()
    return json.dumps(application.serialize(), cls=ModelEncoder)

@app.route("/applications/<id>", methods=['DELETE'])
def delete_application(id):
    application = ClanApplications.query.filter_by(id=id).first()
    if application is None:
        return "Could not find Application", 404
    db.session.delete(application)
    db.session.commit()
    return "Application deleted", 200

@app.route("/applications/<id>/accept", methods=['PUT'])
def accept_application(id):
    application = ClanApplications.query.filter_by(id=id).first()
    if application is None:
        return "Could not find Application", 404
    application.status = "Accepted"
    application.verdict_timestamp = datetime.datetime.now()

    user = Users.query.filter_by(discord_id=application.user_id).first()
    user.rank = "Trialist"
    user.is_member = True
    user.join_date = datetime.datetime.now()

    increment_clan_points(
        user_id=user.discord_id,
        points=10,  # Example points for accepting an application
        tag=PointTag.EVENT,
        message="Application Accepted"
    )

    db.session.commit()
    return "Application accepted", 200

@app.route("/applications/<id>/reject", methods=['PUT'])
def reject_application(id):
    application = ClanApplications.query.filter_by(id=id).first()
    if application is None:
        return "Could not find Application", 404
    application.status = "Rejected"
    body = request.get_json()
    if body is None:
        application.reason = "No reason provided"
    else:
        application.reason = body["reason"]
    application.verdict_timestamp = datetime.datetime.now()

    user = Users.query.filter_by(discord_id=application.user_id).first()
    user.rank = "Guest"

    db.session.commit()
    return "Application rejected", 200

@app.route("/applications/diary", methods=['GET'])
def get_applications_diary():
    params = request.args
    filter = params.get('filter')
    discord_id = params.get('discord_id')
    
    if filter is not None:
        applications = DiaryApplications.query.filter_by(status=filter).all()
    elif discord_id is not None:
        applications = DiaryApplications.query.filter_by(user_id=discord_id).all()
    else:
        applications = DiaryApplications.query.all()

    data = []
    for row in applications:
        data.append(row.serialize())
    return data

@app.route("/applications/diary", methods=['POST'])
def create_application_diary():
    data = DiaryApplications(**request.get_json())
    if data is None:
        return "No JSON received", 400
    user = Users.query.filter_by(discord_id=data.user_id).first()
    if user is None or not user.is_active:
        return "Could not find User", 404
    diary = DiaryTasks.query.filter_by(diary_shorthand=data.diary_shorthand).all()
    if diary is None or len(diary) == 0:
        return "Could not find Diary", 404
    
    data.user_id = user.discord_id
    data.runescape_name = user.runescape_name
    data.diary_name = diary[0].diary_name # All diaries with the same shorthand have the same name

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

@app.route("/applications/diary/<id>", methods=['GET'])
def get_application_diary(id):
    application = DiaryApplications.query.filter_by(id=id).first()
    if application is None:
        return "Could not find Application", 404
    return json.dumps(application.serialize(), cls=ModelEncoder)

@app.route("/applications/diary/<id>/accept", methods=['PUT'])
def accept_application_diary(id):
    application = DiaryApplications.query.filter_by(id=id).first()
    if application is None:
        return "Could not find Application", 404
    
    if application.status != "Pending":
        return "Application is not pending", 400
    
    target_diary = DiaryTasks.query.filter_by(id=application.target_diary_id).first()
    if target_diary is None:
        return "Could not find Diary", 404
    application.status = "Accepted"
    application.verdict_timestamp = datetime.datetime.now()
    
    update_successful = []
    update_failed = []

    # Grab all of the users in the party
    users = application.party_ids
    if users is None or len(users) == 0:
        users = [application.user_id]
    
    for i, user_id in enumerate(users):
        user = Users.query.filter_by(discord_id=user_id).first()
        if user is None:
            update_failed.append(application.party[i])
            continue

        # Grab the latest diary progress for the user for this diary
        current_diary_progress = DiaryCompletionLog.query.filter_by(user_id=user.discord_id, diary_category_shorthand=application.diary_shorthand).order_by(DiaryCompletionLog.timestamp.desc()).first()

        if current_diary_progress is None:
            new_diary_progress = DiaryCompletionLog()
            new_diary_progress.user_id = user_id
            new_diary_progress.diary_id = application.target_diary_id
            new_diary_progress.diary_category_shorthand = target_diary.diary_shorthand
            if application.party is not None:
                new_diary_progress.party = application.party
                new_diary_progress.party_ids = users
            new_diary_progress.proof = application.proof
            new_diary_progress.time_split = application.time_split
            db.session.add(new_diary_progress)

            increment_clan_points(
                user_id=user.discord_id,
                points=target_diary.diary_points,
                tag=PointTag.DIARY,
                message=application.diary_shorthand
            )

            update_successful.append(user_id)
        else:
            # Check to see if the application is faster than the current diary time
            # and faster than the applied diary time
            current_time_seconds = parse_time_to_seconds(current_diary_progress.time_split)
            application_time_seconds = parse_time_to_seconds(application.time_split)
            target_time_seconds = parse_time_to_seconds(target_diary.diary_time)
            if current_time_seconds is None or application_time_seconds is None:
                update_failed.append(user_id)
                continue
            if application_time_seconds < current_time_seconds and application_time_seconds < target_time_seconds:
                new_diary_progress = DiaryCompletionLog()
                new_diary_progress.user_id = user_id
                new_diary_progress.diary_id = application.target_diary_id
                new_diary_progress.diary_category_shorthand = target_diary.diary_shorthand
                if application.party is not None:
                    new_diary_progress.party = application.party
                    new_diary_progress.party_ids = users
                new_diary_progress.proof = application.proof
                new_diary_progress.time_split = application.time_split
                db.session.add(new_diary_progress)

                # Get the difference in points between the new diary and the old diary
                current_diary = DiaryTasks.query.filter_by(id=current_diary_progress.diary_id).first()
                if current_diary is not None:
                    points_difference = target_diary.diary_points - current_diary.diary_points
                else:
                    points_difference = 0
                    logging.warning("Could not find current diary for id: " + str(current_diary_progress.diary_id))
                
                increment_clan_points(
                    user_id=user.discord_id,
                    points=points_difference,
                    tag=PointTag.DIARY,
                    message=application.diary_shorthand
                )

                update_successful.append(user_id)
            else:
                update_failed.append(user_id)
                continue

    db.session.commit()

    return_json = {
        "successful": update_successful,
        "failed": update_failed
    }
    return json.dumps(return_json), 200

@app.route("/applications/diary/<id>/reject", methods=['PUT'])
def reject_application_diary(id):
    application = DiaryApplications.query.filter_by(id=id).first()
    if application is None:
        return "Could not find Application", 404
    
    if application.status != "Pending":
        return "Application is not pending", 400

    application.status = "Rejected"
    body = request.get_json()
    if body is None or "reason" not in body:
        application.reason = "No reason provided"
    else:
        application.reason = body["reason"]
    application.verdict_timestamp = datetime.datetime.now()

    db.session.commit()
    return "Application rejected", 200
