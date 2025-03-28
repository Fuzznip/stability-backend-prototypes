from app import app, db
from flask import request
from models.models import Announcements
from helper.helpers import ModelEncoder
import json

@app.route("/announcements", methods=['GET'])
def get_announcements():
    data = []
    rows = Announcements.query.all()
    for row in rows:
        data.append(row.serialize())
    return data

@app.route("/announcements", methods=['POST'])
def create_announcement():
    data = Announcements(**request.get_json())
    if data is None:
        return "No JSON received", 400
    db.session.add(data)
    db.session.commit()
    return json.dumps(data.serialize(), cls=ModelEncoder)

@app.route("/announcements/<id>", methods=['GET'])
def get_announcement(id):
    announcement = Announcements.query.filter_by(id=id).first()
    if announcement is None:
        return "Could not find Announcement", 404
    return json.dumps(announcement.serialize(), cls=ModelEncoder)

@app.route("/announcements/<id>", methods=['PUT'])
def update_announcement(id):
    data = Announcements(**request.get_json())
    if data is None:
        return "No JSON received", 400
    announcement = Announcements.query.filter_by(id=id).first()
    if announcement is None:
        return "Could not find Announcement", 404
    announcement.message = data.message
    db.session.commit()
    return json.dumps(announcement.serialize(), cls=ModelEncoder)

