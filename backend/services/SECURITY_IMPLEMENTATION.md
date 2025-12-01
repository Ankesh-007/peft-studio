# Security Best Practices Implementation

## Overview

This document describes the comprehensive security implementation for PEFT Studio, covering all aspects of application security including input validation, CSRF protection, rate limiting, secure headers, and audit logging.

**Validates Requirements:** 15.1, 15.2, 15.3, 15.4, 15.5

## Architecture

The security system consists of several integrated components:

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Application                    │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Security Middleware Layer                   │ │
│  │  - SecurityMiddleware (rate limit, headers, audit) │ │
│  │  - InputValidationMiddleware (payload validation)  │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │           Security Service Layer                    │ │
│  │  - InputValidator (sanitization, validation)       │ │
│  │  - CSRFProtection (token management)               │ │
│  │  - RateLimiter (request throttling)                │ │
│  │  - SecurityAuditLogger (event logging)             │ │
│  │  - SecurityHeadersManager (header configuration)   │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Security API Endpoints                 │ │
│  │  - /api/security/csrf-token                        │ │
│  │  - /api/security/audit-log                         │ │
│  │  - /api/security/suspicious-activity               │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. Input Validation and Sanitization (Requirement 15.1)

**Purpose:** Protect against injection attacks and malicious input.

**Features:**
- HTML escaping and sanitization
- SQL injection detection
- XSS (Cross-Site Scripting) detection
- Path traversal detection
- Command injection detection
- Length validation
- Pattern validation (regex)
- Allowed values validation

**Usage Example:**

```python
from services.security_service import get_security_service, ValidationRule

security_service = get_security_service()

# Define validation rules
rules = [
    ValidationRule(
        field_name="username",
        required=True,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_]+$"
    ),
    ValidationRule(
        field_name="email",
        required=True,
        pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"
    ),
]

# Validate input
data = {"username": "testuser", "email": "test@example.com"}
is_valid, errors, sanitized_data = security_service.validate_input(data, rules)

if is_valid:
    # Use sanitized_data
    print(f"Valid input: {sanitized_data}")
else:
    # Handle errors
    print(f"Validation errors: {errors}")
```

**Detected Attack Patterns:**

1. **SQL Injection:**
   - `'; DROP TABLE users; --`
   - `1' OR '1'='1`
   - `UNION SELECT * FROM passwords`

2. **XSS:**
   - `<script>alert('xss')</script>`
   - `javascript:alert('xss')`
   - `<img src=x onerror=alert('xss')>`

3. **Path Traversal:**
   - `../../../etc/passwd`
   - `..\\..\\..\\windows\\system32`

4. **Command Injection:**
   - `test; rm -rf /`
   - `test && cat /etc/passwd`
   - `$(whoami)`

### 2. CSRF Protection (Requirement 15.2)

**Purpose:** Prevent Cross-Site Request Forgery attacks.

**Features:**
- Token generation with cryptographic randomness
- Token validation with expiry
- Automatic token cleanup
- Session-based token management

**Usage Example:**

```python
from services.security_service import get_security_service

security_service = get_security_service()

# Generate CSRF token
token = security_service.generate_csrf_token(session_id="user_session_123")

# Include token in response headers or body
response.headers["X-CSRF-Token"] = token

# Validate token on subsequent requests
is_valid = security_service.validate_csrf_token(token)
if not is_valid:
    raise HTTPException(status_code=403, detail="Invalid CSRF token")
```

**Protected Endpoints:**

The following endpoints require CSRF tokens for POST/PUT/DELETE/PATCH requests:
- `/api/credentials`
- `/api/platforms/connect`
- `/api/training/start`
- `/api/deployment/deploy`
- `/api/config/export`
- `/api/config/import`

**Token Lifecycle:**
- Tokens expire after 1 hour (3600 seconds)
- Tokens are invalidated after use (optional)
- Expired tokens are automatically cleaned up

### 3. Rate Limiting (Requirement 15.3)

**Purpose:** Prevent abuse and DoS attacks through request throttling.

