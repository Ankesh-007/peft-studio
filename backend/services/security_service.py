"""
Security Service

Implements comprehensive security best practices:
- Input validation and sanitization
- CSRF protection
- Rate limiting
- Secure headers
- Security audit logging

Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5
"""

import re
import hashlib
import secrets
import time
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import logging
import html
import json

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Types of security events to log"""
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    CREDENTIAL_ACCESS = "credential_access"
    CREDENTIAL_CREATED = "credential_created"
    CREDENTIAL_UPDATED = "credential_updated"
    CREDENTIAL_DELETED = "credential_deleted"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_INPUT = "invalid_input"
    CSRF_TOKEN_MISMATCH = "csrf_token_mismatch"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PERMISSION_DENIED = "permission_denied"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    CONFIGURATION_CHANGE = "configuration_change"


class SecurityEventSeverity(Enum):
    """Severity levels for security events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event for audit logging"""
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    timestamp: datetime
    user_id: Optional[str]
    ip_address: Optional[str]
    endpoint: Optional[str]
    details: Dict[str, Any]
    success: bool


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10  # Allow short bursts


@dataclass
class ValidationRule:
    """Input validation rule"""
    field_name: str
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    sanitize: bool = True


class InputValidator:
    """Input validation and sanitization"""
    
    # Common dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
        r"\.\.\\",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\(",
        r"`.*`",
        r"\|\|",
        r"&&",
    ]
    
    def __init__(self):
        self.sql_regex = re.compile("|".join(self.SQL_INJECTION_PATTERNS), re.IGNORECASE)
        self.xss_regex = re.compile("|".join(self.XSS_PATTERNS), re.IGNORECASE)
        self.path_regex = re.compile("|".join(self.PATH_TRAVERSAL_PATTERNS), re.IGNORECASE)
        self.cmd_regex = re.compile("|".join(self.COMMAND_INJECTION_PATTERNS))
    
    def sanitize_string(self, value: str) -> str:
        """
        Sanitize a string by escaping HTML and removing dangerous characters.
        
        Validates: Requirement 15.1 - Input validation and sanitization
        """
        if not isinstance(value, str):
            return str(value)
        
        # HTML escape
        sanitized = html.escape(value)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    def validate_string(self, value: str, rule: ValidationRule) -> tuple[bool, Optional[str]]:
        """
        Validate a string against a validation rule.
        
        Returns: (is_valid, error_message)
        """
        if rule.required and not value:
            return False, f"{rule.field_name} is required"
        
        if not value and not rule.required:
            return True, None
        
        # Length validation
        if rule.min_length and len(value) < rule.min_length:
            return False, f"{rule.field_name} must be at least {rule.min_length} characters"
        
        if rule.max_length and len(value) > rule.max_length:
            return False, f"{rule.field_name} must be at most {rule.max_length} characters"
        
        # Pattern validation
        if rule.pattern:
            if not re.match(rule.pattern, value):
                return False, f"{rule.field_name} format is invalid"
        
        # Allowed values
        if rule.allowed_values and value not in rule.allowed_values:
            return False, f"{rule.field_name} must be one of: {', '.join(rule.allowed_values)}"
        
        # Security checks
        if self.sql_regex.search(value):
            return False, f"{rule.field_name} contains potentially dangerous SQL patterns"
        
        if self.xss_regex.search(value):
            return False, f"{rule.field_name} contains potentially dangerous XSS patterns"
        
        if self.path_regex.search(value):
            return False, f"{rule.field_name} contains path traversal patterns"
        
        if self.cmd_regex.search(value):
            return False, f"{rule.field_name} contains command injection patterns"
        
        return True, None
    
    def validate_dict(self, data: Dict[str, Any], rules: List[ValidationRule]) -> tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate and sanitize a dictionary of data.
        
        Returns: (is_valid, errors, sanitized_data)
        """
        errors = []
        sanitized = {}
        
        for rule in rules:
            value = data.get(rule.field_name)
            
            if value is None:
                if rule.required:
                    errors.append(f"{rule.field_name} is required")
                continue
            
            # Validate
            if isinstance(value, str):
                is_valid, error = self.validate_string(value, rule)
                if not is_valid:
                    errors.append(error)
                    continue
                
                # Sanitize if needed
                if rule.sanitize:
                    sanitized[rule.field_name] = self.sanitize_string(value)
                else:
                    sanitized[rule.field_name] = value
            else:
                # Non-string values pass through
                sanitized[rule.field_name] = value
        
        return len(errors) == 0, errors, sanitized


