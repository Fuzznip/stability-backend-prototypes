import json
import pytest
import time
from app import app, db
from models.models import Users, DiaryApplications, DiaryCompletionLog
from sqlalchemy.sql import text

@pytest.fixture(scope="module")
def test_user():
    """
    Fixture to create a test user before the tests and delete the user after the tests finish.
    """
    with app.app_context():
        # Create the test user
        user = Users(
            discord_id="12345",
            runescape_name="TestUser",
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        yield user  # Provide the user to the tests

        # Clean up the test user
        db.session.delete(user)
        db.session.commit()

def setup_module(module):
    with app.app_context():
        # Setup test database
        db.create_all()

def teardown_module(module):
    with app.app_context():
        # Clean up test database
        db.session.remove()
        db.drop_all()

def teardown_function(function):
    """Teardown function to delete all applications after each test."""
    with app.app_context():
        # set user diary and clan points to 0
        sql = text("UPDATE users SET diary_points = 0, rank_points = 0 WHERE discord_id = '12345'")
        db.session.execute(sql)

        # Delete all diary applications
        DiaryApplications.query.delete()
        # Delete all diary completion logs
        DiaryCompletionLog.query.delete()
        db.session.commit()

def test_create_diary_tasks():
    client = app.test_client()

    # Create three diary tasks for the same piece of content
    with app.app_context():
        tasks = [
            {"diary_name": "Combat Achievements", "diary_shorthand": "master", "boss_name": "master", "scale": 1, "diary_description": "Master description", "diary_time": None, "diary_points": 3500},
            {"diary_name": "Combat Achievements", "diary_shorthand": "gm", "boss_name": "gm", "scale": 1, "diary_description": "Grandmaster description", "diary_time": None, "diary_points": 5000},
            {"diary_name": "Combat Achievements", "diary_shorthand": "elite", "boss_name": "elite", "scale": 1, "diary_description": "Elite description", "diary_time": None, "diary_points": 1000},
        ]
        for task in tasks:
            response = client.post("/diary", json=task)
            assert response.status_code == 200

def test_apply_elite_twice(test_user):
    client = app.test_client()

    # First application (rejected)
    first_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "elite",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof1"
    }
    response = client.post("/applications/diary", json=first_application)
    assert response.status_code == 201

    application_id = json.loads(response.data)["id"]

    # Reject the first application
    reject_payload = {"reason": "Insufficient proof"}
    response = client.put(f"/applications/diary/{application_id}/reject", json=reject_payload)
    assert response.status_code == 200

    # Second application (accepted)
    second_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "elite",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof2"
    }
    response = client.post("/applications/diary", json=second_application)
    assert response.status_code == 201

    application_id = json.loads(response.data)["id"]

    # Accept the second application
    response = client.put(f"/applications/diary/{application_id}/accept")
    assert response.status_code == 200

def test_apply_elite_and_master(test_user):
    client = app.test_client()

    # Apply for elite
    elite_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "elite",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_elite"
    }
    response = client.post("/applications/diary", json=elite_application)
    assert response.status_code == 201

    elite_application_id = json.loads(response.data)["id"]

    # Accept elite application
    response = client.put(f"/applications/diary/{elite_application_id}/accept")
    assert response.status_code == 200

    # Verify points after elite
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 1000

    # Apply for master
    master_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "master",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_master"
    }
    response = client.post("/applications/diary", json=master_application)
    assert response.status_code == 201

    master_application_id = json.loads(response.data)["id"]

    # Accept master application
    response = client.put(f"/applications/diary/{master_application_id}/accept")
    assert response.status_code == 200

    # Verify points after master
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 3500

def test_apply_master_and_gm(test_user):
    client = app.test_client()

    # Apply for master
    master_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "master",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_master"
    }
    response = client.post("/applications/diary", json=master_application)
    assert response.status_code == 201

    master_application_id = json.loads(response.data)["id"]

    # Accept master application
    response = client.put(f"/applications/diary/{master_application_id}/accept")
    assert response.status_code == 200

    # Verify points after master
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 3500

    # Apply for grandmaster (gm)
    gm_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "gm",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_gm"
    }
    response = client.post("/applications/diary", json=gm_application)
    assert response.status_code == 201

    gm_application_id = json.loads(response.data)["id"]

    # Accept gm application
    response = client.put(f"/applications/diary/{gm_application_id}/accept")
    assert response.status_code == 200

    # Verify points after gm
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 5000

