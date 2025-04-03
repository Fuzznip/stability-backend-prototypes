from app import app, db
from helper.helpers import ModelEncoder
from flask import request
from models.models import ClanRanks
import json

@app.route("/ranks", methods=['GET'])
def get_all_ranks():
    ranks = ClanRanks.query.order_by(ClanRanks.rank_order).all()
    return json.dumps([rank.serialize() for rank in ranks], cls=ModelEncoder)
