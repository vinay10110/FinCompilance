from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ChangeType(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"

class RequirementType(str, Enum):
    TECHNICAL = "technical"
    OPERATIONAL = "operational"
    REPORTING = "reporting"
    COMPLIANCE = "compliance"
    FINANCIAL = "financial"
    GENERAL = "general"

class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Requirement(BaseModel):
    id: str = Field(..., description="Unique identifier for the requirement")
    text: str = Field(..., description="The actual requirement text")
    type: RequirementType = Field(..., description="Type of requirement")
    priority: PriorityLevel = Field(..., description="Priority level of the requirement")
    deadline: Optional[datetime] = Field(None, description="Deadline for implementation")
    source_document: str = Field(..., description="Source document identifier")
    section: Optional[str] = Field(None, description="Section in the document")
    dependencies: List[str] = Field(default_factory=list, description="IDs of dependent requirements")

class DocumentMetadata(BaseModel):
    title: str
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None

class ProcessedDocument(BaseModel):
    metadata: DocumentMetadata
    requirements: List[Requirement]
    key_phrases: List[str]
    dates: List[str]
    images: List[Dict[str, Any]]
    page_count: int
    processed_at: datetime
    file_hash: str

class RequirementChange(BaseModel):
    old: Optional[Requirement] = None
    new: Optional[Requirement] = None
    change_type: str = Field(..., description="Type of change: added, modified, or removed")
    impact_score: float = Field(..., ge=0, le=1, description="Impact score of the change")

class DocumentComparison(BaseModel):
    requirements_changes: Dict[str, List[RequirementChange]]
    key_phrase_changes: Dict[str, List[str]]
    similarity_score: float = Field(..., ge=0, le=1)
    comparison_date: datetime = Field(default_factory=datetime.now)

class ImplementationTask(BaseModel):
    id: str = Field(..., description="Unique identifier for the task")
    requirement_id: str = Field(..., description="ID of the requirement this task implements")
    title: str
    description: str
    type: str
    status: str = "pending"
    assigned_to: Optional[str] = None
    estimated_hours: float
    dependencies: List[str] = Field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    progress: float = Field(0, ge=0, le=100)
    priority: PriorityLevel

class ImplementationPlan(BaseModel):
    id: str = Field(..., description="Unique identifier for the plan")
    document_id: str = Field(..., description="ID of the regulatory document")
    tasks: List[ImplementationTask]
    timeline: Dict[str, Any]
    resources: Dict[str, Any]
    total_estimated_hours: float
    risk_assessment: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = "draft"

class ComplianceVerification(BaseModel):
    plan_id: str = Field(..., description="ID of the implementation plan")
    verification_date: datetime = Field(default_factory=datetime.now)
    requirements_status: Dict[str, Dict[str, Any]]
    compliance_score: float = Field(..., ge=0, le=100)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    reviewer: Optional[str] = None
    status: str = "pending"

class RBIUpdate(Base):
    __tablename__ = "rbi_updates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    press_release_link = Column(String(1000), unique=True, nullable=False)
    pdf_link = Column(String(1000), nullable=True)
    date_published = Column(DateTime, nullable=True)
    date_scraped = Column(DateTime, default=datetime.utcnow)
    is_new = Column(Boolean, default=True)
    content_summary = Column(Text, nullable=True)

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/rbi_compliance"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)