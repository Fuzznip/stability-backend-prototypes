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
    data = Announcements(request.get_json())
    if data is None:
        return "No JSON received", 400
    db.session.add(data)
    db.session.commit()
    return "Message \"{0}\" Created".format(data.message), 200

