import sys
from pathlib import Path

from samples.video_example import main as run

BASE_DIR = Path(__file__).parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


def main():
    run()


if __name__ == "__main__":
    main()
