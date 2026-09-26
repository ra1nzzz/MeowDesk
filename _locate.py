"""Backward-compatible protocol entry. Delegates to the app handler."""

import os
import runpy
import sys

root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.insert(0, root)
sys.argv = [os.path.join(root, "meowdesk_main.py"), "--locate", *sys.argv[1:]]
runpy.run_path(os.path.join(root, "meowdesk_main.py"), run_name="__main__")
