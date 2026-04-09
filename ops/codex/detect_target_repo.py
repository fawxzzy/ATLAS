from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, discover_git_root, load_repo_registry, load_stack_config, normalize_slashes, path_is_within, repo_candidates_for_path


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_relative_path(value: str | None) -> str | None:
    if value is None:
        return None
    return normalize_slashes(value).strip()


def build_detection_result(
    *,
    explicit_repo_id: str | None,
    handoff_file: Path | None,
    workspace_root: str | None,
    repo_ids: list[str],
    changed_files: list[str],
) -> dict[str, Any]:
    root = atlas_root()
    config = load_stack_config(root / "stack.yaml")
    registry = load_repo_registry(config, root=root)
    reasons: list[str] = []
    evidence: list[dict[str, Any]] = []

    chosen_repo_id: str | None = None
    chosen_entry = None

    if explicit_repo_id:
        chosen_entry = registry.get(explicit_repo_id)
        if chosen_entry is None:
            return {
                "status": "invalid_repo_id",
                "repo_id": explicit_repo_id,
                "candidate_repo_ids": sorted(registry.keys()),
                "reasons": [f"Explicit repo id '{explicit_repo_id}' is not present in stack.yaml repo_registry."],
            }
        chosen_repo_id = explicit_repo_id
        reasons.append(f"Selected explicit repo id '{explicit_repo_id}'.")

    handoff_repo_ids = [item for item in repo_ids if item in registry]
    if not chosen_repo_id and len(set(handoff_repo_ids)) == 1:
        chosen_repo_id = handoff_repo_ids[0]
        chosen_entry = registry[chosen_repo_id]
        reasons.append(f"Selected the single repo id declared in handoff.repo_ids: '{chosen_repo_id}'.")
    elif not chosen_repo_id and len(set(handoff_repo_ids)) > 1:
        reasons.append("handoff.repo_ids names multiple repos, so file and workspace evidence must break the tie.")

    workspace_repo_ids: list[str] = []
    if workspace_root:
        workspace_root = normalize_relative_path(workspace_root)
        if workspace_root:
            workspace_candidates = repo_candidates_for_path(workspace_root, registry)
            workspace_repo_ids = [item.repo_id for item in workspace_candidates]
            evidence.append(
                {
                    "source": "workspace_root",
                    "value": workspace_root,
                    "candidate_repo_ids": workspace_repo_ids,
                }
            )
            if not chosen_repo_id and len(workspace_repo_ids) == 1:
                chosen_repo_id = workspace_repo_ids[0]
                chosen_entry = registry[chosen_repo_id]
                reasons.append(f"Selected repo '{chosen_repo_id}' because workspace_root lives under that repo.")

    file_hits: list[dict[str, Any]] = []
    file_counter: Counter[str] = Counter()
    outside_repo_paths: list[str] = []
    for relative_path in changed_files:
        normalized = normalize_relative_path(relative_path)
        if not normalized:
            continue
        candidates = repo_candidates_for_path(normalized, registry)
        candidate_ids = [item.repo_id for item in candidates]
        file_hits.append(
            {
                "path": normalized,
                "candidate_repo_ids": candidate_ids,
            }
        )
        if not candidate_ids:
            outside_repo_paths.append(normalized)
        elif len(candidate_ids) == 1:
            file_counter[candidate_ids[0]] += 1
        else:
            file_counter[candidate_ids[0]] += 1

    if file_hits:
        evidence.append({"source": "changed_files", "matches": file_hits})

    if not chosen_repo_id and len(file_counter) == 1:
        chosen_repo_id = next(iter(file_counter))
        chosen_entry = registry[chosen_repo_id]
        reasons.append(f"Selected repo '{chosen_repo_id}' because every changed file maps to that repo.")

    if not chosen_repo_id and file_counter:
        strongest_repo_id, strongest_count = file_counter.most_common(1)[0]
        tied_repo_ids = sorted(repo_id for repo_id, count in file_counter.items() if count == strongest_count)
        if len(tied_repo_ids) == 1:
            chosen_repo_id = strongest_repo_id
            chosen_entry = registry[chosen_repo_id]
            reasons.append(f"Selected repo '{chosen_repo_id}' from changed-file majority evidence.")
        else:
            reasons.append(f"Changed files map to multiple repos with the same weight: {', '.join(tied_repo_ids)}.")

    if chosen_repo_id and chosen_entry is None:
        chosen_entry = registry.get(chosen_repo_id)

    if chosen_entry is not None:
        if handoff_repo_ids and chosen_repo_id not in handoff_repo_ids:
            reasons.append(
                f"Resolved repo '{chosen_repo_id}' is not listed in handoff.repo_ids ({', '.join(handoff_repo_ids)})."
            )
            return {
                "status": "repo_mismatch",
                "repo_id": chosen_repo_id,
                "candidate_repo_ids": sorted(set(handoff_repo_ids + list(file_counter.keys()) + workspace_repo_ids)),
                "reasons": reasons,
                "evidence": evidence,
            }

        repo_root = chosen_entry.root.resolve()
        changed_outside_target = [
            item["path"]
            for item in file_hits
            if not path_is_within(root / Path(item["path"]), repo_root)
        ]
        if changed_outside_target:
            reasons.append("Some changed files are outside the resolved repo root.")
            return {
                "status": "mixed_scope",
                "repo_id": chosen_repo_id,
                "repo_root": normalize_slashes(str(repo_root)),
                "repo_root_atlas_path": atlas_relative(repo_root, root=root),
                "changed_files_outside_repo": changed_outside_target,
                "candidate_repo_ids": sorted(set([chosen_repo_id] + handoff_repo_ids + workspace_repo_ids + list(file_counter.keys()))),
                "reasons": reasons,
                "evidence": evidence,
            }

        git_root = discover_git_root(repo_root)
        git_ready = git_root is not None and git_root == repo_root
        if not git_ready:
            reasons.append("Resolved repo path exists but is not the root of a usable git checkout.")

        status = "resolved" if git_ready else "git_unavailable"
        return {
            "status": status,
            "repo_id": chosen_repo_id,
            "repo_root": normalize_slashes(str(repo_root)),
            "repo_root_atlas_path": atlas_relative(repo_root, root=root),
            "git_root": normalize_slashes(str(git_root)) if git_root else None,
            "git_ready": git_ready,
            "candidate_repo_ids": sorted(set([chosen_repo_id] + handoff_repo_ids + workspace_repo_ids + list(file_counter.keys()))),
            "changed_files_outside_repo": [],
            "changed_files_without_repo": outside_repo_paths,
            "reasons": reasons,
            "evidence": evidence,
            "source_handoff": normalize_slashes(str(handoff_file)) if handoff_file else None,
        }

    status = "no_repo_detected" if outside_repo_paths or not (workspace_repo_ids or file_counter or handoff_repo_ids) else "ambiguous"
    if outside_repo_paths:
        reasons.append("Changed files include stack-level paths that are outside any registered repo root.")
    elif handoff_repo_ids:
        reasons.append("handoff.repo_ids did not narrow to a single repo.")
    else:
        reasons.append("No changed-file or workspace evidence mapped to a registered repo.")
    return {
        "status": status,
        "repo_id": None,
        "candidate_repo_ids": sorted(set(handoff_repo_ids + workspace_repo_ids + list(file_counter.keys()))),
        "changed_files_without_repo": outside_repo_paths,
        "reasons": reasons,
        "evidence": evidence,
        "source_handoff": normalize_slashes(str(handoff_file)) if handoff_file else None,
    }


