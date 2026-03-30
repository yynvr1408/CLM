"""Pydantic schemas for request/response validation."""
import re
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, field_serializer
from app.core.config import settings


# ═══════════════════════════════════════════════════════════════
# Organization Schemas
# ═══════════════════════════════════════════════════════════════
class OrganizationBase(BaseModel):
    name: str
    slug: str = Field(..., pattern=r'^[a-z0-9\-]+$')
    domain: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Dict[str, Any] = {}
    subscription_tier: str = "free"


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    subscription_tier: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# Role Schemas
# ═══════════════════════════════════════════════════════════════
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleResponse(RoleBase):
    id: int
    is_system_role: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# User Schemas
# ═══════════════════════════════════════════════════════════════
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Enforce password complexity rules."""
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':\"\\|,.<>\/?]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, v):
        """Restrict registration to allowed email domains."""
        if settings.ALLOWED_EMAIL_DOMAINS:
            domain = v.split('@')[1]
            if domain not in settings.ALLOWED_EMAIL_DOMAINS:
                raise ValueError(f'Registration is restricted to approved email domains')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    is_approved: bool
    role_id: int
    organization_id: Optional[int] = None
    permissions: List[str] = []
    role_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserAdminUpdate(BaseModel):
    """Admin update for user management."""
    is_active: Optional[bool] = None
    is_approved: Optional[bool] = None
    role_id: Optional[int] = None
    organization_id: Optional[int] = None
    is_superuser: Optional[bool] = None


# ═══════════════════════════════════════════════════════════════
# Authentication Schemas
# ═══════════════════════════════════════════════════════════════
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':\"\\|,.<>\/?]', v):
            raise ValueError('Password must contain at least one special character')
        return v


# ═══════════════════════════════════════════════════════════════
# Tag Schemas
# ═══════════════════════════════════════════════════════════════
class TagBase(BaseModel):
    name: str
    color: str = "#6366f1"


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: int
    organization_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# Attachment Schemas
# ═══════════════════════════════════════════════════════════════
class AttachmentBase(BaseModel):
    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None


class AttachmentResponse(AttachmentBase):
    id: int
    file_path: str
    uploaded_by_id: int
    created_at: datetime

    class Config:
        from_attributes = True



# ═══════════════════════════════════════════════════════════════
# Clause Schemas
# ═══════════════════════════════════════════════════════════════
class ClauseBase(BaseModel):
    title: str
    content: str
    category: str


class ClauseCreate(ClauseBase):
    pass


class ClauseUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


class ClauseResponse(ClauseBase):
    id: int
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    attachments: List[AttachmentResponse] = []

    @field_serializer('created_at', 'updated_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")

    class Config:
        from_attributes = True


class ClauseVersionResponse(BaseModel):
    id: int
    clause_id: int
    version_number: int
    title: str
    content: str
    category: str
    created_by_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# Contract Schemas
# ═══════════════════════════════════════════════════════════════
class ContractClauseLink(BaseModel):
    clause_id: int
    order: int = 0


class ContractBase(BaseModel):
    title: str
    description: Optional[str] = None
    contract_type: str
    value: Optional[int] = None
    currency: str = "USD"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    metadata_fields: Dict[str, Any] = {}


class ContractCreate(ContractBase):
    clauses: List[ContractClauseLink] = []
    tag_ids: List[int] = []
    template_id: Optional[int] = None


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    contract_type: Optional[str] = None
    value: Optional[int] = None
    currency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    metadata_fields: Optional[Dict[str, Any]] = None


class ContractResponse(ContractBase):
    id: int
    contract_number: str
    status: str
    owner_id: int
    organization_id: Optional[int] = None
    template_id: Optional[int] = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    executed_at: Optional[datetime] = None
    attachments: List[AttachmentResponse] = []

    class Config:

        from_attributes = True


class ContractDetailResponse(ContractResponse):
    clauses: List[ClauseResponse] = []
    tags: List[TagResponse] = []


# ═══════════════════════════════════════════════════════════════
# Contract Version Schemas
# ═══════════════════════════════════════════════════════════════
class ContractVersionCreate(BaseModel):
    change_summary: str


class ContractVersionResponse(BaseModel):
    id: int
    version_number: int
    change_summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# Contract Template Schemas
# ═══════════════════════════════════════════════════════════════
class TemplateClauseLink(BaseModel):
    clause_id: int
    order: int = 0
    is_required: bool = True


class ContractTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    contract_type: str
    default_fields: Dict[str, Any] = {}
    approval_workflow: List[Dict[str, Any]] = []


class ContractTemplateCreate(ContractTemplateBase):
    clause_ids: List[TemplateClauseLink] = []


class ContractTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contract_type: Optional[str] = None
    default_fields: Optional[Dict[str, Any]] = None
    approval_workflow: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class ContractTemplateResponse(ContractTemplateBase):
    id: int
    version: int
    is_active: bool
    organization_id: Optional[int] = None
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    clauses: List[ClauseResponse] = []
    attachments: List[AttachmentResponse] = []

    class Config:

        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# Comment Schemas
# ═══════════════════════════════════════════════════════════════
class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    content: Optional[str] = None
    is_resolved: Optional[bool] = None


class CommentResponse(BaseModel):
    id: int
    contract_id: int
    user_id: int
    parent_id: Optional[int] = None
    content: str
    is_resolved: bool
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# Notification Schemas
# ═══════════════════════════════════════════════════════════════
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationMarkRead(BaseModel):
    notification_ids: List[int] = []
    mark_all: bool = False


# ═══════════════════════════════════════════════════════════════
# Approval Schemas
# ═══════════════════════════════════════════════════════════════
class ApprovalBase(BaseModel):
    approval_level: int
    comments: Optional[str] = None


class ApprovalCreate(ApprovalBase):
    approver_id: int


class ApprovalUpdate(BaseModel):
    status: str
    comments: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    contract_id: int
    approver_id: int
    approval_level: int
    status: str
    comments: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    # Nested info for UI
    contract_title: Optional[str] = None
    contract_number: Optional[str] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# Renewal Schemas
# ═══════════════════════════════════════════════════════════════
class RenewalCreate(BaseModel):
    renewal_date: date
    alert_date: date


class RenewalUpdate(BaseModel):
    status: str


class RenewalResponse(BaseModel):
    id: int
    contract_id: int
    renewal_date: date
    alert_date: date
    status: str
    notification_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# API Key Schemas
# ═══════════════════════════════════════════════════════════════
class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str] = []
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    """Response when creating a new key — includes the raw key (shown only once)."""
    raw_key: str


# ═══════════════════════════════════════════════════════════════
# Audit Log Schemas
# ═══════════════════════════════════════════════════════════════
class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    contract_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[int]
    changes: Optional[Dict]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    entry_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# Search Schemas
# ═══════════════════════════════════════════════════════════════
class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    page: int = 1
    per_page: int = 20


class SearchResponse(BaseModel):
    total: int
    page: int
    per_page: int
    results: List[Dict]


# ═══════════════════════════════════════════════════════════════
# Bulk Operation Schemas
# ═══════════════════════════════════════════════════════════════
class BulkStatusUpdate(BaseModel):
    contract_ids: List[int]
    new_status: str


class BulkDeleteRequest(BaseModel):
    contract_ids: List[int]


# ═══════════════════════════════════════════════════════════════
# Dashboard / Analytics Schemas
# ═══════════════════════════════════════════════════════════════
class DashboardStats(BaseModel):
    total_contracts: int = 0
    draft_contracts: int = 0
    submitted_contracts: int = 0
    approved_contracts: int = 0
    rejected_contracts: int = 0
    executed_contracts: int = 0
    total_value: int = 0
    pending_approvals: int = 0
    upcoming_renewals: int = 0
    overdue_renewals: int = 0
    total_users: int = 0
    contracts_expiring_30d: int = 0
    contracts_expiring_60d: int = 0
    contracts_expiring_90d: int = 0


# ═══════════════════════════════════════════════════════════════
# History & Integrity Schemas
# ═══════════════════════════════════════════════════════════════
class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    contract_id: Optional[int] = None
    clause_id: Optional[int] = None
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    # User info
    user_full_name: Optional[str] = None

    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")

    class Config:
        from_attributes = True


class IntegrityStatus(BaseModel):
    is_valid: bool
    broken_id: Optional[int] = None
    total_logs: int


class ContractVersionResponse(BaseModel):
    id: int
    contract_id: int
    version_number: int
    change_summary: Optional[str] = None
    file_path: Optional[str] = None
    created_by_id: int
    created_at: datetime
    # User info
    created_by_name: Optional[str] = None

    class Config:
        from_attributes = True
