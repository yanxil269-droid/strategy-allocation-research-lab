"""Run from the repository root: python run_report.py --help."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from evaluate import main
if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError, FileExistsError, KeyError) as exc:
        print(f"Input/run error: {exc}\nCheck the input contract and choose a NEW output directory; see README.md.", file=sys.stderr)
        sys.exit(2)