**Features:**
- Per-IP rate limiting
- Multiple time windows (minute, hour, day)
- Burst protection
- Automatic IP blocking for excessive violations
- Configurable limits

**Default Limits:**

```python
RateLimitConfig(
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000,
    burst_size=10  # Max requests in 10 seconds
)
```

**Usage Example:**

```python
from services.security_service import get_security_service

security_service = get_security_service()

# Check rate limit
client_ip = request.client.host
is_allowed, reason = security_service.check_rate_limit(client_ip, endpoint="/api/data")

if not is_allowed:
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded", "message": reason}
    )
```

**Behavior:**
- First violation: Request blocked with 429 status
- Repeated violations: IP temporarily blocked for 1 hour
- Per-IP isolation: Each IP has independent limits
- Exempt endpoints: Health checks and root endpoint

### 4. Secure Headers (Requirement 15.4)

**Purpose:** Protect against common web vulnerabilities through HTTP headers.

**Implemented Headers:**

```python
{
    # Prevent clickjacking
    "X-Frame-Options": "DENY",
    
    # Prevent MIME type sniffing
    "X-Content-Type-Options": "nosniff",
    
    # Enable XSS protection
    "X-XSS-Protection": "1; mode=block",
    
    # Enforce HTTPS
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    
    # Content Security Policy
    "Content-Security-Policy": "default-src 'self'; ...",
    
    # Referrer Policy
    "Referrer-Policy": "strict-origin-when-cross-origin",
    
    # Permissions Policy
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), ..."
}
```

**Automatic Application:**

All security headers are automatically added to every HTTP response through the `SecurityMiddleware`.

### 5. Security Audit Logging (Requirement 15.5)

**Purpose:** Track security-relevant events for monitoring and forensics.

**Logged Events:**

- `LOGIN_ATTEMPT` / `LOGIN_SUCCESS` / `LOGIN_FAILURE`
- `CREDENTIAL_ACCESS` / `CREDENTIAL_CREATED` / `CREDENTIAL_UPDATED` / `CREDENTIAL_DELETED`
- `API_KEY_CREATED` / `API_KEY_REVOKED`
- `RATE_LIMIT_EXCEEDED`
- `INVALID_INPUT`
- `CSRF_TOKEN_MISMATCH`
- `SUSPICIOUS_ACTIVITY`
- `PERMISSION_DENIED`
- `DATA_EXPORT` / `DATA_IMPORT`
- `CONFIGURATION_CHANGE`

**Event Structure:**

```python
SecurityEvent(
    event_type=SecurityEventType.LOGIN_SUCCESS,
    severity=SecurityEventSeverity.INFO,
    timestamp=datetime.utcnow(),
    user_id="user123",
    ip_address="192.168.1.1",
    endpoint="/api/login",
    details={"method": "POST", "status_code": 200},
    success=True
)
```

**Usage Example:**

```python
from services.security_service import (
    get_security_service,
    SecurityEventType,
    SecurityEventSeverity
)

security_service = get_security_service()

# Log security event
security_service.log_security_event(
    event_type=SecurityEventType.LOGIN_SUCCESS,
    severity=SecurityEventSeverity.INFO,
    user_id="user123",
    ip_address="192.168.1.1",
    endpoint="/api/login",
    details={"method": "POST"},
    success=True
)

# Query audit log
events = security_service.get_audit_events(
    event_type=SecurityEventType.LOGIN_FAILURE,
    start_time=datetime.utcnow() - timedelta(hours=1),
    limit=100
)

# Detect suspicious activity
suspicious = security_service.get_suspicious_activity(time_window_minutes=60)
```

**Suspicious Activity Detection:**

The system automatically detects:
- Multiple failed login attempts (≥5 in time window)
- Excessive rate limit violations (≥10 in time window)
- Excessive invalid input attempts (≥20 in time window)

**Log Storage:**

- In-memory buffer: Last 1000 events
- File storage: `backend/data/security_audit.log` (JSON lines format)
- Standard logging: Python logging system

