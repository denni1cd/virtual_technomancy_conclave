"""
Ensure the project root (this file’s parent directory) is on sys.path
so `import conclave ...` works regardless of where pytest is invoked.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
