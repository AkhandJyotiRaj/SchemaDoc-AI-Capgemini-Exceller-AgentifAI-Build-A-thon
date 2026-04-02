from typing import TypedDict, List, Dict, Any, Optional, Union


class ColumnStats(TypedDict):
    """Deterministic statistical profile of a column."""
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    sample_values: List[Any]
    min_value: Optional[Union[int, float]]
    max_value: Optional[Union[int, float]]
    mean_value: Optional[float]

class ColumnMetadata(TypedDict):
    """The atomic unit of the data dictionary."""
    name: str
    original_type: str
    
    description: Optional[str]
    business_logic: Optional[str]
    potential_pii: bool
    tags: List[str]
    stats: Optional[ColumnStats]

class ForeignKey(TypedDict):
    column: str
    referred_table: str
    referred_column: str

class TableSchema(TypedDict):
    """Represents a single table's state."""
    table_name: str
    row_count: int
    columns: Dict[str, ColumnMetadata]
    health_score: float # 0.0 to 1.0
    foreign_keys: List[ForeignKey]
    description: Optional[str]


class AgentState(TypedDict):
    """The shared memory of the LangGraph pipeline."""
    connection_string: str
    schema_raw: Dict[str, TableSchema]

    # Separated to prevent AI hallucinations from overwriting actual schema
    schema_enriched: Dict[str, TableSchema]

    errors: List[str]
    retry_count: int
    validation_status: str
    final_markdown: str