def print_preview(payload: dict[str, Any]) -> None:
    print(f"Status         : {payload['status']}")
    print(f"Repo id        : {payload.get('repo_id') or '<none>'}")
    if payload.get("repo_root_atlas_path"):
        print(f"Repo root      : {payload['repo_root_atlas_path']}")
    print(f"Candidates     : {', '.join(payload.get('candidate_repo_ids') or ['<none>'])}")
    without_repo = payload.get("changed_files_without_repo") or []
    if without_repo:
        print("Outside repo   :")
        for item in without_repo:
            print(f"  - {item}")
    for reason in payload.get("reasons") or []:
        print(f"Reason         : {reason}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve the owning git repo for a Codex handoff.")
    parser.add_argument("--handoff-file")
    parser.add_argument("--repo-id")
    parser.add_argument("--workspace-root")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args(argv)

    handoff_path: Path | None = None
    repo_ids: list[str] = []
    changed_files = [normalize_relative_path(item) for item in args.changed_file if normalize_relative_path(item)]
    workspace_root = normalize_relative_path(args.workspace_root) if args.workspace_root else None

    if args.handoff_file:
        handoff_path = Path(args.handoff_file).resolve()
        if not handoff_path.exists():
            print(json.dumps({"status": "missing_handoff", "reasons": [f"Handoff file not found: {normalize_slashes(str(handoff_path))}"]}, indent=2))
            return 1
        payload = load_json(handoff_path)
        if not isinstance(payload, dict):
            print(json.dumps({"status": "invalid_handoff", "reasons": ["Handoff must deserialize to a JSON object."]}, indent=2))
            return 1
        if workspace_root is None and isinstance(payload.get("workspace_root"), str):
            workspace_root = payload["workspace_root"]
        if not changed_files:
            for item in payload.get("changed_files", []):
                if isinstance(item, dict) and isinstance(item.get("path"), str):
                    changed_files.append(item["path"])
        for item in payload.get("repo_ids", []) or []:
            if isinstance(item, str):
                repo_ids.append(item)

    result = build_detection_result(
        explicit_repo_id=args.repo_id,
        handoff_file=handoff_path,
        workspace_root=workspace_root,
        repo_ids=repo_ids,
        changed_files=changed_files,
    )
    print(json.dumps(result, indent=2))
    if args.preview:
        print("")
        print_preview(result)
    return 0 if result.get("status") in {"resolved", "git_unavailable", "no_repo_detected"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
