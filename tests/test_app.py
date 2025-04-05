import json
from app import app, db
from models.models import Users

def setup_module(module):
    with app.app_context():
        # Setup test database
        db.create_all()

        # Add a test user
        test_user = Users(
            discord_id="12345",
            runescape_name="TestUser",
            is_active=True
        )
        db.session.add(test_user)
        db.session.commit()

def teardown_module(module):
    with app.app_context():
        # Clean up test database
        db.session.remove()
        db.drop_all()

def test_get_users():
    client = app.test_client()
    response = client.get("/users")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0

def test_create_user():
    client = app.test_client()
    new_user = {
        "discord_id": "67890",
        "runescape_name": "NewUser",
        "is_active": True
    }
    response = client.post("/users", json=new_user)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["discord_id"] == "67890"

def test_get_user_profile():
    client = app.test_client()
    response = client.get("/users/12345")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["runescape_name"] == "TestUser"

def test_update_user_profile():
    client = app.test_client()
    updated_data = {
        "runescape_name": "UpdatedUser",
        "rank": "General",
        "progression_data": {}
    }
    response = client.put("/users/12345", json=updated_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["runescape_name"] == "UpdatedUser"

def test_delete_user():
    client = app.test_client()
    response = client.delete("/users/12345")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == "User deleted successfully"

def test_rename_user():
    client = app.test_client()
    rename_data = {
        "runescape_name": "RenamedUser"
    }
    response = client.put("/users/67890/rename", json=rename_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["runescape_name"] == "RenamedUser"