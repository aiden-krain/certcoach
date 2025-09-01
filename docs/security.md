# Security Architecture and Implementation

## Overview

CertCoach implements a comprehensive security architecture to protect user data, prevent abuse, and ensure compliance with privacy regulations. This document outlines our security controls, threat model, and implementation details.

## Security Principles

### 1. Defense in Depth
- Multiple layers of security controls
- No single point of failure
- Principle of least privilege
- Zero-trust architecture

### 2. Data Protection
- Encryption at rest and in transit
- Minimal data collection
- Secure data processing
- Privacy by design

### 3. Access Control
- Multi-factor authentication
- Role-based access control (RBAC)
- Row-level security (RLS)
- Audit logging

## Threat Model

### Identified Threats

#### 1. Unauthorized Data Access
**Threat**: Attackers gaining access to user data or exam content
**Mitigation**:
- JWT-based authentication with short expiration
- Database-level encryption
- Row-level security policies
- API rate limiting

#### 2. Content Extraction/Abuse
**Threat**: Automated scraping of exam questions for redistribution
**Mitigation**:
- Rate limiting on question generation
- User behavior analysis
- CAPTCHA for suspicious activity
- Legal terms enforcement

#### 3. Exam Dump Creation
**Threat**: Users attempting to recreate real exam content
**Mitigation**:
- Similarity detection algorithms
- Human content review
- User reporting mechanisms
- Content quarantine system

#### 4. Data Breaches
**Threat**: External attackers accessing sensitive data
**Mitigation**:
- Network segmentation
- Encrypted storage
- Regular security audits
- Incident response procedures

#### 5. Privilege Escalation
**Threat**: Users gaining unauthorized access to admin functions
**Mitigation**:
- Strict RBAC implementation
- Regular permission audits
- Principle of least privilege
- Multi-factor authentication for admin accounts

## Authentication and Authorization

### JWT Authentication
```python
# JWT Configuration
JWT_SETTINGS = {
    "ALGORITHM": "RS256",  # RSA-based signing
    "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
    "REFRESH_TOKEN_EXPIRE_DAYS": 7,
    "ISSUER": "certcoach.com",
    "AUDIENCE": "certcoach-api",
    "REQUIRE_EXP": True,
    "VERIFY_SIGNATURE": True,
    "VERIFY_EXP": True,
    "VERIFY_NBF": True,
    "VERIFY_ISS": True,
    "VERIFY_AUD": True
}
```

### OAuth Integration
**Supported Providers**:
- GitHub OAuth 2.0
- Microsoft Azure AD
- Google Workspace (planned)

**OAuth Security**:
- PKCE (Proof Key for Code Exchange)
- State parameter validation
- Secure redirect URI validation
- Token refresh handling

### Role-Based Access Control

#### User Roles
```yaml
roles:
  student:
    permissions:
      - read:own_progress
      - read:study_materials
      - write:practice_attempts
      - write:notes
    
  instructor:
    permissions:
      - read:class_progress
      - read:student_analytics
      - write:assignments
      - manage:class_roster
    
  content_reviewer:
    permissions:
      - read:content_queue
      - write:content_approval
      - read:content_analytics
    
  admin:
    permissions:
      - read:all_data
      - write:user_management
      - write:system_config
      - manage:billing
```

## Data Protection

### Encryption Standards

#### At Rest
- **Database**: AES-256 encryption for all PII fields
- **File Storage**: Azure Storage Service Encryption (SSE)
- **Backups**: Encrypted with customer-managed keys
- **Logs**: Encrypted with platform-managed keys

#### In Transit
- **API Communication**: TLS 1.3 minimum
- **Database Connections**: Encrypted PostgreSQL connections
- **Internal Services**: mTLS for service-to-service communication
- **CDN**: HTTPS enforcement with HSTS

### Data Classification

#### Highly Sensitive
- User passwords (hashed with bcrypt)
- Payment information (tokenized via Stripe)
- Personal identification data
- Authentication tokens

#### Sensitive  
- User study progress and performance
- Practice attempt history
- User notes and annotations
- Email addresses and contact information

#### Internal
- System logs (anonymized)
- Performance metrics
- Usage analytics (aggregated)
- Content metadata

#### Public
- Published study materials
- Documentation
- Marketing content
- Public API specifications

### Row-Level Security (RLS)

```sql
-- Example RLS policy for user data isolation
CREATE POLICY user_data_isolation ON user_progress
    FOR ALL TO authenticated_users
    USING (user_id = current_user_id());

-- Instructor access to their students
CREATE POLICY instructor_student_access ON user_progress  
    FOR SELECT TO instructors
    USING (
        user_id IN (
            SELECT student_id FROM class_enrollments 
            WHERE instructor_id = current_user_id()
        )
    );
```

## API Security

### Rate Limiting
```python
# Rate limiting configuration
RATE_LIMITS = {
    "authentication": "5 per minute",
    "practice_session": "10 per minute", 
    "content_generation": "3 per minute",
    "user_registration": "2 per minute",
    "password_reset": "3 per hour",
    "admin_operations": "20 per minute"
}
```

### Input Validation
- Pydantic model validation for all endpoints
- SQL injection prevention through parameterized queries
- XSS prevention through output encoding
- File upload validation and scanning
- Request size limitations

### API Security Headers
```python
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'",
    "X-Content-Type-Options": "nosniff", 
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
```

