# test_shop_generator_pytest.py
import pytest
from collections import Counter
from typing import List, Dict, Any

# Import the function to be tested from your event_handlers.stability_party.item_system
from event_handlers.stability_party.item_system import generate_shop_inventory

# Import the actual get_all_items function and ItemDefinition from your item registry
# This assumes your project structure allows this import (e.g., running pytest from project root)
try:
    from event_handlers.stability_party.item_definitions import (
        get_all_items as actual_get_all_items,
        ItemDefinition as ActualItemDefinition, # We can use this for more specific type hints if needed
        ITEM_REGISTRY as ACTUAL_ITEM_REGISTRY # To check if items are loaded
    )
except ImportError as e:
    pytest.skip(f"Skipping tests that require item_registry.py: {e}", allow_module_level=True)

# Define the base rarity weights that will be used by the mocked RARITY_WEIGHTS
# This remains the same as it's specific to the event_handlers.stability_party.item_system's logic
# Updated weights for desired distribution:
# Legendary: 1%
# Epic: ~9%
# Rare: ~20%
# Uncommon: ~30%
# Common: ~40%
MOCK_RARITY_WEIGHTS_CONFIG: Dict[str, int] = {
    "common": 50,
    "uncommon": 30, 
    "rare": 15,
    "epic": 4,
    "legendary": 1
}

# Pytest fixture to mock get_all_items in event_handlers.stability_party.item_system
# This fixture will now make event_handlers.stability_party.item_system.get_all_items use the *actual*
# get_all_items from your item_registry.py
@pytest.fixture
def mock_get_all_items_fixture(mocker):
    """
    Mocks the get_all_items function within event_handlers.stability_party.item_system
    to use the actual get_all_items from event_handlers.stability_party.item_registry.
    """
    # Ensure the actual item registry has items. This happens at import time of item_registry.py
    if not ACTUAL_ITEM_REGISTRY:
        pytest.skip("Actual item registry is empty. Ensure items are registered in item_registry.py.")

    # Patch the get_all_items function *where it is looked up* by generate_shop_inventory,
    # which is within 'event_handlers.stability_party.item_system'.
    # We replace it with the actual_get_all_items function.
    mocked_function = mocker.patch('event_handlers.stability_party.item_system.get_all_items', side_effect=actual_get_all_items)
    return mocked_function

# Pytest fixture to mock RARITY_WEIGHTS in event_handlers.stability_party.item_system
@pytest.fixture
def mock_rarity_weights_fixture(mocker):
    """Mocks the RARITY_WEIGHTS global in event_handlers.stability_party.item_system."""
    return mocker.patch('event_handlers.stability_party.item_system.RARITY_WEIGHTS', MOCK_RARITY_WEIGHTS_CONFIG)

# Pytest fixture to mock logging in event_handlers.stability_party.item_system
@pytest.fixture
def mock_logging_fixture(mocker):
    """Mocks the logging module used in event_handlers.stability_party.item_system."""
    return mocker.patch('event_handlers.stability_party.item_system.logging')