class CSRFProtection:
    """CSRF token management"""
    
    def __init__(self, token_expiry_seconds: int = 3600):
        self.token_expiry_seconds = token_expiry_seconds
        self.tokens: Dict[str, datetime] = {}
    
    def generate_token(self, session_id: str) -> str:
        """
        Generate a CSRF token for a session.
        
        Validates: Requirement 15.2 - CSRF protection
        """
        token = secrets.token_urlsafe(32)
        self.tokens[token] = datetime.utcnow()
        return token
    
    def validate_token(self, token: str) -> bool:
        """
        Validate a CSRF token.
        
        Returns: True if token is valid and not expired
        """
        if token not in self.tokens:
            return False
        
        created_at = self.tokens[token]
        age = (datetime.utcnow() - created_at).total_seconds()
        
        if age > self.token_expiry_seconds:
            # Token expired
            del self.tokens[token]
            return False
        
        return True
    
    def invalidate_token(self, token: str):
        """Invalidate a CSRF token after use"""
        if token in self.tokens:
            del self.tokens[token]
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens"""
        now = datetime.utcnow()
        expired = [
            token for token, created_at in self.tokens.items()
            if (now - created_at).total_seconds() > self.token_expiry_seconds
        ]
        for token in expired:
            del self.tokens[token]


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.blocked_ips: Dict[str, datetime] = {}
    
    def is_allowed(self, identifier: str, endpoint: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Check if a request is allowed based on rate limits.
        
        Validates: Requirement 15.3 - Rate limiting
        
        Returns: (is_allowed, reason)
        """
        now = time.time()
        
        # Check if IP is blocked
        if identifier in self.blocked_ips:
            block_until = self.blocked_ips[identifier]
            if datetime.utcnow() < block_until:
                return False, "IP temporarily blocked due to rate limit violations"
            else:
                del self.blocked_ips[identifier]
        
        # Get request history
        request_times = self.requests[identifier]
        
        # Remove old requests
        minute_ago = now - 60
        hour_ago = now - 3600
        day_ago = now - 86400
        
        request_times = [t for t in request_times if t > day_ago]
        self.requests[identifier] = request_times
        
        # Count requests in different time windows
        requests_last_minute = sum(1 for t in request_times if t > minute_ago)
        requests_last_hour = sum(1 for t in request_times if t > hour_ago)
        requests_last_day = len(request_times)
        
        # Check limits
        if requests_last_minute >= self.config.requests_per_minute:
            return False, f"Rate limit exceeded: {self.config.requests_per_minute} requests per minute"
        
        if requests_last_hour >= self.config.requests_per_hour:
            return False, f"Rate limit exceeded: {self.config.requests_per_hour} requests per hour"
        
        if requests_last_day >= self.config.requests_per_day:
            # Block for 1 hour
            self.blocked_ips[identifier] = datetime.utcnow() + timedelta(hours=1)
            return False, f"Rate limit exceeded: {self.config.requests_per_day} requests per day. IP blocked for 1 hour."
        
        # Check burst protection
        recent_requests = sum(1 for t in request_times if t > now - 10)
        if recent_requests >= self.config.burst_size:
            return False, f"Burst limit exceeded: {self.config.burst_size} requests in 10 seconds"
        
        # Record this request
        request_times.append(now)
        
        return True, None
    
    def reset(self, identifier: str):
        """Reset rate limit for an identifier"""
        if identifier in self.requests:
            del self.requests[identifier]
        if identifier in self.blocked_ips:
            del self.blocked_ips[identifier]


