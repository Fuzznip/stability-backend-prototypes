from app import app, db
from helper.helpers import ModelEncoder
from flask import request
from models.models import ClanApplications
import json

@app.route("/applications", methods=['GET'])
def get_applications():
    data = []
    applications = ClanApplications.query.all()
    for row in applications:
        data.append(row.serialize())
    return data

@app.route("/applications", methods=['POST'])
def create_application():
    data = ClanApplications(**request.get_json())
    if data is None:
        return "No JSON received", 400
    if ClanApplications.query.filter_by(discord_id=data.discord_id).first() is not None:
        return "Id already exists", 400
    data.id = None
    db.session.add(data)
    db.session.commit()
    return json.dumps(data.serialize(), cls=ModelEncoder)

@app.route("/applications/<id>", methods=['GET'])
def get_application(id):
    return json.dumps(ClanApplications.query.filter_by(id=id).first().serialize(), cls=ModelEncoder)

@app.route("/applications/<id>", methods=['PUT'])
def update_application(id):
    data = ClanApplications(**request.get_json())
    if data is None:
        return "No JSON received", 400
    application = ClanApplications.query.filter_by(id=id).first()
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
    db.session.commit()
    return "Application accepted", 200

@app.route("/applications/<id>/reject", methods=['PUT'])
def reject_application(id):
    application = ClanApplications.query.filter_by(id=id).first()
    if application is None:
        return "Could not find Application", 404
    application.status = "Rejected"
    db.session.commit()
    return "Application rejected", 200