## Middleware Integration

### SecurityMiddleware

Applied to all requests, provides:
1. Rate limiting (except exempt endpoints)
2. CSRF validation for state-changing operations
3. Security headers on all responses
4. Audit logging for sensitive operations

### InputValidationMiddleware

Applied to POST/PUT/PATCH requests, provides:
1. Payload size validation (max 10MB)
2. Content-type validation
3. Automatic logging of validation failures

## API Endpoints

### GET /api/security/csrf-token

Generate a CSRF token for the current session.

**Response:**
```json
{
  "token": "abc123...",
  "expires_in_seconds": 3600
}
```

### POST /api/security/validate-input

Validate and sanitize input data.

**Request:**
```json
{
  "data": {"username": "testuser", "email": "test@example.com"},
  "rules": [
    {"field_name": "username", "required": true, "min_length": 3},
    {"field_name": "email", "required": true, "pattern": "^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"}
  ]
}
```

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "sanitized_data": {"username": "testuser", "email": "test@example.com"}
}
```

### GET /api/security/audit-log

Query security audit log.

**Parameters:**
- `event_type` (optional): Filter by event type
- `severity` (optional): Filter by severity
- `user_id` (optional): Filter by user
- `start_time` (optional): Start of time range
- `end_time` (optional): End of time range
- `limit` (default: 100): Maximum events to return

**Response:**
```json
[
  {
    "event_type": "login_success",
    "severity": "info",
    "timestamp": "2024-01-01T12:00:00",
    "user_id": "user123",
    "ip_address": "192.168.1.1",
    "endpoint": "/api/login",
    "details": {"method": "POST"},
    "success": true
  }
]
```

### GET /api/security/suspicious-activity

Detect suspicious activity patterns.

**Parameters:**
- `time_window_minutes` (default: 60): Time window for detection

**Response:**
```json
[
  {
    "type": "multiple_failed_logins",
    "ip_address": "192.168.1.100",
    "count": 10,
    "severity": "high"
  }
]
```

### GET /api/security/rate-limit-status

Get current rate limit status for the client.

**Response:**
```json
{
  "ip_address": "192.168.1.1",
  "is_allowed": true,
  "reason": null,
  "limits": {
    "requests_per_minute": 60,
    "requests_per_hour": 1000,
    "requests_per_day": 10000,
    "burst_size": 10
  }
}
```

### POST /api/security/rate-limit/reset

Reset rate limit for an IP address (admin only).

**Parameters:**
- `ip_address` (optional): IP to reset, defaults to client IP

**Response:**
```json
{
  "message": "Rate limit reset for IP: 192.168.1.1"
}
```

### GET /api/security/headers

Get recommended security headers.

**Response:**
```json
{
  "headers": {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    ...
  },
  "description": "These headers should be set on all HTTP responses for security"
}
```

## Configuration

### Rate Limit Configuration

Customize rate limits by modifying the `RateLimitConfig`:

```python
from services.security_service import SecurityService, RateLimitConfig

config = RateLimitConfig(
    requests_per_minute=100,  # Increase for high-traffic
    requests_per_hour=5000,
    requests_per_day=50000,
    burst_size=20
)

security_service = SecurityService(rate_limit_config=config)
```

### Audit Log Configuration

Configure audit log file location:

```python
from services.security_service import SecurityService

security_service = SecurityService(
    audit_log_file="/path/to/security_audit.log"
)
```

### CSRF Token Expiry

Configure CSRF token expiry:

```python
from services.security_service import CSRFProtection

