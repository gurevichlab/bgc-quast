import sys
from pathlib import Path

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata  # type: ignore


def get_version() -> str:
    """
    Get the version of BGC-QUAST.
    Tries metadata.version("bgc-quast"), falling back to reading VERSION.txt.
    """
    try:
        return metadata.version("bgc-quast")
    except metadata.PackageNotFoundError:
        project_root = Path(__file__).resolve().parents[1]
        version_file = project_root / "VERSION.txt"
        try:
            return version_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return "unknown"
