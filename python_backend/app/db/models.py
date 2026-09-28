import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .encrypted_db import Base

class SystemSetting(Base):
    __tablename__ = 'system_settings'
    key = Column(String, primary_key=True)
    value_json = Column(String)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    
    role = relationship("Role")

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False) # e.g., Operator, Approver, Auditor, Admin
    permissions = Column(JSON, nullable=False, default=list)

class Policy(Base):
    __tablename__ = 'policies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(20), nullable=False, unique=True)
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Case(Base):
    __tablename__ = 'cases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String(100), unique=True, nullable=False)
    legal_hold = Column(Boolean, default=False, nullable=False)

class Evidence(Base):
    __tablename__ = 'evidence'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_tag = Column(String(100), unique=True, nullable=False)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    active_evidence = Column(Boolean, default=True, nullable=False)
    original_hash = Column(String(128), nullable=True) # Hash baseline from first import

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_type = Column(String(50), nullable=False) # e.g., sanitisation, recovery
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    actor_username = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    sensitive_details = Column(JSON, nullable=True) # Unredacted paths, NOT hashed
    previous_hash = Column(String(128), nullable=True) # SHA-512 hex
    event_hash = Column(String(128), nullable=False)   # SHA-512 hex
    signature = Column(Text, nullable=False)           # Ed25519 signature hex

class Certificate(Base):
    __tablename__ = 'certificates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    manifest_json = Column(JSON, nullable=False)
    pdf_bytes = Column(Text, nullable=True) # store base64 encoded pdf bytes
    issued_at = Column(DateTime, default=datetime.datetime.utcnow)

class FileSchedule(Base):
    __tablename__ = 'file_schedules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    paths = Column(JSON, nullable=False)
    schedule_type = Column(String(50), nullable=False) # one-time, recurring
    cron_expr = Column(String(100), nullable=True)
    skip_quarantine = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey('users.id'))

class ReviewQueueItem(Base):
    __tablename__ = 'review_queue'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(1024), nullable=False)
    flag_reason = Column(String(255))
    status = Column(String(50), default="pending") # pending, approved, rejected

class QuarantinedFile(Base):
    __tablename__ = 'quarantine'
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_path = Column(String(1024), nullable=False)
    vault_path = Column(String(1024), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(50), default="active") # active, restored, wiped
