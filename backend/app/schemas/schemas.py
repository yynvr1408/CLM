"""Pydantic schemas for request/response validation."""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ===== User Schemas =====
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    role_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== Role Schemas =====
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Dict[str, Any] = {}


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== Authentication Schemas =====
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ===== Clause Schemas =====
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
    
    class Config:
        from_attributes = True


# ===== Contract Schemas =====
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


class ContractCreate(ContractBase):
    clauses: List[ContractClauseLink] = []


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    contract_type: Optional[str] = None
    value: Optional[int] = None
    currency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class ContractResponse(ContractBase):
    id: int
    contract_number: str
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    executed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ContractDetailResponse(ContractResponse):
    clauses: List[ClauseResponse] = []


# ===== Contract Version Schemas =====
class ContractVersionCreate(BaseModel):
    change_summary: str


class ContractVersionResponse(BaseModel):
    id: int
    version_number: int
    change_summary: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== Approval Schemas =====
class ApprovalBase(BaseModel):
    approval_level: int
    comments: Optional[str] = None


class ApprovalCreate(ApprovalBase):
    approver_id: int


class ApprovalUpdate(BaseModel):
    status: str  # approved or rejected
    comments: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    contract_id: int
    approver_id: int
    approval_level: int
    status: str
    comments: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== Renewal Schemas =====
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


# ===== Audit Log Schemas =====
class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    contract_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[int]
    changes: Optional[Dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== Search Schemas =====
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
