from app import app, db
from helper.helpers import ModelEncoder
from flask import request
from models.models import ClanApplications, Users
import json, datetime

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
            return "Application already exists", 400
        elif application.status == "Accepted":
            user = Users.query.filter_by(discord_id=data.user_id).first()
            if user and user.is_member:
                return "User is already a member", 400
        elif application.status == "Rejected":
            if (datetime.datetime.now() - application.verdict_timestamp).days < 30:
                return "User has been rejected", 400

    data.id = None
    db.session.add(data)

    user = Users()
    user.discord_id = data.user_id
    user.runescape_name = data.runescape_name
    user.rank = "Applicant"
    user.rank_points = 0
    user.is_member = False
    user.join_date = None
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

