"""
Tests for Settings API Endpoints

Verifies REST API for settings management.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from services.settings_service import get_settings_service
import json


@pytest.fixture
def client():
    """Create test client"""
    # Disable rate limiting for tests
    from services.security_service import get_security_service
    security_service = get_security_service()
    security_service.rate_limiter.enabled = False
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings before each test"""
    service = get_settings_service()
    service.reset_to_defaults()
    yield
    service.reset_to_defaults()


def test_get_all_settings(client):
    """Test getting all settings"""
    response = client.get("/api/settings")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "settings" in data
    assert "appearance" in data["settings"]
    assert "notifications" in data["settings"]


def test_get_category_settings(client):
    """Test getting settings for a specific category"""
    response = client.get("/api/settings/appearance")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["category"] == "appearance"
    assert "theme" in data["settings"]


def test_get_specific_setting(client):
    """Test getting a specific setting value"""
    response = client.get("/api/settings/appearance/theme")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["category"] == "appearance"
    assert data["key"] == "theme"
    assert data["value"] in ["dark", "light", "auto"]


def test_update_setting(client):
    """Test updating a specific setting"""
    response = client.put("/api/settings/setting", json={
        "category": "appearance",
        "key": "theme",
        "value": "light"
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["settings"]["appearance"]["theme"] == "light"


def test_update_category(client):
    """Test updating an entire category"""
    response = client.put("/api/settings/category", json={
        "category": "notifications",
        "values": {
            "enabled": False,
            "soundEnabled": False
        }
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["settings"]["notifications"]["enabled"] is False
    assert data["settings"]["notifications"]["soundEnabled"] is False


def test_reset_settings(client):
    """Test resetting settings to defaults"""
    # Modify a setting
    client.put("/api/settings/setting", json={
        "category": "appearance",
        "key": "theme",
        "value": "light"
    })
    
    # Reset appearance category
    response = client.post("/api/settings/reset?category=appearance")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "reset" in data["message"].lower()


def test_export_settings(client):
    """Test exporting settings"""
    # Test export directly through service
    service = get_settings_service()
    settings_json = service.export_settings()
    
    # Verify it's valid JSON
    settings = json.loads(settings_json)
    assert "appearance" in settings
    assert "notifications" in settings


def test_import_settings(client):
    """Test importing settings"""
    settings_json = json.dumps({
        "appearance": {"theme": "light"},
        "notifications": {"enabled": False}
    })
    
    response = client.post("/api/settings/import", json={
        "settings_json": settings_json
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["settings"]["appearance"]["theme"] == "light"


def test_validate_settings(client):
    """Test validating settings"""
    # Valid settings
    response = client.post("/api/settings/validate", json={
        "appearance": {"theme": "dark"},
        "dataRetention": {"keepLogs": 30}
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["valid"] is True


def test_get_cleanup_candidates(client):
    """Test getting cleanup candidates"""
    # Test cleanup candidates directly through service
    service = get_settings_service()
    candidates = service.get_cleanup_candidates()
    
    assert "logs_before" in candidates
    assert "checkpoints_before" in candidates
    assert "failed_runs_before" in candidates
    assert "auto_cleanup_enabled" in candidates


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
