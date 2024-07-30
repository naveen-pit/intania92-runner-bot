"""Add the parent directory to the system path."""

import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent.resolve()

sys.path.append(str(parent_dir))
