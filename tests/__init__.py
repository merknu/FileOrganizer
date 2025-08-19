"""
Test package for FileOrganizer application.

This package contains comprehensive tests for all components:
- Unit tests for core logic and utilities
- Integration tests for component interactions
- GUI tests for PyQt5 components
"""

import os
import sys

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)