csrf = CSRFProtection(token_expiry_seconds=7200)  # 2 hours
```

## Testing

Comprehensive test suite in `backend/tests/test_security_best_practices.py`:

- **35 tests** covering all security features
- **100% requirement coverage** for Requirements 15.1-15.5
- Tests for attack detection (SQL injection, XSS, path traversal, command injection)
- Tests for rate limiting behavior
- Tests for CSRF token lifecycle
- Tests for audit logging and suspicious activity detection
- Tests for security headers

Run tests:
```bash
pytest backend/tests/test_security_best_practices.py -v
```

## Best Practices

### For Developers

1. **Always validate user input:**
   ```python
   rules = [ValidationRule(field_name="input", required=True, max_length=100)]
   is_valid, errors, sanitized = security_service.validate_input(data, rules)
   ```

2. **Use CSRF tokens for state-changing operations:**
   ```python
   token = security_service.generate_csrf_token(session_id)
   # Include in response, validate on next request
   ```

3. **Log security-relevant events:**
   ```python
   security_service.log_security_event(
       event_type=SecurityEventType.CREDENTIAL_ACCESS,
       severity=SecurityEventSeverity.INFO,
       user_id=user_id,
       ip_address=client_ip
   )
   ```

4. **Check rate limits for sensitive operations:**
   ```python
   is_allowed, reason = security_service.check_rate_limit(client_ip)
   if not is_allowed:
       raise HTTPException(status_code=429, detail=reason)
   ```

### For Operations

1. **Monitor audit logs regularly:**
   ```bash
   tail -f backend/data/security_audit.log
   ```

2. **Check for suspicious activity:**
   ```bash
   curl http://localhost:8000/api/security/suspicious-activity
   ```

3. **Review rate limit violations:**
   ```bash
   curl http://localhost:8000/api/security/audit-log?event_type=rate_limit_exceeded
   ```

4. **Reset rate limits when needed:**
   ```bash
   curl -X POST http://localhost:8000/api/security/rate-limit/reset?ip_address=192.168.1.1
   ```

## Security Considerations

### Known Limitations

1. **In-memory rate limiting:** Rate limits reset on application restart. For production, consider Redis-backed rate limiting.

2. **CSRF token storage:** Tokens stored in memory. For distributed systems, use shared storage (Redis, database).

3. **Audit log rotation:** Implement log rotation for production to prevent disk space issues.

4. **IP-based rate limiting:** Can be bypassed with multiple IPs. Consider user-based rate limiting for authenticated endpoints.

### Recommendations

1. **Use HTTPS in production:** Security headers assume HTTPS is used.

2. **Implement authentication:** Current implementation focuses on request-level security. Add user authentication for complete security.

3. **Regular security audits:** Review audit logs and suspicious activity reports regularly.

4. **Update dependencies:** Keep security-related dependencies up to date.

5. **Penetration testing:** Conduct regular penetration testing to identify vulnerabilities.

## Compliance

This implementation helps meet common security compliance requirements:

- **OWASP Top 10:** Addresses injection, XSS, CSRF, security misconfiguration
- **PCI DSS:** Audit logging, input validation, secure headers
- **GDPR:** Audit trails for data access and modifications
- **SOC 2:** Security monitoring and logging

## Troubleshooting

### Rate Limit Issues

**Problem:** Legitimate users getting rate limited.

**Solution:**
1. Check current limits: `GET /api/security/rate-limit-status`
2. Increase limits in configuration
3. Reset specific IP: `POST /api/security/rate-limit/reset`

### CSRF Token Issues

**Problem:** CSRF token validation failing.

**Solution:**
1. Ensure token is included in `X-CSRF-Token` header
2. Check token hasn't expired (1 hour default)
3. Generate new token: `GET /api/security/csrf-token`

### Audit Log Issues

**Problem:** Audit log file growing too large.

**Solution:**
1. Implement log rotation
2. Archive old logs
3. Reduce retention period

## Future Enhancements

1. **Redis integration:** For distributed rate limiting and CSRF tokens
2. **User-based rate limiting:** In addition to IP-based
3. **Anomaly detection:** ML-based detection of unusual patterns
4. **Automated blocking:** Automatic IP blocking based on threat score
5. **Security dashboard:** Real-time security monitoring UI
6. **Webhook notifications:** Alert on critical security events
7. **Two-factor authentication:** Additional authentication layer
8. **API key management:** Secure API key generation and rotation

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
