from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .contracts import (
    canonical_json_bytes,
    canonical_sha256,
    normalize_nonvolatile,
    require_valid_contract,
    validate_contract,
)


def build_validation_report(document: Mapping[str, Any]) -> dict[str, Any]:
    errors = validate_contract(document)
    report: dict[str, Any] = {
        "report_version": "atlas.machine-validation-report.v1",
        "contract_version": document.get("contract_version"),
        "valid": not errors,
        "errors": errors,
        "document_digest": canonical_sha256(document),
    }
    if document.get("contract_version") == "atlas.machine-observed-state.v1" and not errors:
        report["nonvolatile_digest"] = canonical_sha256(normalize_nonvolatile(document))
    return report


def render_contract(document: Mapping[str, Any]) -> bytes:
    require_valid_contract(document)
    return canonical_json_bytes(document) + b"\n"


def render_validation_report(document: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(build_validation_report(document)) + b"\n"


def render_execution_receipt(receipt: Mapping[str, Any]) -> bytes:
    require_valid_contract(
        receipt,
        expected_contract_version="atlas.machine-execution-receipt.v1",
    )
    return canonical_json_bytes(receipt) + b"\n"


def write_sample_bundle(output_root: Path, observation: Mapping[str, Any]) -> dict[str, Any]:
    """Write a new content-addressed evidence bundle without overwriting prior evidence."""

    require_valid_contract(
        observation,
        expected_contract_version="atlas.machine-observed-state.v1",
    )
    observation_id = str(observation["observation_id"])
    run_directory = output_root.resolve() / observation_id
    if run_directory.exists():
        raise FileExistsError(f"Sample directory already exists: {run_directory}")
    run_directory.mkdir(parents=True, exist_ok=False)

    observed_bytes = render_contract(observation)
    report_bytes = render_validation_report(observation)
    outputs = {
        "observed-state.v1.json": observed_bytes,
        "validation-report.v1.json": report_bytes,
    }
    written: list[dict[str, Any]] = []
    for relative_name, content in outputs.items():
        destination = run_directory / relative_name
        with destination.open("xb") as stream:
            stream.write(content)
        written.append(
            {
                "path": relative_name,
                "bytes": len(content),
                "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
            }
        )

    manifest = {
        "manifest_version": "atlas.machine-sample-manifest.v1",
        "observation_id": observation_id,
        "source_contract": observation["contract_version"],
        "nonvolatile_digest": canonical_sha256(normalize_nonvolatile(observation)),
        "outputs": written,
        "machine_mutation_performed": False,
    }
    manifest_bytes = canonical_json_bytes(manifest) + b"\n"
    manifest_path = run_directory / "sample-manifest.v1.json"
    with manifest_path.open("xb") as stream:
        stream.write(manifest_bytes)
    manifest_output = {
        "path": manifest_path.name,
        "bytes": len(manifest_bytes),
        "sha256": "sha256:" + hashlib.sha256(manifest_bytes).hexdigest(),
    }
    return {
        "run_directory": str(run_directory),
        "manifest": manifest,
        "manifest_output": manifest_output,
    }


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object at {path}.")
    return payload
