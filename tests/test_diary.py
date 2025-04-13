import json
import pytest
import time
from app import app, db
from models.models import Users
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

def test_create_diary_tasks():
    client = app.test_client()

    # Create four diary tasks for the same piece of content
    with app.app_context():
        tasks = [
            {"diary_name": "Theatre of Blood", "diary_shorthand": "tob3", "boss_name": "tob", "scale": 3, "diary_description": "Task 1 description", "diary_time": "10:00", "diary_points": 10},
            {"diary_name": "Theatre of Blood", "diary_shorthand": "tob3", "boss_name": "tob", "scale": 3, "diary_description": "Task 2 description", "diary_time": "08:00", "diary_points": 20},
            {"diary_name": "Theatre of Blood", "diary_shorthand": "tob3", "boss_name": "tob", "scale": 3, "diary_description": "Task 3 description", "diary_time": "06:00", "diary_points": 30},
            {"diary_name": "Theatre of Blood", "diary_shorthand": "tob3", "boss_name": "tob", "scale": 3, "diary_description": "Task 4 description", "diary_time": "04:00", "diary_points": 40}
        ]
        for task in tasks:
            response = client.post("/diary", json=task)
            assert response.status_code == 200

def test_apply_with_too_slow_time(test_user):
    client = app.test_client()

    # Apply with too slow a time
    application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "tob3",
        "party": [test_user.runescape_name, "Member2", "Member3"],  # Match the required party size
        "time_split": "12:00",
        "proof": "http://example.com/proof.png"
    }
    response = client.post(f"/applications/diary", json=application)
    assert response.status_code == 427
    assert response.data.decode() == "Diary time is not fast enough"

def test_apply_faster_than_previous_times(test_user):
    client = app.test_client()

    # Helper function to apply for a diary
    def apply_for_diary(time_split):
        application = {
            "user_id": test_user.discord_id,
            "runescape_name": test_user.runescape_name,
            "diary_shorthand": "tob3",
            "party": [test_user.runescape_name, "Member2", "Member3"],  # Match the required party size
            "time_split": time_split,
            "proof": "http://example.com/proof.png"
        }
        return client.post(f"/applications/diary", json=application)

    # Apply faster than the first time
    response = apply_for_diary("09:30")
    assert response.status_code == 201

    # Apply faster than the second time
    response = apply_for_diary("07:30")
    assert response.status_code == 201

    # Apply faster than the third time
    response = apply_for_diary("05:30")
    assert response.status_code == 201

    # Apply faster than the fourth time
    response = apply_for_diary("03:30")
    assert response.status_code == 201

    # Apply faster than 1 seconds
    response = apply_for_diary("00:00")
    assert response.status_code == 420 # Should fail as it's not a valid time

def test_approve_all_except_fourth_application():
    client = app.test_client()

    with app.app_context():
        applications = db.session.execute(text("SELECT id FROM diary_applications ORDER BY timestamp")).fetchall()
        for i, app_id in enumerate(applications):
            if i < 3:  # Skip the fourth application
                response = client.put(f"/applications/diary/{app_id[0]}/accept")
                print(response.data)
                assert response.status_code == 200

                # Verify diary points and clan points are updated
                user = Users.query.filter_by(discord_id="12345").first()
                assert user.diary_points == 10 * (i + 1)  # Assuming each application gives 10 points
                assert user.rank_points == 10 * (i + 1)
            else:
                data = { "reason": "Didn't like your style, bub" }
                response = client.put(f"/applications/diary/{app_id[0]}/reject", json=data)
                assert response.status_code == 200

def test_reapply_and_approve_fourth_application(test_user):
    client = app.test_client()

    # Reapply for the fourth time
    application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "tob3",
        "party": [test_user.runescape_name, "Member2", "Member3"],  # Match the required party size
        "time_split": "03:30",
        "proof": "http://example.com/proof.png"
    }
    response = client.post(f"/applications/diary", json=application)
    print(response.data)
    assert response.status_code == 201

    # Parse the application ID from the JSON response
    application_id = json.loads(response.data)["id"]
    assert application_id is not None

    # Approve the fourth application
    response = client.put(f"/applications/diary/{application_id}/accept")
    print(response.data)
    assert response.status_code == 200

    # Verify diary points and clan points are updated
    with app.app_context():
        user = Users.query.filter_by(discord_id=test_user.discord_id).first()
        # Print all variables of user
        print(user.__dict__)

        assert user.diary_points == 40
        assert user.rank_points == 40

def test_apply_again_and_get_all_applications(test_user):
    client = app.test_client()

    # Apply again
    application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "tob3",
        "party": [test_user.runescape_name, "Member2", "Member3"],  # Match the required party size
        "time_split": "03:00",
        "proof": "http://example.com/proof.png"
    }
    response = client.post(f"/applications/diary", json=application)
    assert response.status_code == 201
    
    application_id = json.loads(response.data)["id"]
    assert application_id is not None

    # Apply with one more application
    application = {
        "user_id": test_user.discord_id,
        "runescape_name": test_user.runescape_name,
        "diary_shorthand": "tob3",
        "party": [test_user.runescape_name, "Member2", "Member3"],  # Match the required party size
        "time_split": "02:00",
        "proof": "http://example.com/proof.png"
    }
    response = client.post(f"/applications/diary", json=application)
    assert response.status_code == 201

    # Approve the previous application
    response = client.put(f"/applications/diary/{application_id}/accept")
    assert response.status_code == 200

    # Get all of the applications for the user
    response = client.get(f"/users/{test_user.discord_id}/diary/applications")
    assert response.status_code == 200
    data = json.loads(response.data)
    print(response.data)
    assert len(data) > 0
    assert data[0]["status"] == "Pending"

    response = client.post(f"/applications/diary", json=application)
    assert response.status_code == 201
