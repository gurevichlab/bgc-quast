from pathlib import Path


def get_version() -> str:
    project_root = Path(__file__).resolve().parents[1]
    version_file = project_root / "VERSION.txt"

    try:
        return version_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "unknown"