def test_apply_gm(test_user):
    client = app.test_client()

    # Apply for grandmaster (gm)
    gm_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "gm",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_gm"
    }
    response = client.post("/applications/diary", json=gm_application)
    assert response.status_code == 201

    gm_application_id = json.loads(response.data)["id"]

    # Accept gm application
    response = client.put(f"/applications/diary/{gm_application_id}/accept")
    assert response.status_code == 200

    # Verify points after gm
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 5000

def test_apply_gm_then_elite_and_master(test_user):
    client = app.test_client()

    # Apply for grandmaster (gm)
    gm_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "gm",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_gm"
    }
    response = client.post("/applications/diary", json=gm_application)
    assert response.status_code == 201

    gm_application_id = json.loads(response.data)["id"]

    # Accept gm application
    response = client.put(f"/applications/diary/{gm_application_id}/accept")
    assert response.status_code == 200

    # Verify points after gm
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 5000

    # Attempt to apply for elite
    elite_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "elite",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_elite"
    }
    response = client.post("/applications/diary", json=elite_application)
    assert response.status_code == 400  # Should fail since gm is already completed

    # Attempt to apply for master
    master_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "master",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_master"
    }
    response = client.post("/applications/diary", json=master_application)
    assert response.status_code == 400  # Should fail since gm is already completed

def test_apply_multiple_tiers(test_user):
    client = app.test_client()

    # Apply for elite
    elite_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "elite",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_elite"
    }
    response = client.post("/applications/diary", json=elite_application)
    assert response.status_code == 201
    elite_application_id = json.loads(response.data)["id"]
    response = client.put(f"/applications/diary/{elite_application_id}/accept")
    assert response.status_code == 200

    # Verify points after elite
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 1000

    # Apply for master
    master_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "master",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_master"
    }
    response = client.post("/applications/diary", json=master_application)
    assert response.status_code == 201
    master_application_id = json.loads(response.data)["id"]
    response = client.put(f"/applications/diary/{master_application_id}/accept")
    assert response.status_code == 200

    # Verify points after master
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 3500

    # Attempt to apply for elite again
    response = client.post("/applications/diary", json=elite_application)
    assert response.status_code == 430  # Should fail since elite is already completed

    # Apply for grandmaster (gm)
    gm_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "gm",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_gm"
    }
    response = client.post("/applications/diary", json=gm_application)
    assert response.status_code == 201
    gm_application_id = json.loads(response.data)["id"]
    response = client.put(f"/applications/diary/{gm_application_id}/accept")
    assert response.status_code == 200

    # Verify points after grandmaster
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 5000

    # Attempt to apply for elite again
    response = client.post("/applications/diary", json=elite_application)
    assert response.status_code == 430  # Should fail since gm is already completed

    # Attempt to apply for master again
    response = client.post("/applications/diary", json=master_application)
    assert response.status_code == 430  # Should fail since gm is already completed

def test_apply_master_then_gm_then_elite(test_user):
    client = app.test_client()

    # Apply for master
    master_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "master",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_master"
    }
    response = client.post("/applications/diary", json=master_application)
    assert response.status_code == 201
    master_application_id = json.loads(response.data)["id"]
    response = client.put(f"/applications/diary/{master_application_id}/accept")
    assert response.status_code == 200

    # Verify points after master
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 3500

    # Apply for grandmaster (gm)
    gm_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "gm",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_gm"
    }
    response = client.post("/applications/diary", json=gm_application)
    assert response.status_code == 201
    gm_application_id = json.loads(response.data)["id"]
    response = client.put(f"/applications/diary/{gm_application_id}/accept")
    assert response.status_code == 200

    # Verify points after gm
    user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert user.diary_points == 5000

    # Attempt to apply for elite
    elite_application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "elite",
        "party": [test_user.runescape_name],
        "proof": "http://example.com/proof_elite"
    }
    response = client.post("/applications/diary", json=elite_application)
    assert response.status_code == 400  # Should fail since gm is already completed

