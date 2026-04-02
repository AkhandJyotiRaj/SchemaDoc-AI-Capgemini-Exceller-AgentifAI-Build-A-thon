"""
Forensic log search service — scans application logs for column usage evidence.
Ported from src/backend/services/usage_search.py with updated imports.
"""
import os
import re
import logging
from typing import List, Optional
from backend.core.config import settings

logger = logging.getLogger(__name__)


class UsageSearchService:
    """Scanning application or database logs for forensic evidence of column usage."""

    def __init__(self, log_filename: str = "usage_logs.sql"):
        self.log_path = settings.DATA_DIR / log_filename

    def search_column_usage(self, column_name: str) -> str:
        """
        Scan the log file for any SQL queries that use the specific column name.
        Returns the exact lines of code where the column appears.
        """
        if not self.log_path.exists():
            logger.warning(f"Log file not found at: {self.log_path}")
            return f"System Note: Log file '{self.log_path.name}' not found. No usage data available."

        evidence: List[str] = []

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if re.search(
                        r"\b" + re.escape(column_name) + r"\b", line, re.IGNORECASE
                    ):
                        clean_line = line.strip()
                        if clean_line:
                            evidence.append(f"Line {i + 1}: {clean_line}")

            if not evidence:
                return f"No usage found for '{column_name}' in analyzed logs."

            return "EVIDENCE FOUND IN LOGS:\n" + "\n".join(evidence[:10])

        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return f"System Error: Could not analyze logs due to {str(e)}"


# Singleton instance
usage_search = UsageSearchService()
