"""
Shared utility helpers for the SchemaDoc AI backend.
Consolidates common patterns (e.g., JSON encoding) that were
previously duplicated across multiple modules.
"""
import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """
    JSON encoder that converts Decimal values to float.

    BEFORE (duplicated in 4+ files):
        # In chat.py, schema.py, export.py, pipeline_service.py — each had its own copy:
        class DecimalEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                return super().default(obj)

    AFTER (single source of truth):
        from backend.core.utils import DecimalEncoder
        json.dumps(data, cls=DecimalEncoder)

    WHY: Eliminates 4 duplicate class definitions. If encoding logic ever needs to
    handle additional types (e.g., datetime, UUID), we change it in ONE place.
    """

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def safe_json_dumps(data, **kwargs) -> str:
    """Convenience wrapper that always uses DecimalEncoder."""
    return json.dumps(data, cls=DecimalEncoder, **kwargs)
