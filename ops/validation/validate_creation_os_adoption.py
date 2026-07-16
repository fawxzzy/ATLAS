#!/usr/bin/env python3
"""Fail-closed validation for the governed Atlas Creation OS research adoption."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
IMPORT_DIR = ROOT / "data/imports/creation-os/deep-research-2026-07-16"
MANIFEST_PATH = IMPORT_DIR / "IMPORT-MANIFEST.json"
RAW_PATH = IMPORT_DIR / "deep-research-report.md"
REGISTRY_PATH = ROOT / "docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json"

EXPECTED_SHA256 = "6d3ecbfba3cb22e9a29a30d00befaf7c4ac04720b8a619fc19a8e61e6f52fe8f"
EXPECTED_BYTES = 39592
EXPECTED_LINES = 415
EXPECTED_STORED_REF = "data/imports/creation-os/deep-research-2026-07-16/deep-research-report.md"

REQUIRED_CANDIDATE_IDS = (
    "lane-creation-os-product-definition-first-wedge",
    "lane-atlas-bootstrap-manifest-recovery-pointer",
    "lane-durable-memory-fabric-context-compaction",
    "lane-repository-ingestion-compatibility-graph",
    "lane-deterministic-builder-loop",
    "lane-conversational-realtime-creative-loop",
    "lane-spatial-blueprint-surface",
    "lane-device-gateway-safe-actuation",
    "lane-policy-tracing-evaluation-artifact-trust",
    "lane-pmf-monetization-success-kill-criteria",
)

CANONICAL_REFS = (
    "data/imports/creation-os/deep-research-2026-07-16/.gitattributes",
    "data/imports/creation-os/deep-research-2026-07-16/IMPORT-MANIFEST.json",
    "docs/audits/ATLAS-CREATION-OS-RESEARCH-RECONCILIATION-2026-07-16.md",
    "docs/architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md",
    "docs/atlas-book/INDEX.md",
    "docs/atlas-book/README.md",
    "docs/atlas-book/17-creation-os-target-architecture.md",
    "docs/atlas/decisions/adr-signed-versioned-atlas-bootstrap-manifest.md",
    "docs/ops/ATLAS-CREATION-OS-PLAYBOOK-PROMOTION-CANDIDATES-2026-07-16.md",
    "docs/registry/project-board-owner-exports/atlas.project-board.owner-export.v1.json",
    "docs/registry/project-board-owner-exports/cortex.project-board.owner-export.v1.json",
    "ops/atlas/test_project_board_owner_export.py",
    "ops/validation/validate_creation_os_adoption.py",
)

MOJIBAKE_FRAGMENTS = (
    "\u00e2\u20ac",
    "\u00c3",
    "\u00c2",
    "\ufffd",
)


def _load_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot load JSON {path.relative_to(ROOT).as_posix()}: {exc}")
        return {}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _line_count(data: bytes) -> int:
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def _is_portable_ref(value: str) -> bool:
    if PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute():
        return False
    return all(part not in {"", ".", ".."} for part in PurePosixPath(value.replace("\\", "/")).parts)


def _validate_raw_import(manifest: dict[str, Any], source: Path | None, errors: list[str]) -> None:
    try:
        raw = RAW_PATH.read_bytes()
    except OSError as exc:
        errors.append(f"cannot read stored raw import: {exc}")
        return

    actual_sha = _sha256(raw)
    actual_bytes = len(raw)
    actual_lines = _line_count(raw)
    expected_manifest = {
        "stored_ref": EXPECTED_STORED_REF,
        "source_sha256": EXPECTED_SHA256,
        "stored_sha256": EXPECTED_SHA256,
        "byte_length": EXPECTED_BYTES,
        "line_count": EXPECTED_LINES,
        "trust_classification": "external-research-input",
        "review_status": "reconciled-not-canonical",
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) != expected:
            errors.append(f"manifest {key} must be {expected!r}, found {manifest.get(key)!r}")

    if actual_sha != EXPECTED_SHA256:
        errors.append(f"stored raw SHA-256 mismatch: {actual_sha}")
    if actual_bytes != EXPECTED_BYTES:
        errors.append(f"stored raw byte length mismatch: {actual_bytes}")
    if actual_lines != EXPECTED_LINES:
        errors.append(f"stored raw line count mismatch: {actual_lines}")

    if source is not None:
        try:
            source_raw = source.read_bytes()
        except OSError as exc:
            errors.append(f"cannot read operator source {source}: {exc}")
        else:
            if source_raw != raw:
                errors.append("stored raw import is not byte-identical to the operator source")
            if _sha256(source_raw) != EXPECTED_SHA256:
                errors.append("operator source SHA-256 does not match the admitted digest")
            if len(source_raw) != EXPECTED_BYTES:
                errors.append("operator source byte length does not match the admitted length")
            if _line_count(source_raw) != EXPECTED_LINES:
                errors.append("operator source line count does not match the admitted count")


def _validate_derived_refs(manifest: dict[str, Any], errors: list[str]) -> None:
    refs = manifest.get("derived_artifacts")
    if not isinstance(refs, list) or not refs:
        errors.append("manifest derived_artifacts must be a non-empty array")
        return
    for ref in refs:
        if not isinstance(ref, str) or not _is_portable_ref(ref):
            errors.append(f"derived artifact ref is not portable: {ref!r}")
            continue
        if not (ROOT / ref).is_file():
            errors.append(f"derived artifact does not exist: {ref}")


def _validate_candidate_lanes(registry: dict[str, Any], errors: list[str]) -> None:
    lanes = registry.get("lanes")
    backlog = registry.get("backlog_candidates")
    if not isinstance(lanes, list) or not isinstance(backlog, list):
        errors.append("lane registry must contain lanes and backlog_candidates arrays")
        return

    all_records = [record for record in [*lanes, *backlog] if isinstance(record, dict)]
    by_id = {record.get("id"): record for record in all_records}
    if len(by_id) != len(all_records):
        errors.append("lane registry contains a missing or duplicate id")

    for lane_id in REQUIRED_CANDIDATE_IDS:
        record = by_id.get(lane_id)
        if not isinstance(record, dict):
            errors.append(f"required Creation OS candidate lane is missing: {lane_id}")
            continue
        if record not in backlog:
            errors.append(f"Creation OS candidate must remain in backlog_candidates: {lane_id}")
        if record.get("status") != "candidate":
            errors.append(f"{lane_id} status must be candidate")
        if record.get("percentage") is not None:
            errors.append(f"{lane_id} percentage must remain null")
        if record.get("completed_units") is not None:
            errors.append(f"{lane_id} completed_units numerator must remain null")
        denominator = record.get("denominator")
        if not isinstance(denominator, dict) or denominator.get("value") is not None:
            errors.append(f"{lane_id} denominator.value must remain null")
        for key in (
            "title",
            "scope",
            "measurement_unit",
            "evidence_sources",
            "definition_of_done",
            "automation_opportunity",
            "program_links",
        ):
            if key not in record or record.get(key) in (None, "", []):
                errors.append(f"{lane_id} is missing required field {key}")
        if "dependencies" not in record or not isinstance(record.get("dependencies"), list):
            errors.append(f"{lane_id} dependencies must be an array")
        for dependency in record.get("dependencies", []):
            if dependency not in by_id:
                errors.append(f"{lane_id} references unknown dependency {dependency}")
        for related_lane in record.get("related_lanes", []):
            if related_lane not in by_id:
                errors.append(f"{lane_id} references unknown related lane {related_lane}")
        for ref in record.get("evidence_sources", []):
            if not isinstance(ref, str) or not _is_portable_ref(ref.split("#", 1)[0]):
                errors.append(f"{lane_id} contains a non-portable evidence ref: {ref!r}")
                continue
            if not (ROOT / ref.split("#", 1)[0]).exists():
                errors.append(f"{lane_id} evidence ref does not exist: {ref}")
        program_links = record.get("program_links")
        if isinstance(program_links, dict):
            for key in ("clean_and_resync", "pre_development_gate", "post_preparation_development"):
                value = program_links.get(key)
                if not isinstance(value, str) or not value:
                    errors.append(f"{lane_id} program_links.{key} must be a non-empty ref")
                    continue
                if not _is_portable_ref(value.split("#", 1)[0]) or not (ROOT / value.split("#", 1)[0]).exists():
                    errors.append(f"{lane_id} program_links.{key} is not a valid local ref: {value}")


def _validate_canonical_text(ref: str, text: str, errors: list[str]) -> None:
    absolute_pattern = re.compile(r"(?:(?<![A-Za-z])[A-Za-z]:[\\/]|/" + "Users/|/" + "home/)")
    try:
        text.encode("ascii")
    except UnicodeEncodeError as exc:
        errors.append(f"canonical artifact is not ASCII: {ref}: {exc}")
    if absolute_pattern.search(text):
        errors.append(f"canonical artifact contains a machine-specific absolute path: {ref}")
    for fragment in MOJIBAKE_FRAGMENTS:
        if fragment in text:
            errors.append(f"canonical artifact contains mojibake residue {fragment!r}: {ref}")
    if any(0xE000 <= ord(char) <= 0xF8FF for char in text):
        errors.append(f"canonical artifact contains private-use citation residue: {ref}")


def _validate_ascii_and_residue(errors: list[str]) -> None:
    for ref in CANONICAL_REFS:
        path = ROOT / ref
        if not path.is_file():
            errors.append(f"canonical artifact missing: {ref}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"cannot read canonical artifact as UTF-8: {ref}: {exc}")
            continue
        _validate_canonical_text(ref, text, errors)


def _validate_candidate_registry_residue(registry: dict[str, Any], errors: list[str]) -> None:
    records = registry.get("backlog_candidates")
    if not isinstance(records, list):
        return
    by_id = {record.get("id"): record for record in records if isinstance(record, dict)}
    registry_ref = REGISTRY_PATH.relative_to(ROOT).as_posix()
    for lane_id in REQUIRED_CANDIDATE_IDS:
        record = by_id.get(lane_id)
        if not isinstance(record, dict):
            continue
        text = json.dumps(record, ensure_ascii=False, sort_keys=True)
        _validate_canonical_text(f"{registry_ref}#{lane_id}", text, errors)


def _validate_markdown_links(errors: list[str]) -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for ref in CANONICAL_REFS:
        if not ref.endswith(".md"):
            continue
        path = ROOT / ref
        if not path.is_file():
            continue
        text = path.read_text(encoding="ascii")
        for target in link_pattern.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            base = target.split("#", 1)[0]
            if not base:
                continue
            resolved = (path.parent / base).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"Markdown link escapes the Atlas root in {ref}: {target}")
                continue
            if not resolved.exists():
                errors.append(f"broken Markdown link in {ref}: {target}")


def _validate_book_integration(errors: list[str]) -> None:
    index = (ROOT / "docs/atlas-book/INDEX.md").read_text(encoding="utf-8")
    readme = (ROOT / "docs/atlas-book/README.md").read_text(encoding="utf-8")
    numbered = sorted((ROOT / "docs/atlas-book").glob("[0-9][0-9]-*.md"))
    expected_numbers = list(range(1, len(numbered) + 1))
    actual_numbers = [int(path.name.split("-", 1)[0]) for path in numbered]
    if actual_numbers != expected_numbers:
        errors.append(f"Atlas Book chapter numbering is not contiguous: {actual_numbers}")
    for path in numbered:
        number = int(path.name.split("-", 1)[0])
        filename = path.name
        if f"{number}. [" not in index or f"]({filename})" not in index:
            errors.append(f"Atlas Book index does not include chapter {number}: {filename}")
        if f"]({filename})" not in readme:
            errors.append(f"Atlas Book README does not include chapter {number}: {filename}")


def validate(source: Path | None) -> list[str]:
    errors: list[str] = []
    manifest = _load_json(MANIFEST_PATH, errors)
    registry = _load_json(REGISTRY_PATH, errors)
    if isinstance(manifest, dict):
        _validate_raw_import(manifest, source, errors)
        _validate_derived_refs(manifest, errors)
    if isinstance(registry, dict):
        _validate_candidate_lanes(registry, errors)
        _validate_candidate_registry_residue(registry, errors)
    _validate_ascii_and_residue(errors)
    _validate_markdown_links(errors)
    _validate_book_integration(errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        help="Optional operator source path; when supplied it must match the governed raw import byte-for-byte.",
    )
    args = parser.parse_args()
    errors = validate(args.source)
    if errors:
        print(json.dumps({"status": "error", "errors": errors}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": "ok",
                "source_compared": args.source is not None,
                "sha256": EXPECTED_SHA256,
                "bytes": EXPECTED_BYTES,
                "lines": EXPECTED_LINES,
                "candidate_lane_count": len(REQUIRED_CANDIDATE_IDS),
                "candidate_percentages": "unmeasured",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
