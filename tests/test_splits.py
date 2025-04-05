import pytest
from app import app, db
from models.models import Users, Splits
from datetime import datetime
import decimal
import json

@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def test_user():
    user = Users(
        discord_id="12345",
        runescape_name="TestUser",
        is_active=True,
        is_member=True,
        join_date=datetime.now(),
        timestamp=datetime.now()
    )
    db.session.add(user)
    db.session.commit()
    return user

def test_create_split(test_client, test_user):
    split_data = {
        "user_id": test_user.discord_id,
        "item_name": "Test Item",
        "item_price": 5000000,
        "item_id": 123456,
        "group_size": 5,
        "timestamp": datetime.now().isoformat()
    }
    response = test_client.post("/splits", json=split_data)
    assert response.status_code == 200
    assert Splits.query.count() == 1

def test_update_split(test_client, test_user):
    split = Splits(
        user_id=test_user.discord_id,
        item_name="Old Item",
        item_price=3000000,
        item_id=987654,
        group_size=3,
        split_contribution=2000000,
        timestamp=datetime.now()
    )
    db.session.add(split)
    db.session.commit()

    updated_data = {
        "item_name": "Updated Item",
        "item_price": 6000000,
        "item_id": 654321,
        "group_size": 6,
        "split_contribution": 5000000
    }
    response = test_client.put(f"/splits/{split.id}", json=updated_data)
    assert response.status_code == 200
    updated_split = Splits.query.filter_by(id=split.id).first()
    assert updated_split.item_name == "Updated Item"

def test_delete_split(test_client, test_user):
    split_data = {
        "user_id": test_user.discord_id,
        "item_name": "Test Item",
        "item_price": 4000000,
        "item_id": 789012,
        "group_size": 4,
        "timestamp": datetime.now().isoformat()
    }
    response = test_client.post("/splits", json=split_data)
    assert response.status_code == 200
    json_data = json.loads(response.data)
    split_id = json_data["id"]

    response = test_client.delete(f"/splits/{split_id}")
    assert response.status_code == 200
    assert Splits.query.count() == 0

    # Refresh the user from the database
    updated_user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert updated_user.split_points == 0

def test_validate_split(test_client, test_user):
    invalid_split_data = {
        "user_id": test_user.discord_id,
        "item_name": "Invalid Item",
        "item_price": 500000,
        "item_id": 123456,
        "group_size": 5,
        "split_contribution": 400000
    }
    response = test_client.post("/splits", json=invalid_split_data)
    assert response.status_code == 400
    assert b"Split per person cannot be less than 1,000,000" in response.data

def test_split_points_added_correctly(test_client, test_user):
    initial_split_points = test_user.split_points
    split_data = {
        "user_id": test_user.discord_id,
        "item_name": "Test Item",
        "item_price": 5000000,
        "item_id": 123456,
        "group_size": 5,
        "timestamp": datetime.now().isoformat()
    }
    response = test_client.post("/splits", json=split_data)
    assert response.status_code == 200

    # Calculate expected split points
    split_contribution = int((split_data["item_price"] / split_data["group_size"]) * (split_data["group_size"] - 1))
    expected_split_points = round(split_contribution * decimal.Decimal(10 / 4_000_000), 2)

    # Refresh the user from the database
    updated_user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert updated_user.split_points == initial_split_points + expected_split_points

def test_non_member_cannot_submit_split(test_client):
    non_member_user = Users(
        discord_id="67890",
        runescape_name="NonMemberUser",
        is_active=True,
        is_member=False,  # Non-member
        join_date=datetime.now(),
        timestamp=datetime.now()
    )
    db.session.add(non_member_user)
    db.session.commit()

    split_data = {
        "user_id": non_member_user.discord_id,
        "item_name": "Test Item",
        "item_price": 5000000,
        "item_id": 123456,
        "group_size": 5,
        "timestamp": datetime.now().isoformat()
    }
    response = test_client.post("/splits", json=split_data)
    assert response.status_code == 400
    assert b"User is not a member" in response.data

def test_add_and_delete_middle_split(test_client, test_user):
    # Initial split points
    initial_split_points = test_user.split_points

    # Add first split
    split_data_1 = {
        "user_id": test_user.discord_id,
        "item_name": "Item 1",
        "item_price": 3000000,
        "item_id": 111111,
        "group_size": 3,
        "timestamp": datetime.now().isoformat()
    }
    response_1 = test_client.post("/splits", json=split_data_1)
    assert response_1.status_code == 200

    # Add second split
    split_data_2 = {
        "user_id": test_user.discord_id,
        "item_name": "Item 2",
        "item_price": 4000000,
        "item_id": 222222,
        "group_size": 4,
        "timestamp": datetime.now().isoformat()
    }
    response_2 = test_client.post("/splits", json=split_data_2)
    assert response_2.status_code == 200
    split_id_2 = json.loads(response_2.data)["id"]

    # Add third split
    split_data_3 = {
        "user_id": test_user.discord_id,
        "item_name": "Item 3",
        "item_price": 5000000,
        "item_id": 333333,
        "group_size": 5,
        "timestamp": datetime.now().isoformat()
    }
    response_3 = test_client.post("/splits", json=split_data_3)
    assert response_3.status_code == 200

    # Calculate expected points after adding all splits
    split_contribution_1 = int((split_data_1["item_price"] / split_data_1["group_size"]) * (split_data_1["group_size"] - 1))
    split_contribution_2 = int((split_data_2["item_price"] / split_data_2["group_size"]) * (split_data_2["group_size"] - 1))
    split_contribution_3 = int((split_data_3["item_price"] / split_data_3["group_size"]) * (split_data_3["group_size"] - 1))
    total_split_points = round((split_contribution_1 + split_contribution_2 + split_contribution_3) * decimal.Decimal(10 / 4_000_000), 2)

    updated_user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert updated_user.split_points == initial_split_points + total_split_points

    # Delete the middle split
    response_delete = test_client.delete(f"/splits/{split_id_2}")
    assert response_delete.status_code == 200

    # Recalculate expected points after deletion
    remaining_split_points = round((split_contribution_1 + split_contribution_3) * decimal.Decimal(10 / 4_000_000), 2)
    updated_user = Users.query.filter_by(discord_id=test_user.discord_id).first()
    assert updated_user.split_points == initial_split_points + remaining_split_points
