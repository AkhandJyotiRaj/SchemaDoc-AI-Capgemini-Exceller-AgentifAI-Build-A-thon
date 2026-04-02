import os
import re
import logging
from typing import List, Optional
from src.core.config import AppConfig

logger = logging.getLogger(__name__)

class UsageSearchService:
    """Scans application/database logs for forensic evidence of column usage."""

    def __init__(self, log_filename: str = "usage_logs.sql"):
        self.log_path = AppConfig.DATA_DIR / log_filename

    def search_column_usage(self, column_name: str) -> str:
        """
        scan the log file for any SQL queries that use the specific column name.
        and give the exact lines of code where the col appears.
        """
        if not self.log_path.exists():
            # fail silently for the llm's sake, but log for dev
            logger.warning(f"Log file not found at: {self.log_path}")
            return f"System Note: Log file '{self.log_path.name}' not found. No usage data available."

        evidence: List[str] = []
        
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    # regex word boundary to avoid partial matches (e.g. 'id' matching 'user_id')
                    if re.search(r'\b' + re.escape(column_name) + r'\b', line, re.IGNORECASE):
                        clean_line = line.strip()
                        if clean_line:
                            evidence.append(f"Line {i+1}: {clean_line}")
                
            if not evidence:
                return f"No usage found for '{column_name}' in analyzed logs."
                
            return "EVIDENCE FOUND IN LOGS:\n" + "\n".join(evidence[:10])

        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return f"System Error: Could not analyze logs due to {str(e)}"

usage_search = UsageSearchService()