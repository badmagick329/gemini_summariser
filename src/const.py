import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = Path(__file__).parent.parent / "data"

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


SAMPLE_MD = DATA_DIR / "sample_md.md"
