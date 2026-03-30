"""Database models for CLM Platform."""
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    Date, Index, UniqueConstraint, JSON, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


def utcnow():
    """Timezone-aware UTC now."""
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════
# Organization / Tenant
# ═══════════════════════════════════════════════════════════════
class Organization(Base):
    """Organization / tenant for multi-tenancy."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    settings = Column(JSON, default={})
    subscription_tier = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    users = relationship("User", back_populates="organization")
    contracts = relationship("Contract", back_populates="organization")
    clauses = relationship("Clause", back_populates="organization")
    templates = relationship("ContractTemplate", back_populates="organization")
    tags = relationship("Tag", back_populates="organization")


# ═══════════════════════════════════════════════════════════════
# Roles & Permissions
# ═══════════════════════════════════════════════════════════════
# Master list of granular permissions
ALL_PERMISSIONS = [
    # Contracts
    "contracts:create", "contracts:read", "contracts:read_all",
    "contracts:update", "contracts:update_all",
    "contracts:delete", "contracts:delete_all",
    "contracts:submit", "contracts:execute",
    # Clauses
    "clauses:create", "clauses:read", "clauses:update", "clauses:delete",
    # Approvals
    "approvals:view", "approvals:approve", "approvals:reject", "approvals:assign",
    # Templates
    "templates:create", "templates:read", "templates:update", "templates:delete",
    # Tags
    "tags:create", "tags:read", "tags:update", "tags:delete",
    # Comments
    "comments:create", "comments:read", "comments:delete",
    # Admin
    "users:manage", "users:view",
    "roles:manage",
    "audit:view", "audit:export",
    "settings:manage",
    "reports:export",
    "notifications:manage",
    "org:manage",
]

# Pre-defined role templates
ROLE_TEMPLATES = {
    "super_admin": {
        "description": "Full system access including role management and data deletion.",
        "permissions": ALL_PERMISSIONS,
    },
    "admin": {
        "description": "Organization administrator. Can manage users and organization settings.",
        "permissions": [
            "contracts:create", "contracts:read", "contracts:read_all",
            "contracts:update", "contracts:update_all",
            "contracts:submit", "contracts:execute",
            "clauses:create", "clauses:read", "clauses:update",
            "approvals:view", "approvals:approve", "approvals:reject", "approvals:assign",
            "templates:create", "templates:read", "templates:update", "templates:delete",
            "tags:create", "tags:read", "tags:update", "tags:delete",
            "comments:create", "comments:read", "comments:delete",
            "users:manage", "users:view", "roles:manage",
            "audit:view", "audit:export",
            "settings:manage", "reports:export",
            "notifications:manage", "org:manage",
        ],
    },
    "editor": {
        "description": "Standard internal user. Can create and edit contracts and clauses.",
        "permissions": [
            "contracts:create", "contracts:read", "contracts:read_all",
            "contracts:update", "contracts:submit",
            "clauses:create", "clauses:read", "clauses:update",
            "approvals:view", "approvals:assign", "approvals:approve", "approvals:reject",
            "templates:read",
            "tags:create", "tags:read",
            "comments:create", "comments:read",
            "users:view", "audit:view",
        ],
    },
    "viewer": {
        "description": "Read-only access to the system.",
        "permissions": [
            "contracts:read",
            "clauses:read",
            "approvals:view",
            "templates:read", "tags:read",
            "comments:read",
            "users:view",
        ],
    },
}


class Role(Base):
    """User roles with granular permissions."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    permissions = Column(JSON, default=[])  # list of permission strings
    is_system_role = Column(Boolean, default=False)  # built-in roles cannot be deleted
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    users = relationship("User", back_populates="role")


