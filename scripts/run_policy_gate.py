"""Run Conftest policy gate against evidence/manifest.json. Exits with Conftest's exit code."""
import subprocess
import sys
from pathlib import Path


def main() -> None:
    manifest = Path("evidence/manifest.json")
    if not manifest.exists():
        print(f"error: {manifest} not found; run evidence assembly first.", file=sys.stderr)
        sys.exit(1)
    result = subprocess.run(
        [
            "conftest",
            "test",
            str(manifest),
            "--policy",
            "policy",
            "--namespace",
            "evidence",
        ],
        cwd=Path(__file__).resolve().parent.parent,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
