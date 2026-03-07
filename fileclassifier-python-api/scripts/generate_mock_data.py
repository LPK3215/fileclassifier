from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def main() -> int:
    from fileclassifier.services.mock_data import generate_mock_dataset

    manifest = generate_mock_dataset(PROJECT_ROOT / "data")
    print(f"Excel: {manifest['excel_path']}")
    print(f"Input: {manifest['input_dir']}")
    print(f"Output: {manifest['output_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
