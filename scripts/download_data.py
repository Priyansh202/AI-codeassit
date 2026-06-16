"""Download the Kaggle Stack Overflow Python Q&A dataset."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def download_dataset(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import kaggle  # type: ignore
    except ImportError:
        print("Installing kaggle CLI package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "kaggle"])
        import kaggle  # type: ignore

    archive = output_dir / "pythonquestions.zip"
    kaggle.api.dataset_download_files(
        "stackoverflow/pythonquestions",
        path=str(output_dir),
        quiet=False,
    )

    csv_files = list(output_dir.glob("*.csv"))
    if csv_files:
        return csv_files[0]

    zip_files = list(output_dir.glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError("Kaggle download did not produce a CSV or ZIP file")

    extract_dir = output_dir / "raw"
    extract_dir.mkdir(exist_ok=True)
    shutil.unpack_archive(str(zip_files[0]), extract_dir)
    csv_files = list(extract_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("No CSV file found after extracting Kaggle archive")
    return csv_files[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Stack Overflow Python Q&A dataset from Kaggle")
    parser.add_argument("--output-dir", default="data", help="Directory to store downloaded files")
    args = parser.parse_args()

    csv_path = download_dataset(Path(args.output_dir))
    print(f"Dataset ready at: {csv_path}")
    print("Set DATA_PATH in .env to this CSV before running scripts/build_index.py")


if __name__ == "__main__":
    main()
