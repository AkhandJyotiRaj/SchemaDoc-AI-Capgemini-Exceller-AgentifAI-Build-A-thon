"""
Shared Pydantic models for API request/response validation.
Used by both backend API routes and can generate TypeScript types for frontend.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


# ── Column & Table Schemas ──

class ColumnStatsResponse(BaseModel):
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    unique_percentage: float = 0.0
    sample_values: List[Any] = []
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    mean_value: Optional[float] = None


class ColumnMetadataResponse(BaseModel):
    name: str
    original_type: str
    description: Optional[str] = None
    business_logic: Optional[str] = None
    potential_pii: bool = False
    tags: List[str] = []
    stats: Optional[ColumnStatsResponse] = None


class ForeignKeyResponse(BaseModel):
    column: str
    referred_table: str
    referred_column: str


class TableSchemaResponse(BaseModel):
    table_name: str
    row_count: int = 0
    columns: Dict[str, ColumnMetadataResponse] = {}
    health_score: float = 100.0
    foreign_keys: List[ForeignKeyResponse] = []
    description: Optional[str] = None


# ── Pipeline ──

class PipelineRunRequest(BaseModel):
    connection_string: str = Field(
        ..., description="SQLAlchemy connection string (e.g., sqlite:///path/to/db.sqlite)"
    )


class PipelineLogEntry(BaseModel):
    step: str
    status: str
    message: str
    icon: str
    errors: List[str] = []


class PipelineRunResponse(BaseModel):
    run_id: str
    status: str  # "running", "completed", "failed"
    created_at: datetime
    schema_enriched: Optional[Dict[str, TableSchemaResponse]] = None
    pipeline_log: List[PipelineLogEntry] = []
    errors: List[str] = []


class PipelineStatusResponse(BaseModel):
    run_id: str
    status: str
    progress: float = 0.0  # 0.0 to 1.0
    current_step: Optional[str] = None


# ── Chat ──

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    run_id: str
    history: List[Dict[str, str]] = []  # [{"role": "user", "content": "..."}, ...]


class ChatResponse(BaseModel):
    response: str
    sql_query: Optional[str] = None


# ── Export ──

class ExportRequest(BaseModel):
    run_id: str
    format: str = Field("json", pattern="^(json|markdown)$")


# ── Database Overview ──

class DatabaseOverviewResponse(BaseModel):
    overview: str
    total_tables: int
    total_columns: int
    total_rows: int
    avg_health: float
    pii_count: int
    fk_count: int


# ── Connections ──

class ConnectionInfo(BaseModel):
    id: str
    name: str
    connection_string: str
    db_type: str  # "sqlite", "postgresql", "mysql"
    created_at: datetime


class ConnectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    connection_string: str
