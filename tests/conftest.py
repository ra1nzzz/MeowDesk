"""Pytest configuration for MeowDesk.

Make the project root importable so tests can import ``meowdesk``
regardless of where pytest is invoked from.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ignore the legacy top-level smoke-test scripts that exit() on import.
# They were designed for ad-hoc execution (``python test_xxx.py``), not
# for pytest collection, and they call ``sys.exit(1)`` on non-target
# platforms.
collect_ignore = [
    os.path.join(PROJECT_ROOT, "test_cross_platform.py"),
    os.path.join(PROJECT_ROOT, "test_exe_debug.py"),
    os.path.join(PROJECT_ROOT, "test_macos.py"),
    os.path.join(PROJECT_ROOT, "test_windows_features.py"),
]
