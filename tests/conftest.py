import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"
sys.path[:0] = [str(PROJECT_ROOT), str(SOURCE_ROOT)]

# Model clients are constructed when graph nodes are imported. Unit tests mock
# every model invocation, so a non-secret placeholder keeps collection local.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
