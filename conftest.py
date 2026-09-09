import os
import sys

# Make sure the project root (where app.py lives) is always importable,
# regardless of which directory pytest is invoked from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