# ═══════════════════════════════════════════════════════════════
# Users
# ═══════════════════════════════════════════════════════════════
class User(Base):
    """Users table with security enhancements."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=False)  # Inactive by default (needs admin approval)
    is_superuser = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)  # Admin must approve registration

    # Security: account lockout
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    last_login = Column(DateTime, nullable=True)

    role = relationship("Role", back_populates="users")
    organization = relationship("Organization", back_populates="users")
    contracts = relationship("Contract", back_populates="owner", foreign_keys="[Contract.owner_id]")
    approvals = relationship("Approval", back_populates="approver")
    audit_logs = relationship("AuditLog", back_populates="user")
    clause_versions = relationship("ClauseVersion", back_populates="created_by")
    comments = relationship("Comment", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


# ═══════════════════════════════════════════════════════════════
# Token Blocklist (for logout/revocation)
# ═══════════════════════════════════════════════════════════════
class TokenBlocklist(Base):
    """Blocklisted JWT tokens (revoked on logout)."""
    __tablename__ = "token_blocklist"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID
    token_type = Column(String(20), nullable=False)  # access or refresh
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    blocked_at = Column(DateTime, default=utcnow)


# ═══════════════════════════════════════════════════════════════
# API Keys
# ═══════════════════════════════════════════════════════════════
class APIKey(Base):
    """API keys for system-to-system integrations."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(10), nullable=False)  # first 8 chars for identification
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scopes = Column(JSON, default=[])  # list of permission strings
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="api_keys")


# ═══════════════════════════════════════════════════════════════
# Tags
# ═══════════════════════════════════════════════════════════════
class Tag(Base):
    """Tags for categorizing contracts."""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    color = Column(String(20), default="#6366f1")
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='uq_tag_name_org'),
    )

    organization = relationship("Organization", back_populates="tags")
    contracts = relationship("ContractTag", back_populates="tag")


class ContractTag(Base):
    """Junction table for contracts and tags."""
    __tablename__ = "contract_tags"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint('contract_id', 'tag_id', name='uq_contract_tag'),
    )

    contract = relationship("Contract", back_populates="tags")
    tag = relationship("Tag", back_populates="contracts")


# ═══════════════════════════════════════════════════════════════
# Contracts
# ═══════════════════════════════════════════════════════════════
class Contract(Base):
    """Contracts table with soft delete and org scoping."""
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("contract_templates.id"), nullable=True)
    contract_type = Column(String(50), nullable=False)
    status = Column(String(50), default="draft")
    value = Column(Integer)
    currency = Column(String(10), default="USD")
    start_date = Column(Date)
    end_date = Column(Date)
    renewal_date = Column(Date)
    file_path = Column(String(500))
    metadata_fields = Column(JSON, default={})  # custom key-value metadata

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    executed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('ix_contracts_status', 'status'),
        Index('ix_contracts_not_deleted', 'is_deleted'),
    )

    owner = relationship("User", back_populates="contracts", foreign_keys=[owner_id])
    organization = relationship("Organization", back_populates="contracts")
    template = relationship("ContractTemplate", back_populates="contracts")
    versions = relationship("ContractVersion", back_populates="contract")
    clauses = relationship("ContractClause", back_populates="contract")
    approvals = relationship("Approval", back_populates="contract")
    renewals = relationship("Renewal", back_populates="contract")
    audit_logs = relationship("AuditLog", back_populates="contract")
    tags = relationship("ContractTag", back_populates="contract")
    comments = relationship("Comment", back_populates="contract")
    attachments = relationship("Attachment", back_populates="contract", cascade="all, delete-orphan")



class ContractVersion(Base):
    """Contract versions for version control."""
    __tablename__ = "contract_versions"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    change_summary = Column(Text)
    file_path = Column(String(500))
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint('contract_id', 'version_number', name='uq_contract_version'),
    )

    contract = relationship("Contract", back_populates="versions")


# ═══════════════════════════════════════════════════════════════
# Contract Templates
# ═══════════════════════════════════════════════════════════════
class ContractTemplate(Base):
    """Reusable contract templates."""
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    contract_type = Column(String(50), nullable=False)
    default_fields = Column(JSON, default={})  # pre-filled field values
    approval_workflow = Column(JSON, default=[])  # list of {role, level}
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="templates")
    template_clauses = relationship("TemplateClause", back_populates="template")
    contracts = relationship("Contract", back_populates="template")
    attachments = relationship("Attachment", back_populates="template", cascade="all, delete-orphan")



