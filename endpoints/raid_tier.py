from app import app, db
from helper.helpers import ModelEncoder
from flask import request
from models.models import RaidTiers
import json


@app.route("/raidTier", methods=['GET'])
def get_raid_tiers():
    content = request.args.get('content')
    if content is not None:
        tiers = RaidTiers.query.filter(RaidTiers.tier_name.contains(content)).all()
    else:
        tiers = RaidTiers.query.all()
    data = [tier.serialize() for tier in tiers]
    return json.dumps(data, cls=ModelEncoder)

@app.route("/raidTier", methods=['POST'])
def create_raid_tier():
    data = RaidTiers(**request.get_json())
    if data is None:
        return "No JSON received", 400
    tier = RaidTiers.query.filter_by(tier_name=data.tier_name, tier_order=data.tier_order).count()
    if tier > 0:
        return "Raid tier already exists", 400
    db.session.add(data)
    db.session.commit()
    return json.dumps(data.serialize(), cls=ModelEncoder)


@app.route("/raidTier/<id>", methods=['GET'])
def get_raid_tier(id):
    tier = RaidTiers.query.filter_by(id=id).first()
    if tier is None:
        return "Could not find Raid Tier", 404
    return json.dumps(tier.serialize(), cls=ModelEncoder)


@app.route("/raidTier/<id>", methods=['PUT'])
def update_raid_tier(id):
    data = RaidTiers(**request.get_json())
    if data is None:
        return "No JSON received", 400
    tier = RaidTiers.query.filter_by(id=id).first()
    if tier is None:
        return "Could not find Raid Tier", 404
    tier.tier_name = data.tier_name
    tier.tier_order = data.tier_order
    tier.tier_icon = data.tier_icon
    tier.tier_color = data.tier_color
    tier.tier_description = data.tier_description
    tier.tier_requirements = data.tier_requirements
    tier.tier_points = data.tier_points
    db.session.commit()
    return json.dumps(tier.serialize(), cls=ModelEncoder)


@app.route("/raidTier/<id>", methods=['DELETE'])
def delete_raid_tier(id):
    task = RaidTiers.query.filter_by(id=id).first()
    if task is None:
        return "Could not find Raid Tier", 404
    db.session.delete(task)
    db.session.commit()
    return "Raid Tier deleted", 200
