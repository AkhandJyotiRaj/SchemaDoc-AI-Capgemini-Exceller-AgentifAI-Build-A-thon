"""
Pytest configuration for SchemaDoc AI backend tests.
"""
import sys
from pathlib import Path

# Ensure the project root is on sys.path so all imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
