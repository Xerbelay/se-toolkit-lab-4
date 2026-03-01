"""Unit tests for item endpoints edge cases and boundary values."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.item import ItemRecord


@pytest.fixture
def client():
    """Create a test client with API key authentication."""
    # Set the API token to match what we'll send in requests
    os.environ["API_TOKEN"] = "test_token"
    
    # Re-import app after setting env var to pick up new settings
    from importlib import reload
    import app.settings
    reload(app.settings)
    
    import app.main
    reload(app.main)
    
    from app.main import app
    
    with TestClient(app) as test_client:
        yield test_client


def test_get_item_returns_404_for_nonexistent_id(client) -> None:
    """Test that GET /items/{id} returns 404 when item does not exist."""
    with patch(
        "app.routers.items.read_item", new_callable=AsyncMock
    ) as mock_read:
        mock_read.return_value = None
        response = client.get(
            "/items/99999",
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Item not found"


def test_put_item_returns_404_for_nonexistent_id(client) -> None:
    """Test that PUT /items/{id} returns 404 when updating non-existent item."""
    with patch(
        "app.routers.items.update_item", new_callable=AsyncMock
    ) as mock_update:
        mock_update.return_value = None
        response = client.put(
            "/items/99999",
            json={"title": "Updated Title", "description": "Updated description"},
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Item not found"


def test_post_item_with_very_long_title(client) -> None:
    """Test that POST /items accepts very long titles (boundary value)."""
    # Test with a 500-character title (boundary testing)
    long_title = "A" * 500
    
    with patch(
        "app.routers.items.create_item", new_callable=AsyncMock
    ) as mock_create:
        mock_item = ItemRecord(
            id=1,
            type="step",
            parent_id=None,
            title=long_title,
            description="Test description",
        )
        mock_create.return_value = mock_item
        
        response = client.post(
            "/items",
            json={
                "type": "step",
                "parent_id": None,
                "title": long_title,
                "description": "Test description",
            },
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 201
        assert response.json()["title"] == long_title


def test_post_item_with_special_characters_in_title(client) -> None:
    """Test that POST /items accepts titles with special characters (boundary value)."""
    special_title = "Test: <script>alert('XSS')</script> & \"quotes\" 'apostrophe'"
    
    with patch(
        "app.routers.items.create_item", new_callable=AsyncMock
    ) as mock_create:
        mock_item = ItemRecord(
            id=1,
            type="step",
            parent_id=None,
            title=special_title,
            description="Test description",
        )
        mock_create.return_value = mock_item
        
        response = client.post(
            "/items",
            json={
                "type": "step",
                "parent_id": None,
                "title": special_title,
                "description": "Test description",
            },
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 201
        assert response.json()["title"] == special_title


def test_post_item_with_empty_description_succeeds(client) -> None:
    """Test that POST /items accepts empty description (boundary value)."""
    with patch(
        "app.routers.items.create_item", new_callable=AsyncMock
    ) as mock_create:
        mock_item = ItemRecord(
            id=1,
            type="lab",
            parent_id=1,
            title="Test Lab",
            description="",
        )
        mock_create.return_value = mock_item
        
        response = client.post(
            "/items",
            json={
                "type": "lab",
                "parent_id": 1,
                "title": "Test Lab",
                "description": "",
            },
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 201
        assert response.json()["description"] == ""
