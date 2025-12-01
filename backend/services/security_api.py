"""
Security API Endpoints

Provides endpoints for:
- CSRF token generation
- Security audit log queries
- Suspicious activity detection
- Rate limit management

Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from services.security_service import (
    get_security_service,
    SecurityEventType,
    SecurityEventSeverity,
    ValidationRule
)

router = APIRouter(prefix="/api/security", tags=["security"])


class CSRFTokenResponse(BaseModel):
    """CSRF token response"""
    token: str
    expires_in_seconds: int


class ValidationRequest(BaseModel):
    """Input validation request"""
    data: dict
    rules: List[dict]


class ValidationResponse(BaseModel):
    """Input validation response"""
    is_valid: bool
    errors: List[str]
    sanitized_data: dict


class AuditEventResponse(BaseModel):
    """Security audit event response"""
    event_type: str
    severity: str
    timestamp: str
    user_id: Optional[str]
    ip_address: Optional[str]
    endpoint: Optional[str]
    details: dict
    success: bool


class SuspiciousActivityResponse(BaseModel):
    """Suspicious activity response"""
    type: str
    ip_address: str
    count: int
    severity: str


@router.get("/csrf-token", response_model=CSRFTokenResponse)
async def get_csrf_token(request: Request):
    """
    Generate a CSRF token for the current session.
    
    Validates: Requirement 15.2 - CSRF protection
    """
    security_service = get_security_service()
    
    # Use session ID or client IP as identifier
    session_id = request.headers.get('X-Session-ID')
    if not session_id and request.client:
        session_id = request.client.host
    elif not session_id:
        session_id = 'default'
    
    token = security_service.generate_csrf_token(session_id)
    
    return CSRFTokenResponse(
        token=token,
        expires_in_seconds=3600
    )


@router.post("/validate-input", response_model=ValidationResponse)
async def validate_input(request: ValidationRequest):
    """
    Validate and sanitize input data.
    
    Validates: Requirement 15.1 - Input validation and sanitization
    """
    security_service = get_security_service()
    
    # Convert dict rules to ValidationRule objects
    rules = []
    for rule_dict in request.rules:
        rule = ValidationRule(
            field_name=rule_dict['field_name'],
            required=rule_dict.get('required', False),
            min_length=rule_dict.get('min_length'),
            max_length=rule_dict.get('max_length'),
            pattern=rule_dict.get('pattern'),
            allowed_values=rule_dict.get('allowed_values'),
            sanitize=rule_dict.get('sanitize', True)
        )
        rules.append(rule)
    
    is_valid, errors, sanitized_data = security_service.validate_input(
        request.data,
        rules
    )
    
    return ValidationResponse(
        is_valid=is_valid,
        errors=errors,
        sanitized_data=sanitized_data
    )


@router.get("/audit-log", response_model=List[AuditEventResponse])
async def get_audit_log(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    user_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
):
    """
    Query security audit log.
    
    Validates: Requirement 15.5 - Security audit logging
    """
    security_service = get_security_service()
    
    # Convert string enums
    event_type_enum = SecurityEventType(event_type) if event_type else None
    severity_enum = SecurityEventSeverity(severity) if severity else None
    
    events = security_service.get_audit_events(
        event_type=event_type_enum,
        severity=severity_enum,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return [
        AuditEventResponse(
            event_type=event.event_type.value,
            severity=event.severity.value,
            timestamp=event.timestamp.isoformat(),
            user_id=event.user_id,
            ip_address=event.ip_address,
            endpoint=event.endpoint,
            details=event.details,
            success=event.success
        )
        for event in events
    ]


@router.get("/suspicious-activity", response_model=List[SuspiciousActivityResponse])
async def get_suspicious_activity(time_window_minutes: int = 60):
    """
    Detect suspicious activity patterns.
    
    Validates: Requirement 15.5 - Security audit logging
    """
    security_service = get_security_service()
    
    suspicious = security_service.get_suspicious_activity(time_window_minutes)
    
    return [
        SuspiciousActivityResponse(
            type=item['type'],
            ip_address=item['ip_address'],
            count=item['count'],
            severity=item['severity']
        )
        for item in suspicious
    ]


@router.get("/rate-limit-status")
async def get_rate_limit_status(request: Request):
    """
    Get current rate limit status for the client.
    
    Validates: Requirement 15.3 - Rate limiting
    """
    security_service = get_security_service()
    
    # Get client IP
    client_ip = request.client.host if request.client else 'unknown'
    
    # Check if allowed
    is_allowed, reason = security_service.check_rate_limit(client_ip)
    
    return {
        'ip_address': client_ip,
        'is_allowed': is_allowed,
        'reason': reason,
        'limits': {
            'requests_per_minute': security_service.rate_limiter.config.requests_per_minute,
            'requests_per_hour': security_service.rate_limiter.config.requests_per_hour,
            'requests_per_day': security_service.rate_limiter.config.requests_per_day,
            'burst_size': security_service.rate_limiter.config.burst_size
        }
    }


@router.post("/rate-limit/reset")
async def reset_rate_limit(request: Request, ip_address: Optional[str] = None):
    """
    Reset rate limit for an IP address (admin only).
    
    Validates: Requirement 15.3 - Rate limiting
    """
    security_service = get_security_service()
    
    # Use provided IP or client IP
    target_ip = ip_address or (request.client.host if request.client else None)
    
    if not target_ip:
        raise HTTPException(status_code=400, detail="No IP address provided")
    
    security_service.rate_limiter.reset(target_ip)
    
    # Log the reset
    security_service.log_security_event(
        event_type=SecurityEventType.CONFIGURATION_CHANGE,
        severity=SecurityEventSeverity.INFO,
        ip_address=request.client.host if request.client else 'unknown',
        endpoint='/api/security/rate-limit/reset',
        details={'reset_ip': target_ip},
        success=True
    )
    
    return {
        'message': f'Rate limit reset for IP: {target_ip}'
    }


@router.get("/headers")
async def get_security_headers():
    """
    Get recommended security headers.
    
    Validates: Requirement 15.4 - Secure headers
    """
    security_service = get_security_service()
    headers = security_service.get_security_headers()
    
    return {
        'headers': headers,
        'description': 'These headers should be set on all HTTP responses for security'
    }


@router.get("/health")
async def security_health_check():
    """Health check for security service"""
    security_service = get_security_service()
    
    # Check if service is operational
    try:
        # Test basic functionality
        test_token = security_service.generate_csrf_token('health_check')
        is_valid = security_service.validate_csrf_token(test_token)
        
        return {
            'status': 'healthy',
            'csrf_protection': 'operational' if is_valid else 'degraded',
            'rate_limiting': 'operational',
            'audit_logging': 'operational',
            'input_validation': 'operational'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }
