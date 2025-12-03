"""
Security Middleware for FastAPI

Integrates security features into the FastAPI application:
- Rate limiting
- Security headers
- Audit logging
- Input validation

Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5
"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from typing import Callable

from services.security_service import (
    get_security_service,
    SecurityEventType,
    SecurityEventSeverity
)

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies security measures to all requests.
    
    Features:
    - Rate limiting per IP address
    - Security headers on all responses
    - Audit logging for sensitive operations
    - Request/response timing
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_service = get_security_service()
        
        # Endpoints that require CSRF protection
        self.csrf_protected_endpoints = {
            "/api/credentials",
            "/api/platforms/connect",
            "/api/training/start",
            "/api/deployment/deploy",
            "/api/config/export",
            "/api/config/import",
        }
        
        # Endpoints that should be audit logged
        self.audit_logged_endpoints = {
            "/api/credentials",
            "/api/platforms/connect",
            "/api/training/start",
            "/api/deployment/deploy",
            "/api/models/upload",
            "/api/config/export",
            "/api/config/import",
        }
        
        # Endpoints exempt from rate limiting (health checks, etc.)
        self.rate_limit_exempt = {
            "/api/health",
            "/",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware"""
        start_time = time.time()
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path
        method = request.method
        
        try:
            # 1. Rate Limiting (except for exempt endpoints)
            if endpoint not in self.rate_limit_exempt:
                is_allowed, reason = self.security_service.check_rate_limit(
                    client_ip, endpoint
                )
                
                if not is_allowed:
                    # Log rate limit violation
                    self.security_service.log_security_event(
                        event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                        severity=SecurityEventSeverity.WARNING,
                        ip_address=client_ip,
                        endpoint=endpoint,
                        details={'reason': reason, 'method': method},
                        success=False
                    )
                    
                    return JSONResponse(
                        status_code=429,
                        content={
                            'error': 'Rate limit exceeded',
                            'message': reason
                        }
                    )
            
            # 2. CSRF Protection for state-changing operations
            if method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                if any(endpoint.startswith(protected) for protected in self.csrf_protected_endpoints):
                    csrf_token = request.headers.get('X-CSRF-Token')
                    
                    if not csrf_token or not self.security_service.validate_csrf_token(csrf_token):
                        # Log CSRF token mismatch
                        self.security_service.log_security_event(
                            event_type=SecurityEventType.CSRF_TOKEN_MISMATCH,
                            severity=SecurityEventSeverity.ERROR,
                            ip_address=client_ip,
                            endpoint=endpoint,
                            details={'method': method},
                            success=False
                        )
                        
                        return JSONResponse(
                            status_code=403,
                            content={
                                'error': 'CSRF token validation failed',
                                'message': 'Invalid or missing CSRF token'
                            }
                        )
            
            # 3. Process request
            response = await call_next(request)
            
            # 4. Add security headers
            security_headers = self.security_service.get_security_headers()
            for header_name, header_value in security_headers.items():
                response.headers[header_name] = header_value
            
            # 5. Audit logging for sensitive operations
            if any(endpoint.startswith(logged) for logged in self.audit_logged_endpoints):
                duration = time.time() - start_time
                
                # Determine event type based on endpoint
                event_type = self._determine_event_type(endpoint, method)
                severity = SecurityEventSeverity.INFO if response.status_code < 400 else SecurityEventSeverity.WARNING
                
                self.security_service.log_security_event(
                    event_type=event_type,
                    severity=severity,
                    ip_address=client_ip,
                    endpoint=endpoint,
                    details={
                        'method': method,
                        'status_code': response.status_code,
                        'duration_ms': round(duration * 1000, 2)
                    },
                    success=response.status_code < 400
                )
            
            return response
            
        except HTTPException as e:
            # Log HTTP exceptions
            self.security_service.log_security_event(
                event_type=SecurityEventType.PERMISSION_DENIED if e.status_code == 403 else SecurityEventType.SUSPICIOUS_ACTIVITY,
                severity=SecurityEventSeverity.WARNING,
                ip_address=client_ip,
                endpoint=endpoint,
                details={
                    'method': method,
                    'status_code': e.status_code,
                    'detail': e.detail
                },
                success=False
            )
            raise
            
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in security middleware: {e}", exc_info=True)
            
            self.security_service.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                severity=SecurityEventSeverity.ERROR,
                ip_address=client_ip,
                endpoint=endpoint,
                details={
                    'method': method,
                    'error': str(e)
                },
                success=False
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    'error': 'Internal server error',
                    'message': 'An unexpected error occurred'
                }
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return 'unknown'
    
    def _determine_event_type(self, endpoint: str, method: str) -> SecurityEventType:
        """Determine security event type based on endpoint and method"""
        if '/credentials' in endpoint:
            if method == 'POST':
                return SecurityEventType.CREDENTIAL_CREATED
            elif method == 'PUT':
                return SecurityEventType.CREDENTIAL_UPDATED
            elif method == 'DELETE':
                return SecurityEventType.CREDENTIAL_DELETED
            else:
                return SecurityEventType.CREDENTIAL_ACCESS
        
        elif '/platforms/connect' in endpoint:
            return SecurityEventType.LOGIN_ATTEMPT
        
        elif '/config/export' in endpoint:
            return SecurityEventType.DATA_EXPORT
        
        elif '/config/import' in endpoint:
            return SecurityEventType.DATA_IMPORT
        
        elif '/training/start' in endpoint or '/deployment/deploy' in endpoint:
            return SecurityEventType.CONFIGURATION_CHANGE
        
        else:
            return SecurityEventType.SUSPICIOUS_ACTIVITY


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic input validation on POST/PUT requests.
    
    Validates: Requirement 15.1 - Input validation and sanitization
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_service = get_security_service()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request input"""
        
        # Only validate POST/PUT/PATCH requests with JSON body
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                try:
                    # Read body
                    body = await request.body()
                    
                    # Basic validation: check for excessively large payloads
                    max_body_size = 10 * 1024 * 1024  # 10MB
                    if len(body) > max_body_size:
                        client_ip = request.client.host if request.client else 'unknown'
                        
                        self.security_service.log_security_event(
                            event_type=SecurityEventType.INVALID_INPUT,
                            severity=SecurityEventSeverity.WARNING,
                            ip_address=client_ip,
                            endpoint=request.url.path,
                            details={
                                'reason': 'payload_too_large',
                                'size_bytes': len(body)
                            },
                            success=False
                        )
                        
                        return JSONResponse(
                            status_code=413,
                            content={
                                'error': 'Payload too large',
                                'message': f'Request body exceeds maximum size of {max_body_size} bytes'
                            }
                        )
                    
                    # Reconstruct request with validated body
                    # (FastAPI will handle JSON parsing and Pydantic validation)
                    
                except Exception as e:
                    logger.error(f"Error validating input: {e}")
        
        # Continue processing
        response = await call_next(request)
        return response
