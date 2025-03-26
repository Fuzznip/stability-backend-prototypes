from app import app, db
from flask import request
from models.models import Announcements


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
    return "Message \"{0}\" Created".format(data.message), 200

@app.route("/announcements/<id>", methods=['GET'])
def get_announcement(id):
    return Announcements.query.filter_by(id=id).first().serialize()

@app.route("/announcements/<id>", methods=['PUT'])
def update_announcement(id):
    data = Announcements(**request.get_json())
    if data is None:
        return "No JSON received", 400
    announcement = Announcements.query.filter_by(id=id).first()
    announcement.message = data.message
    db.session.commit()
    return "Message \"{0}\" Updated".format(announcement.message), 200