class TemplateClause(Base):
    """Clauses associated with a template."""
    __tablename__ = "template_clauses"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("contract_templates.id"), nullable=False)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=False)
    order = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint('template_id', 'clause_id', name='uq_template_clause'),
    )

    template = relationship("ContractTemplate", back_populates="template_clauses")
    clause = relationship("Clause", back_populates="template_clauses")


# ═══════════════════════════════════════════════════════════════
# Clauses
# ═══════════════════════════════════════════════════════════════
class Clause(Base):
    """Reusable clauses library with org scoping."""
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="clauses")
    contracts = relationship("ContractClause", back_populates="clause")
    template_clauses = relationship("TemplateClause", back_populates="clause")
    attachments = relationship("Attachment", back_populates="clause", cascade="all, delete-orphan")
    versions = relationship("ClauseVersion", back_populates="clause", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="clause")



class ContractClause(Base):
    """Junction table for contracts and clauses."""
    __tablename__ = "contract_clauses"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint('contract_id', 'clause_id', name='uq_contract_clause'),
    )

    contract = relationship("Contract", back_populates="clauses")
    clause = relationship("Clause", back_populates="contracts")


class ClauseVersion(Base):
    """Historical versions of clauses."""
    __tablename__ = "clause_versions"

    id = Column(Integer, primary_key=True, index=True)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    clause = relationship("Clause", back_populates="versions")
    created_by = relationship("User", back_populates="clause_versions")


# ═══════════════════════════════════════════════════════════════
# Approvals
# ═══════════════════════════════════════════════════════════════
class Approval(Base):
    """Approval workflow states."""
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approval_level = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")
    comments = Column(Text)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    contract = relationship("Contract", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")


# ═══════════════════════════════════════════════════════════════
# Renewals
# ═══════════════════════════════════════════════════════════════
class Renewal(Base):
    """Contract renewals and deadlines."""
    __tablename__ = "renewals"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    renewal_date = Column(Date, nullable=False)
    alert_date = Column(Date, nullable=False)
    status = Column(String(50), default="pending")
    notification_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    contract = relationship("Contract", back_populates="renewals")


# ═══════════════════════════════════════════════════════════════
# Comments (threaded, on contracts)
# ═══════════════════════════════════════════════════════════════
class Comment(Base):
    """Threaded comments on contracts."""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # threading
    content = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    contract = relationship("Contract", back_populates="comments")
    user = relationship("User", back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])


# ═══════════════════════════════════════════════════════════════
# In-App Notifications
# ═══════════════════════════════════════════════════════════════
class Notification(Base):
    """In-app notifications for users."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # approval_request, status_change, comment, renewal, system
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500), nullable=True)  # deep link to relevant page
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="notifications")


# ═══════════════════════════════════════════════════════════════
# Audit Logs
# ═══════════════════════════════════════════════════════════════
class AuditLog(Base):
    """Audit logging for compliance with tamper-proof hashing."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer)
    changes = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    previous_hash = Column(String(64), nullable=True)  # SHA-256 of previous entry
    entry_hash = Column(String(64), nullable=True)  # hash of this entry for tamper detection
    created_at = Column(DateTime, default=utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")
    contract = relationship("Contract", back_populates="audit_logs")
    clause = relationship("Clause", back_populates="audit_logs")


# ═══════════════════════════════════════════════════════════════
# Media & Attachments
# ═══════════════════════════════════════════════════════════════
class Attachment(Base):
    """Media files and attachments linked to various entities."""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100))  # mime type
    file_size = Column(Integer)  # in bytes
    
    # Polymorphic-like links (FKs)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("contract_templates.id"), nullable=True)
    
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    contract = relationship("Contract", back_populates="attachments")
    clause = relationship("Clause", back_populates="attachments")
    template = relationship("ContractTemplate", back_populates="attachments")
    uploader = relationship("User")