## Abuse Prevention

### Content Generation Protection
```python
# Anti-abuse measures for content generation
class ContentGenerationGuard:
    def __init__(self):
        self.similarity_threshold = 0.8
        self.generation_limit_per_hour = 10
        self.suspicious_pattern_detector = SuspiciousPatternDetector()
    
    def validate_generation_request(self, user_id: str, request: ContentRequest) -> bool:
        # Check rate limits
        if self.check_rate_limit_exceeded(user_id):
            raise RateLimitExceeded()
        
        # Check for suspicious patterns
        if self.suspicious_pattern_detector.is_suspicious(request):
            self.flag_for_review(user_id, request)
            return False
        
        return True
```

### Behavioral Analysis
- Session duration monitoring
- Request pattern analysis
- Rapid-fire detection
- IP-based geolocation analysis
- User agent validation

### CAPTCHA Integration
- Triggered by suspicious behavior
- Required for high-risk operations
- Progressive difficulty based on threat level
- Accessibility compliance (audio alternatives)

## Privacy Compliance

### GDPR Compliance

#### Data Subject Rights
```python
# GDPR compliance endpoints
@router.get("/data-export")
async def export_user_data(user_id: str = Depends(get_current_user)):
    """Export all user data in machine-readable format"""
    return await gdpr_service.export_user_data(user_id)

@router.delete("/data-deletion")
async def delete_user_data(user_id: str = Depends(get_current_user)):
    """Delete all user data (right to be forgotten)"""
    return await gdpr_service.delete_user_data(user_id)

@router.get("/data-portability")
async def get_portable_data(user_id: str = Depends(get_current_user)):
    """Get user data in portable format"""
    return await gdpr_service.get_portable_data(user_id)
```

#### Privacy Controls
- Granular consent management
- Data minimization practices
- Purpose limitation enforcement
- Retention period controls
- Cross-border transfer safeguards

### CCPA Compliance
- California resident identification
- Opt-out mechanisms
- Data category disclosure
- Third-party sharing transparency
- Consumer request handling

## Monitoring and Incident Response

### Security Monitoring
```python
# Security event monitoring
MONITORED_EVENTS = [
    "failed_authentication_attempts",
    "privilege_escalation_attempts", 
    "unusual_data_access_patterns",
    "rate_limit_violations",
    "suspicious_content_generation",
    "data_export_requests",
    "admin_action_anomalies"
]
```

### Alerting Thresholds
- **Critical**: Immediate response required (< 15 minutes)
- **High**: Response within 1 hour
- **Medium**: Response within 4 hours  
- **Low**: Response within 24 hours

### Incident Response Plan

#### Phase 1: Detection and Analysis
1. Automated alert generation
2. Initial severity assessment
3. Stakeholder notification
4. Evidence preservation

#### Phase 2: Containment and Eradication
1. Threat isolation
2. System hardening
3. Vulnerability patching
4. Malicious content removal

#### Phase 3: Recovery and Post-Incident
1. System restoration
2. Monitoring enhancement
3. Lessons learned documentation
4. Process improvement

## Security Development Lifecycle

### Secure Coding Practices
- Input validation and sanitization
- Output encoding and escaping
- Parameterized database queries
- Secure session management
- Error handling without information disclosure

### Code Review Process
- Mandatory security review for all changes
- Automated security scanning (SAST/DAST)
- Dependency vulnerability scanning
- Infrastructure as Code security validation

### Testing Requirements
- Security unit tests
- Integration security testing
- Penetration testing (quarterly)
- Red team exercises (annually)

## Infrastructure Security

### Network Security
- VPC with private subnets
- WAF (Web Application Firewall)
- DDoS protection
- Network segmentation
- Jump box access for production

### Container Security
- Minimal base images
- Regular image scanning
- Runtime security monitoring
- Secret management integration
- Non-root container execution

### Cloud Security
- IAM least privilege
- Resource-based policies
- CloudTrail logging
- Config compliance monitoring
- Security Hub integration

## Compliance and Auditing

### Audit Requirements
- Daily access log review
- Weekly privilege audit
- Monthly security assessment
- Quarterly compliance review
- Annual security audit

### Compliance Standards
- SOC 2 Type II
- ISO 27001 (planned)
- PCI DSS (for payment processing)
- GDPR/CCPA privacy regulations

### Audit Trail
```sql
-- Comprehensive audit logging
CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN,
    details JSONB,
    risk_level VARCHAR(20)
);
```

## Security Configuration

### Environment Variables
```bash
# Security-related environment variables
JWT_PRIVATE_KEY_PATH=/secrets/jwt-private-key.pem
JWT_PUBLIC_KEY_PATH=/secrets/jwt-public-key.pem
DATABASE_ENCRYPTION_KEY=/secrets/db-encryption-key
SESSION_SECRET_KEY=/secrets/session-secret
OAUTH_CLIENT_SECRET=/secrets/oauth-client-secret
WEBHOOK_SIGNING_SECRET=/secrets/webhook-signing-secret
```

### Secrets Management
- Cloud-native secret management (Azure Key Vault/AWS Secrets Manager)
- Automatic secret rotation
- Audit trail for secret access
- Principle of least privilege for secret access

---

**Document Version**: 1.0  
**Classification**: Internal  
**Last Updated**: December 2024  
**Next Review**: March 2025  
**Owner**: Security Team