def test_item_distribution_over_many_runs(
    mock_get_all_items_fixture, 
    mock_rarity_weights_fixture, 
    mock_logging_fixture,
    capsys # Pytest fixture to capture stdout/stderr
    ):
    """
    Tests the item distribution from generate_shop_inventory over many runs,
    using the actual item registry. Tallies item occurrences by name.
    """
    num_runs = 100000 # You might want to reduce this for faster local tests initially
    item_name_counts = Counter()
    
    # Parameters for the shop generation
    event_id_prefix = "sim_event_pytest_actual_registry"
    shop_tier_to_test = 1 # Test with tier 1
    items_per_shop = 3    # Generate 3 items per shop

    # Get the list of available item names from the actual registry for context
    all_actual_items_list = actual_get_all_items()
    available_item_names = [item.name for item in actual_get_all_items()]
    
    # Create a map of item names to their rarities for easy lookup
    item_rarity_map = {item.name: item.rarity for item in all_actual_items_list}
    
    print(f"\nRunning generate_shop_inventory {num_runs} times with pytest...")
    print(f"Shop Tier: {shop_tier_to_test}, Items per shop: {items_per_shop}")
    print(f"Using actual item registry with {len(available_item_names)} unique items.")
    print(f"Available item names: {', '.join(available_item_names[:10])}..." if available_item_names else "No items in registry!")
    print(f"Base Rarity Weights (mocked in event_handlers.stability_party.item_system): {MOCK_RARITY_WEIGHTS_CONFIG}")

    if not available_item_names:
        pytest.fail("Test cannot run meaningfully without items in the actual item registry.")

    for i in range(num_runs):
        event_id = f"{event_id_prefix}_{i}"
        
        generated_items = generate_shop_inventory(
            event_id=event_id,
            shop_tier=shop_tier_to_test,
            item_count=items_per_shop
        )
        
        # Basic check: ensure items_per_shop are generated if possible
        # This depends on the number of unique items in your registry vs items_per_shop
        if len(actual_get_all_items()) >= items_per_shop:
             assert len(generated_items) == items_per_shop, \
                f"Run {i}: Expected {items_per_shop} items, but got {len(generated_items)}. Event ID: {event_id}"
        else:
            assert len(generated_items) <= len(actual_get_all_items()), \
                f"Run {i}: Expected at most {len(actual_get_all_items())} items, but got {len(generated_items)}. Event ID: {event_id}"


        for item in generated_items:
            assert 'name' in item, f"Generated item missing 'name' field: {item}"
            item_name_counts[item['name']] += 1

    total_items_generated = sum(item_name_counts.values())
    
    # Output the tally (will be printed to console when test runs with -s)
    print("\n--- Item Name Tally (after {num_runs} runs, using actual item registry) ---")
    if not item_name_counts:
        print("No items were generated across all runs.")
    else:
        for item_name, count in item_name_counts.most_common():
            percentage = (count / total_items_generated) * 100 if total_items_generated > 0 else 0
            rarity = item_rarity_map.get(item_name, "UNKNOWN_RARITY").upper() # Get rarity, convert to uppercase
            print(f"[{rarity}] {item_name}: {count} ({percentage:.2f}%)")
    
    total_items_generated = sum(item_name_counts.values())
    print(f"\nTotal items generated across all runs: {total_items_generated}")
    
    # --- Assertions ---
    # Assert that the (mocked to be actual) get_all_items was called
    assert mock_get_all_items_fixture.called, "event_handlers.stability_party.item_system.get_all_items was not called"
    assert mock_get_all_items_fixture.call_count == num_runs, \
        (f"Expected event_handlers.stability_party.item_system.get_all_items to be called {num_runs} times, "
         f"but was called {mock_get_all_items_fixture.call_count} times")

    # Assert that some items were generated if the registry is not empty
    if available_item_names:
        assert total_items_generated > 0, "No items were tallied, but the registry is not empty."
        # Check that all tallied items are from the known list of names
        for name in item_name_counts:
            assert name in available_item_names, f"Generated item '{name}' is not in the actual item registry."
    else:
        assert total_items_generated == 0, "Items were tallied, but the registry was expected to be empty."

    # Expected total items, considering the possibility of not enough unique items
    # If there are fewer unique items than items_per_shop, the shop can't be full.
    max_possible_items_per_shop = min(items_per_shop, len(available_item_names))
    expected_total_items_lower_bound = num_runs * max_possible_items_per_shop
    
    if len(available_item_names) >= items_per_shop :
        # If enough unique items, we expect exactly items_per_shop * num_runs
         assert total_items_generated == expected_total_items_lower_bound, \
            (f"Expected exactly {expected_total_items_lower_bound} items, but got {total_items_generated}. "
             "This might indicate issues with item generation logic when enough unique items are available.")
    else:
        # If not enough unique items, total generated should be num_runs * number_of_unique_items
        assert total_items_generated <= expected_total_items_lower_bound, \
            (f"Expected at most {expected_total_items_lower_bound} items, but got {total_items_generated}."
            "This could be due to limited unique items or generation logic issues.")


# To run this test:
# 1. Ensure `event_handlers.stability_party.item_system.py` exists.
# 2. Ensure `event_handlers/stability_party/item_registry.py` exists and is populated.
# 3. Ensure `__init__.py` files are in `event_handlers/` and `event_handlers/stability_party/`.
# 4. Save this code as `test_shop_generator_pytest.py` in your project root.
# 5. Ensure pytest and pytest-mock are installed (`pip install pytest pytest-mock`).
# 6. Open your terminal in the project root directory and run: `pytest -s -v`
#    (-s shows print statements, -v for verbose output)
