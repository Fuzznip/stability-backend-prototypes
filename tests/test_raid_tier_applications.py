import json
import pytest
from app import app, db
from models.models import Users, RaidTiers, RaidTierApplication, RaidTierLog
from sqlalchemy.sql import text

@pytest.fixture(scope="module")
def test_user():
    """
    Fixture to create a test user before the tests and delete the user after the tests finish.
    """
    with app.app_context():
        user = Users(
            discord_id="12345",
            runescape_name="TestUser",
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        yield user

        db.session.delete(user)
        db.session.commit()

def setup_module(module):
    with app.app_context():
        db.create_all()

def teardown_module(module):
    with app.app_context():
        db.session.remove()
        db.drop_all()

def teardown_function(function):
    with app.app_context():
        sql = text("UPDATE users SET raid_tier_points = 0, rank_points = 0 WHERE discord_id = '12345'")
        db.session.execute(sql)
        RaidTierApplication.query.delete()
        RaidTierLog.query.delete()
        db.session.commit()

def test_create_raid_tiers():
    client = app.test_client()

    with app.app_context():
        tiers = [
            {"tier_name": "CoX Tier 0", "tier_order": 0, "tier_points": 0, "tier_description": "0 KC", "tier_requirements": "Collection Log screenshot"},
            {"tier_name": "CoX Tier 1", "tier_order": 1, "tier_points": 10, "tier_description": "Completed a raid", "tier_requirements": "Collection Log screenshot"},
            {"tier_name": "CoX Tier 2", "tier_order": 2, "tier_points": 20, "tier_description": "Deathless raid", "tier_requirements": "'Undying Raid Team' Combat Achievement screenshot"},
            {"tier_name": "CoX Tier 3", "tier_order": 3, "tier_points": 30, "tier_description": "Completed a raid with a team of 4", "tier_requirements": "'The Four Horsemen' Combat Achievement screenshot"},
            {"tier_name": "CoX Tier 4", "tier_order": 4, "tier_points": 40, "tier_description": "Completed a raid with a team of 3", "tier_requirements": "'The Three Musketeers' Combat Achievement screenshot"},
        ]
        for tier in tiers:
            response = client.post("/raidTier", json=tier)
            assert response.status_code == 200

def test_apply_tier_1(test_user):
    client = app.test_client()

    application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "proof": "http://example.com/proof_tier1",
        "target_raid_tier_id": RaidTiers.query.filter_by(tier_order=1).first().id
    }
    response = client.post("/applications/raidTier", json=application)
    assert response.status_code == 201

    application_id = json.loads(response.data)["id"]

    # Accept the application
    response = client.put(f"/applications/raidTier/{application_id}/accept")
    assert response.status_code == 200

    # Verify points and tier progression
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.raid_tier_points == 10

def test_apply_tier_2_then_reject(test_user):
    client = app.test_client()

    application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "proof": "http://example.com/proof_tier2",
        "target_raid_tier_id": RaidTiers.query.filter_by(tier_order=2).first().id
    }
    response = client.post("/applications/raidTier", json=application)
    assert response.status_code == 201

    application_id = json.loads(response.data)["id"]

    # Reject the application
    reject_payload = {"reason": "Insufficient proof"}
    response = client.put(f"/applications/raidTier/{application_id}/reject", json=reject_payload)
    assert response.status_code == 200

def test_apply_tier_2_after_rejection(test_user):
    client = app.test_client()

    application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "proof": "http://example.com/proof_tier2_v2",
        "target_raid_tier_id": RaidTiers.query.filter_by(tier_order=2).first().id
    }
    response = client.post("/applications/raidTier", json=application)
    assert response.status_code == 201

    application_id = json.loads(response.data)["id"]

    # Accept the application
    response = client.put(f"/applications/raidTier/{application_id}/accept")
    assert response.status_code == 200

    # Verify points and tier progression
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.raid_tier_points == 20