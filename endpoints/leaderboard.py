from app import app, db
from helper.helpers import UUIDEncoder
from flask import request
from models.models import Leaderboard, Killcount
import json


@app.route("/leaderboard", methods=['GET'])
def get_leaderboard():
    data = []
    rows = Leaderboard.query.all()
    for row in rows:
        data.append(row.serialize())
    return data


@app.route("/leaderboard/<bossname>", methods=['GET'])
def get_boss_leaderboard(bossname):
    scale = request.args.get("scale")
    sort = request.args.get("sort")
    data = []
    if scale == None:
        rows = Killcount.query.filter_by(boss_name=bossname).all()
    else:
        rows = Killcount.query.filter_by(boss_name=bossname, scale=scale).all()
    if sort == "pb":
        rows.sort(key=lambda x: x.personal_best, reverse=False)
    elif sort == "kc":
        rows.sort(key=lambda x: x.kill_count, reverse=True)
    for row in rows:
        data.append(row.serialize())
    return data
