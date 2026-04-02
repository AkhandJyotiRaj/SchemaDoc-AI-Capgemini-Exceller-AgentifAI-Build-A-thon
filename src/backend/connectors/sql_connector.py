from typing import Dict, Any, List, Optional
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, inspect, MetaData, Table, select, func, text, Column, case, literal
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from src.core.state import TableSchema, ColumnMetadata, ColumnStats

class SQLConnector:
    # SQLite internal tables that should never be documented
    _SYSTEM_TABLES = {
        "sqlite_sequence", "sqlite_stat1", "sqlite_stat2",
        "sqlite_stat3", "sqlite_stat4", "sqlite_master",
    }

    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()

    def get_live_schema(self) -> Dict[str, TableSchema]:
        """
        Orchestrates the full extraction: Structure + Statistics.
        Returns the 'schema_raw' state object.
        """
        schema_out: Dict[str, TableSchema] = {}
        all_tables = self.inspector.get_table_names()
        table_names = [t for t in all_tables if t.lower() not in self._SYSTEM_TABLES]

        print(f"Connected to DB. Found tables: {table_names} (filtered {len(all_tables) - len(table_names)} system tables)")

        def _process_table(t_name: str) -> tuple[str, dict]:
            """Process one table (structure + profiling).  Thread-safe."""
            local_meta = MetaData()
            table_obj = Table(t_name, local_meta, autoload_with=self.engine)
            columns_meta, fk_list = self._extract_structure(t_name, table_obj)
            row_count, health_score, col_stats = self._profile_data(table_obj, columns_meta)
            for col_name, stats in col_stats.items():
                if col_name in columns_meta:
                    columns_meta[col_name]["stats"] = stats
            return t_name, {
                "table_name": t_name,
                "row_count": row_count,
                "columns": columns_meta,
                "health_score": health_score,
                "description": None,
                "foreign_keys": fk_list,
            }

        with ThreadPoolExecutor(max_workers=min(len(table_names), 8)) as pool:
            futures = {pool.submit(_process_table, t): t for t in table_names}
            for future in as_completed(futures):
                t_name = futures[future]
                try:
                    name, data = future.result()
                    schema_out[name] = data
                except Exception as e:
                    print(f"Error processing table '{t_name}': {e}")

        return schema_out

    def _extract_structure(self, table_name: str, table_obj: Table) -> tuple[Dict[str, ColumnMetadata], List[dict]]:
        """Extracts names, types, constraints, and Foreign Keys."""
        cols_out = {}
        
        columns = self.inspector.get_columns(table_name)
        pk_constraint = self.inspector.get_pk_constraint(table_name)
        pk_cols = pk_constraint.get("constrained_columns", [])
        fks = self.inspector.get_foreign_keys(table_name)
        
        fk_list = []
        fk_map = {}
        
        for fk in fks:
            # SQLAlchemy returns list of cols, we take the first for simplicity in graph
            if fk["constrained_columns"]:
                local_col = fk["constrained_columns"][0]
                ref_table = fk["referred_table"]
                ref_col = fk["referred_columns"][0]
                
                fk_map[local_col] = ref_table
                fk_list.append({
                    "column": local_col,
                    "referred_table": ref_table,
                    "referred_column": ref_col
                })

        for col in columns:
            name = col["name"]
            tags = []
            if name in pk_cols: tags.append("PK")
            if name in fk_map: tags.append("FK")
            
            cols_out[name] = {
                "name": name,
                "original_type": str(col["type"]),
                "nullable": col["nullable"],
                "description": col.get("comment", None),
                "business_logic": None,
                "potential_pii": False,
                "tags": tags,
                "stats": None
            }
            
        return cols_out, fk_list

    def _profile_data(self, table_obj: Table, cols_meta: Dict[str, ColumnMetadata]):
        """
        Profile all columns in ONE batched SQL query per table instead of
        3-4 queries per column.  Cuts total DB round-trips from ~4*cols to 2.
        """
        stats_out: Dict[str, ColumnStats] = {}
        row_count = 0
        health_score = 100.0
        
        try:
            with self.engine.connect() as conn:
                count_query = select(func.count()).select_from(table_obj)
                row_count = conn.execute(count_query).scalar() or 0
                
                if row_count == 0:
                    return 0, 100.0, {}

                # ── Build ONE aggregation query for ALL columns ──
                agg_exprs = []
                col_order: List[str] = []
                numeric_flags: List[bool] = []

                for col_name, meta in cols_meta.items():
                    col_obj = table_obj.c[col_name]
                    col_order.append(col_name)

                    agg_exprs.append(
                        func.sum(case((col_obj == None, 1), else_=0)).label(f"{col_name}__nulls")
                    )
                    agg_exprs.append(
                        func.count(func.distinct(col_obj)).label(f"{col_name}__uniq")
                    )

                    type_str = meta["original_type"].upper()
                    is_numeric = any(
                        t in type_str
                        for t in ["INT", "FLOAT", "DECIMAL", "NUMERIC", "REAL"]
                    )
                    numeric_flags.append(is_numeric)
                    if is_numeric:
                        agg_exprs.append(func.min(col_obj).label(f"{col_name}__min"))
                        agg_exprs.append(func.max(col_obj).label(f"{col_name}__max"))
                        agg_exprs.append(func.avg(col_obj).label(f"{col_name}__avg"))

                agg_query = select(*agg_exprs).select_from(table_obj)
                agg_row = conn.execute(agg_query).fetchone()

                # ── ONE sample query ──
                sample_query = select(*[table_obj.c[c] for c in col_order]).limit(3)
                sample_rows = conn.execute(sample_query).fetchall()

                # ── Unpack results ──
                idx = 0
                for i, col_name in enumerate(col_order):
                    null_count = int(agg_row[idx] or 0); idx += 1
                    unique_count = int(agg_row[idx] or 0); idx += 1
                    null_percentage = round((null_count / row_count) * 100, 2)
                    unique_percentage = round((unique_count / row_count) * 100, 2)

                    samples = [
                        str(row[i]) for row in sample_rows
                        if row[i] is not None
                    ][:3]

                    col_stat: ColumnStats = {
                        "null_count": null_count,
                        "null_percentage": null_percentage,
                        "unique_count": unique_count,
                        "unique_percentage": unique_percentage,
                        "sample_values": samples,
                        "min_value": None,
                        "max_value": None,
                        "mean_value": None
                    }
                    
                    if numeric_flags[i]:
                        try:
                            min_v = agg_row[idx]; idx += 1
                            max_v = agg_row[idx]; idx += 1
                            avg_v = agg_row[idx]; idx += 1
                            col_stat["min_value"] = float(min_v) if min_v is not None else None
                            col_stat["max_value"] = float(max_v) if max_v is not None else None
                            col_stat["mean_value"] = round(float(avg_v), 4) if avg_v is not None else None
                            if min_v is not None and min_v < 0 and "ID" in col_name.upper():
                                health_score -= 5
                        except Exception:
                            idx += 3
                    
                    stats_out[col_name] = col_stat
                    
                    if null_percentage > 10.0:
                        health_score -= 2.5
                    if null_percentage > 50.0:
                        health_score -= 5.0

        except SQLAlchemyError as e:
            return row_count, health_score, stats_out

        return row_count, max(0.0, health_score), stats_out
