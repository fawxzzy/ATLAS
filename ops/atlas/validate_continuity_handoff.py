from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.continuity import validate_continuity_handoff


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an ATLAS continuity handoff artifact.")
    parser.add_argument("--handoff-file", required=True, help="Path to the continuity handoff JSON file.")
    args = parser.parse_args()

    handoff_path = Path(args.handoff_file)
    payload = json.loads(handoff_path.read_text(encoding="utf-8-sig"))
    errors = validate_continuity_handoff(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "handoff_file": handoff_path.as_posix(),
                "artifact_id": payload.get("artifact_id"),
                "repo_ref_count": len(payload.get("repo_refs", [])),
                "initiative_ref_count": len(payload.get("initiative_refs", [])),
                "promotion_target_count": len(payload.get("promotion_targets", [])),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