class SecurityAuditLogger:
    """Security audit logging"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.events: List[SecurityEvent] = []
        self.max_events_in_memory = 1000
    
    def log_event(self, event: SecurityEvent):
        """
        Log a security event.
        
        Validates: Requirement 15.5 - Security audit logging
        """
        # Add to in-memory buffer
        self.events.append(event)
        
        # Trim if too large
        if len(self.events) > self.max_events_in_memory:
            self.events = self.events[-self.max_events_in_memory:]
        
        # Log to file
        if self.log_file:
            self._write_to_file(event)
        
        # Log to standard logger
        log_level = {
            SecurityEventSeverity.INFO: logging.INFO,
            SecurityEventSeverity.WARNING: logging.WARNING,
            SecurityEventSeverity.ERROR: logging.ERROR,
            SecurityEventSeverity.CRITICAL: logging.CRITICAL,
        }[event.severity]
        
        logger.log(
            log_level,
            f"Security Event: {event.event_type.value} - "
            f"User: {event.user_id or 'unknown'} - "
            f"IP: {event.ip_address or 'unknown'} - "
            f"Success: {event.success} - "
            f"Details: {json.dumps(event.details)}"
        )
    
    def _write_to_file(self, event: SecurityEvent):
        """Write event to audit log file"""
        try:
            with open(self.log_file, 'a') as f:
                log_entry = {
                    'timestamp': event.timestamp.isoformat(),
                    'event_type': event.event_type.value,
                    'severity': event.severity.value,
                    'user_id': event.user_id,
                    'ip_address': event.ip_address,
                    'endpoint': event.endpoint,
                    'success': event.success,
                    'details': event.details
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to audit log: {e}")
    
    def get_events(
        self,
        event_type: Optional[SecurityEventType] = None,
        severity: Optional[SecurityEventSeverity] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """Query security events with filters"""
        filtered = self.events
        
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        
        if severity:
            filtered = [e for e in filtered if e.severity == severity]
        
        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]
        
        if start_time:
            filtered = [e for e in filtered if e.timestamp >= start_time]
        
        if end_time:
            filtered = [e for e in filtered if e.timestamp <= end_time]
        
        # Return most recent first
        filtered.sort(key=lambda e: e.timestamp, reverse=True)
        
        return filtered[:limit]
    
    def get_suspicious_activity(self, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Detect suspicious activity patterns.
        
        Returns list of suspicious patterns found.
        """
        cutoff = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        recent_events = [e for e in self.events if e.timestamp >= cutoff]
        
        suspicious = []
        
        # Multiple failed login attempts
        failed_logins = defaultdict(int)
        for event in recent_events:
            if event.event_type == SecurityEventType.LOGIN_FAILURE:
                failed_logins[event.ip_address or 'unknown'] += 1
        
        for ip, count in failed_logins.items():
            if count >= 5:
                suspicious.append({
                    'type': 'multiple_failed_logins',
                    'ip_address': ip,
                    'count': count,
                    'severity': 'high'
                })
        
        # Multiple rate limit violations
        rate_limit_violations = defaultdict(int)
        for event in recent_events:
            if event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED:
                rate_limit_violations[event.ip_address or 'unknown'] += 1
        
        for ip, count in rate_limit_violations.items():
            if count >= 10:
                suspicious.append({
                    'type': 'excessive_rate_limit_violations',
                    'ip_address': ip,
                    'count': count,
                    'severity': 'medium'
                })
        
        # Multiple invalid input attempts
        invalid_inputs = defaultdict(int)
        for event in recent_events:
            if event.event_type == SecurityEventType.INVALID_INPUT:
                invalid_inputs[event.ip_address or 'unknown'] += 1
        
        for ip, count in invalid_inputs.items():
            if count >= 20:
                suspicious.append({
                    'type': 'excessive_invalid_inputs',
                    'ip_address': ip,
                    'count': count,
                    'severity': 'medium'
                })
        
        return suspicious


class SecurityHeadersManager:
    """Manage security headers for HTTP responses"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get recommended security headers.
        
        Validates: Requirement 15.4 - Secure headers
        """
        return {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none';"
            ),
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions Policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),
        }


class SecurityService:
    """Main security service coordinating all security features"""
    
    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        audit_log_file: Optional[str] = None
    ):
        self.validator = InputValidator()
        self.csrf = CSRFProtection()
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        self.audit_logger = SecurityAuditLogger(audit_log_file)
        self.headers_manager = SecurityHeadersManager()
    
    def validate_input(
        self,
        data: Dict[str, Any],
        rules: List[ValidationRule]
    ) -> tuple[bool, List[str], Dict[str, Any]]:
        """Validate and sanitize input data"""
        return self.validator.validate_dict(data, rules)
    
    def check_rate_limit(
        self,
        identifier: str,
        endpoint: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """Check if request is within rate limits"""
        return self.rate_limiter.is_allowed(identifier, endpoint)
    
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token"""
        return self.csrf.generate_token(session_id)
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token"""
        return self.csrf.validate_token(token)
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers"""
        return self.headers_manager.get_security_headers()
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: SecurityEventSeverity,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        endpoint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ):
        """Log a security event"""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            ip_address=ip_address,
            endpoint=endpoint,
            details=details or {},
            success=success
        )
        self.audit_logger.log_event(event)
    
    def get_audit_events(
        self,
        event_type: Optional[SecurityEventType] = None,
        severity: Optional[SecurityEventSeverity] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """Query audit events"""
        return self.audit_logger.get_events(
            event_type, severity, user_id, start_time, end_time, limit
        )
    
    def get_suspicious_activity(self, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        """Detect suspicious activity"""
        return self.audit_logger.get_suspicious_activity(time_window_minutes)


# Global security service instance
_security_service: Optional[SecurityService] = None


def get_security_service() -> SecurityService:
    """Get or create the global security service instance"""
    global _security_service
    if _security_service is None:
        from pathlib import Path
        audit_log_path = Path(__file__).parent.parent / "data" / "security_audit.log"
        _security_service = SecurityService(audit_log_file=str(audit_log_path))
    return _security_service
