"""Database models for CLM Platform."""
from datetime import datetime
from typing import List
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text,
    Date, TIMESTAMP, Index, UniqueConstraint, JSON, event, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class Role(Base):
    """User roles."""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    permissions = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", back_populates="role")


class User(Base):
    """Users table."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('ix_users_email', 'email'),
        Index('ix_users_username', 'username'),
    )
    
    role = relationship("Role", back_populates="users")
    contracts = relationship("Contract", back_populates="owner")
    approvals = relationship("Approval", back_populates="approver")
    audit_logs = relationship("AuditLog", back_populates="user")


class Contract(Base):
    """Contracts table."""
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_type = Column(String(50), nullable=False)
    status = Column(String(50), default="draft")  # draft, submitted, approved, rejected, executed
    value = Column(Integer)  # in cents
    currency = Column(String(10), default="USD")
    start_date = Column(Date)
    end_date = Column(Date)
    renewal_date = Column(Date)
    file_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('ix_contracts_contract_number', 'contract_number'),
        Index('ix_contracts_status', 'status'),
        Index('ix_contracts_owner_id', 'owner_id'),
    )
    
    owner = relationship("User", back_populates="contracts")
    versions = relationship("ContractVersion", back_populates="contract")
    clauses = relationship("ContractClause", back_populates="contract")
    approvals = relationship("Approval", back_populates="contract")
    renewals = relationship("Renewal", back_populates="contract")
    audit_logs = relationship("AuditLog", back_populates="contract")


class ContractVersion(Base):
    """Contract versions for version control."""
    __tablename__ = "contract_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    change_summary = Column(Text)
    file_path = Column(String(500))
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('contract_id', 'version_number', name='uq_contract_version'),
        Index('ix_contract_versions_contract_id', 'contract_id'),
    )
    
    contract = relationship("Contract", back_populates="versions")


class Clause(Base):
    """Reusable clauses library."""
    __tablename__ = "clauses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_clauses_title', 'title'),
        Index('ix_clauses_category', 'category'),
    )
    
    contracts = relationship("ContractClause", back_populates="clause")


class ContractClause(Base):
    """Junction table for contracts and clauses."""
    __tablename__ = "contract_clauses"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('contract_id', 'clause_id', name='uq_contract_clause'),
        Index('ix_contract_clauses_contract_id', 'contract_id'),
    )
    
    contract = relationship("Contract", back_populates="clauses")
    clause = relationship("Clause", back_populates="contracts")


class Approval(Base):
    """Approval workflow states."""
    __tablename__ = "approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approval_level = Column(Integer, nullable=False)  # 1, 2, 3 etc.
    status = Column(String(50), default="pending")  # pending, approved, rejected
    comments = Column(Text)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_approvals_contract_id', 'contract_id'),
        Index('ix_approvals_status', 'status'),
    )
    
    contract = relationship("Contract", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")


class Renewal(Base):
    """Contract renewals and deadlines."""
    __tablename__ = "renewals"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    renewal_date = Column(Date, nullable=False)
    alert_date = Column(Date, nullable=False)
    status = Column(String(50), default="pending")  # pending, notified, renewed, expired
    notification_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_renewals_contract_id', 'contract_id'),
        Index('ix_renewals_renewal_date', 'renewal_date'),
    )
    
    contract = relationship("Contract", back_populates="renewals")


class AuditLog(Base):
    """Audit logging for compliance."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)  # contract, clause, approval, etc.
    resource_id = Column(Integer)
    changes = Column(JSON)  # Store before/after changes
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('ix_audit_logs_user_id', 'user_id'),
        Index('ix_audit_logs_contract_id', 'contract_id'),
        Index('ix_audit_logs_created_at', 'created_at'),
    )
    
    user = relationship("User", back_populates="audit_logs")
    contract = relationship("Contract", back_populates="audit_logs")
