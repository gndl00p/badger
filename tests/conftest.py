import sys
from pathlib import Path

_STUBS = Path(__file__).parent / "stubs"
if str(_STUBS) not in sys.path:
    sys.path.insert(0, str(_STUBS))
