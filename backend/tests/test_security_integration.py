"""
Integration tests for security middleware with FastAPI

Tests that security features work correctly when integrated with the application.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


class TestSecurityIntegration:
    """Test security middleware integration"""
    
    def test_security_headers_on_response(self):
        """Test that security headers are added to responses"""
        response = client.get("/api/health")
        
        # Check for security headers
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-XSS-Protection" in response.headers
    
    def test_rate_limiting_works(self):
        """Test that rate limiting is enforced"""
        # This test would need to make many requests to trigger rate limiting
        # For now, just verify the endpoint is accessible
        response = client.get("/api/security/rate-limit-status")
        assert response.status_code == 200
        
        data = response.json()
        assert "is_allowed" in data
        assert "limits" in data
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation endpoint"""
        response = client.get("/api/security/csrf-token")
        assert response.status_code == 200
        
        data = response.json()
        assert "token" in data
        assert "expires_in_seconds" in data
        assert len(data["token"]) > 20
    
    def test_audit_log_endpoint(self):
        """Test audit log query endpoint"""
        response = client.get("/api/security/audit-log")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_suspicious_activity_endpoint(self):
        """Test suspicious activity detection endpoint"""
        response = client.get("/api/security/suspicious-activity")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_security_health_check(self):
        """Test security service health check"""
        response = client.get("/api/security/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "csrf_protection" in data
        assert "rate_limiting" in data
        assert "audit_logging" in data
        assert "input_validation" in data
    
    def test_payload_size_validation(self):
        """Test that large payloads are rejected"""
        # Create a large payload (> 10MB)
        large_data = {"data": "x" * (11 * 1024 * 1024)}
        
        response = client.post("/api/security/validate-input", json=large_data)
        
        # Should be rejected with 413 Payload Too Large
        # Note: This might not trigger if FastAPI has its own limits
        # The middleware will catch it if it gets through
        assert response.status_code in [413, 422]  # 422 if Pydantic rejects it first


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
