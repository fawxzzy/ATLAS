from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, load_repo_registry

REPORT_VERSION = "atlas.vercel_hobby_guardrail.v1"
THRESHOLDS_REVALIDATED_ON = "2026-06-17"
HOBBY_THRESHOLDS = {
    "edge_requests_per_month": 1_000_000,
    "fast_data_transfer_gb_per_month": 100,
    "function_invocations_per_month": 1_000_000,
    "active_cpu_hours_per_month": 4,
    "provisioned_memory_gb_hours_per_month": 360,
    "build_execution_minutes": 6000,
    "speed_insights_points_per_month": 10_000,
    "web_analytics_events_per_month": 50_000,
    "runtime_log_retention_hours": 1,
}
ROUTE_METHOD_PATTERN = re.compile(r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS)\b")
RUNTIME_PATTERN = re.compile(r'export\s+const\s+runtime\s*=\s*["\']([^"\']+)["\']')
DYNAMIC_PATTERN = re.compile(r'export\s+const\s+dynamic\s*=\s*["\']([^"\']+)["\']')
FETCH_PATTERN = re.compile(r"fetch\s*\(")
STRING_LITERAL_FETCH_PATTERN = re.compile(r'fetch\s*\(\s*["\']([^"\']+)["\']')
PUBLIC_AUTHLESS_PATHS_PATTERN = re.compile(r'"/api/[^"]+"')
WATCH_TARGETS = (
    "/api/discord/interactions",
    "/auth/session-keepalive",
    "/api/app-version",
    "/auth/session-sync",
    "/api/history/sessions",
    "/api/history/exercises",
    "/api/sessions/start",
    "/api/sessions/resume",
    "/api/account/export",
    "/api/account/export/preview",
    "/api/migration/export",
    "/api/migration/import",
    "/api/migration/parity",
    "/api/discord/verification-token",
    "/api/ecosystem/fitness/pilot-shadow",
    "/api/exercise-info/",
)


class GuardrailReportError(RuntimeError):
    pass


@dataclass(frozen=True)
class RouteRecord:
    route: str
    methods: tuple[str, ...]
    runtime: str | None
    dynamic: str | None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _route_from_path(app_root: Path, route_path: Path) -> str:
    relative = route_path.relative_to(app_root).as_posix()
    route = "/" + relative.removesuffix("/route.ts").removesuffix("/route.js")
    return route


def _collect_route_records(repo_root: Path) -> list[RouteRecord]:
    app_root = repo_root / "src" / "app"
    if not app_root.exists():
        raise GuardrailReportError(f"Missing app root: {atlas_relative(app_root)}")

    records: list[RouteRecord] = []
    for route_path in sorted(app_root.rglob("route.ts")) + sorted(app_root.rglob("route.js")):
        text = _read_text(route_path)
        methods = tuple(sorted({match.group(1) for match in ROUTE_METHOD_PATTERN.finditer(text)}))
        runtime_match = RUNTIME_PATTERN.search(text)
        dynamic_match = DYNAMIC_PATTERN.search(text)
        records.append(
            RouteRecord(
                route=_route_from_path(app_root, route_path),
                methods=methods,
                runtime=runtime_match.group(1) if runtime_match else None,
                dynamic=dynamic_match.group(1) if dynamic_match else None,
            )
        )
    if not records:
        raise GuardrailReportError(f"No route handlers found under {atlas_relative(app_root)}")
    return records


def _collect_fetch_inventory(repo_root: Path) -> dict[str, Any]:
    src_root = repo_root / "src"
    fetch_records: list[dict[str, str]] = []
    for file_path in sorted(src_root.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        if ".test." in file_path.name or file_path.name.endswith(".contract.test.ts"):
            continue
        text = _read_text(file_path)
        if "fetch(" not in text:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "fetch(" not in line:
                continue
            target_match = STRING_LITERAL_FETCH_PATTERN.search(line)
            target = target_match.group(1) if target_match else "<dynamic>"
            classification = "internal" if target.startswith("/") else "external_or_dynamic"
            fetch_records.append(
                {
                    "file": file_path.relative_to(repo_root).as_posix(),
                    "line": str(line_number),
                    "target": target,
                    "classification": classification,
                }
            )
    total = len(fetch_records)
    internal = sum(1 for record in fetch_records if record["classification"] == "internal")
    external_or_dynamic = total - internal
    return {
        "total_fetch_sites": total,
        "internal_fetch_sites": internal,
        "external_or_dynamic_fetch_sites": external_or_dynamic,
        "records": fetch_records,
    }


def _collect_watch_targets(repo_root: Path) -> list[dict[str, Any]]:
    src_root = repo_root / "src"
    targets: list[dict[str, Any]] = []
    for target in WATCH_TARGETS:
        files: set[str] = set()
        references = 0
        for file_path in sorted(src_root.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            if ".test." in file_path.name or file_path.name.endswith(".contract.test.ts"):
                continue
            text = _read_text(file_path)
            count = text.count(target)
            if count:
                references += count
                files.add(file_path.relative_to(repo_root).as_posix())
        if references:
            targets.append(
                {
                    "target": target,
                    "references": references,
                    "files": sorted(files),
                }
            )
    return targets


def _collect_middleware_inventory(repo_root: Path) -> dict[str, Any]:
    middleware_path = repo_root / "src" / "middleware.ts"
    if not middleware_path.exists():
        return {
            "present": False,
            "path": atlas_relative(middleware_path),
            "public_authless_paths": [],
            "has_broad_non_static_matcher": False,
            "refresh_session_call_present": False,
        }

    text = _read_text(middleware_path)
    auth_session_path = repo_root / "src" / "lib" / "auth-session.ts"
    public_authless_paths: list[str] = []
    if auth_session_path.exists():
        auth_session_text = _read_text(auth_session_path)
        public_authless_paths = sorted(
            {
                value.strip('"')
                for value in PUBLIC_AUTHLESS_PATHS_PATTERN.findall(auth_session_text)
            }
        )
    return {
        "present": True,
        "path": atlas_relative(middleware_path),
        "public_authless_paths": public_authless_paths,
        "has_broad_non_static_matcher": "_next/static|_next/image|favicon.ico" in text,
        "refresh_session_call_present": "recoverSupabaseSessionFromCookies" in text,
    }


def _load_project_link(repo_root: Path) -> dict[str, str]:
    project_path = repo_root / ".vercel" / "project.json"
    if not project_path.exists():
        raise GuardrailReportError(f"Missing Vercel link file: {atlas_relative(project_path)}")
    payload = json.loads(_read_text(project_path))
    project_id = payload.get("projectId")
    team_id = payload.get("orgId")
    project_name = payload.get("projectName")
    if not all(isinstance(value, str) and value.strip() for value in (project_id, team_id, project_name)):
        raise GuardrailReportError(f"Malformed Vercel link file: {atlas_relative(project_path)}")
    return {
        "project_id": project_id.strip(),
        "team_id": team_id.strip(),
        "project_name": project_name.strip(),
        "path": atlas_relative(project_path),
    }


def _load_vercel_config(repo_root: Path) -> dict[str, Any]:
    vercel_path = repo_root / "vercel.json"
    if not vercel_path.exists():
        return {
            "present": False,
            "path": atlas_relative(vercel_path),
            "deployment_enabled": None,
        }
    payload = json.loads(_read_text(vercel_path))
    git_config = payload.get("git") if isinstance(payload.get("git"), dict) else {}
    deployment_enabled = git_config.get("deploymentEnabled")
    return {
        "present": True,
        "path": atlas_relative(vercel_path),
        "deployment_enabled": deployment_enabled if isinstance(deployment_enabled, bool) else None,
    }


def build_report(*, root: Path, repo_id: str) -> dict[str, Any]:
    registry = load_repo_registry(root=root)
    if repo_id not in registry:
        raise GuardrailReportError(f"Unknown repo id: {repo_id}")
    repo_entry = registry[repo_id]
    repo_root = repo_entry.root
    project_link = _load_project_link(repo_root)
    vercel_config = _load_vercel_config(repo_root)
    route_records = _collect_route_records(repo_root)
    fetch_inventory = _collect_fetch_inventory(repo_root)
    middleware_inventory = _collect_middleware_inventory(repo_root)
    watch_targets = _collect_watch_targets(repo_root)

    method_counts: dict[str, int] = {key: 0 for key in ("GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS")}
    api_routes = 0
    auth_routes = 0
    dev_routes = 0
    nodejs_routes: list[str] = []
    force_dynamic_routes = 0
    for record in route_records:
        if record.route.startswith("/api/"):
            api_routes += 1
        elif record.route.startswith("/auth/"):
            auth_routes += 1
        elif record.route.startswith("/dev/"):
            dev_routes += 1
        for method in record.methods:
            method_counts[method] += 1
        if record.runtime == "nodejs":
            nodejs_routes.append(record.route)
        if record.dynamic == "force-dynamic":
            force_dynamic_routes += 1

    route_pressure_posture = "watch" if force_dynamic_routes >= max(1, len(route_records) // 2) else "ok"
    middleware_pressure_posture = "watch" if middleware_inventory["present"] and middleware_inventory["has_broad_non_static_matcher"] else "ok"
    deployment_posture = "ok" if vercel_config["deployment_enabled"] is False else "watch"
    integration_pressure_posture = "watch" if fetch_inventory["external_or_dynamic_fetch_sites"] > 0 else "ok"
    hot_route_watch_posture = "watch" if any(target["target"] == "/api/discord/interactions" for target in watch_targets) else "unknown"

    summary = {
        "total_routes": len(route_records),
        "api_routes": api_routes,
        "auth_routes": auth_routes,
        "dev_routes": dev_routes,
        "force_dynamic_routes": force_dynamic_routes,
        "nodejs_routes": len(nodejs_routes),
        "method_counts": method_counts,
        "fetch_inventory": {
            "total_fetch_sites": fetch_inventory["total_fetch_sites"],
            "internal_fetch_sites": fetch_inventory["internal_fetch_sites"],
            "external_or_dynamic_fetch_sites": fetch_inventory["external_or_dynamic_fetch_sites"],
        },
    }

    return {
        "report_version": REPORT_VERSION,
        "report_id": f"vercel-hobby-guardrail-{repo_id}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_id": repo_id,
        "repo_path": atlas_relative(repo_root, root=root),
        "project_link": project_link,
        "vercel_config": vercel_config,
        "thresholds_revalidated_on": THRESHOLDS_REVALIDATED_ON,
        "hobby_thresholds": HOBBY_THRESHOLDS,
        "summary": summary,
        "middleware_inventory": middleware_inventory,
        "nodejs_routes": nodejs_routes,
        "watch_targets": watch_targets,
        "guardrail_posture": {
            "deployment_posture": deployment_posture,
            "route_pressure_posture": route_pressure_posture,
            "middleware_pressure_posture": middleware_pressure_posture,
            "integration_pressure_posture": integration_pressure_posture,
            "hot_route_watch_posture": hot_route_watch_posture,
        },
        "notes": [
            "This report is repo-local and no-secret by design; it does not read live billing counters.",
            "Threshold values are local checkpoint constants last revalidated on 2026-06-17.",
            "Watch postures are governance hints, not spend claims or upgrade recommendations.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Vercel Hobby Guardrail Report",
        "",
        f"- report id: `{report['report_id']}`",
        f"- generated at: `{report['generated_at']}`",
        f"- repo id: `{report['repo_id']}`",
        f"- repo path: `{report['repo_path']}`",
        f"- project id: `{report['project_link']['project_id']}`",
        f"- team id: `{report['project_link']['team_id']}`",
        f"- thresholds revalidated on: `{report['thresholds_revalidated_on']}`",
        "",
        "## Summary",
        "",
        f"- total routes: `{report['summary']['total_routes']}`",
        f"- api routes: `{report['summary']['api_routes']}`",
        f"- auth routes: `{report['summary']['auth_routes']}`",
        f"- dev routes: `{report['summary']['dev_routes']}`",
        f"- force-dynamic routes: `{report['summary']['force_dynamic_routes']}`",
        f"- explicit nodejs routes: `{report['summary']['nodejs_routes']}`",
        f"- fetch sites: `{report['summary']['fetch_inventory']['total_fetch_sites']}`",
        f"- internal fetch sites: `{report['summary']['fetch_inventory']['internal_fetch_sites']}`",
        f"- external-or-dynamic fetch sites: `{report['summary']['fetch_inventory']['external_or_dynamic_fetch_sites']}`",
        "",
        "## Guardrail Posture",
        "",
        f"- deployment posture: `{report['guardrail_posture']['deployment_posture']}`",
        f"- route pressure posture: `{report['guardrail_posture']['route_pressure_posture']}`",
        f"- middleware pressure posture: `{report['guardrail_posture']['middleware_pressure_posture']}`",
        f"- integration pressure posture: `{report['guardrail_posture']['integration_pressure_posture']}`",
        f"- hot route watch posture: `{report['guardrail_posture']['hot_route_watch_posture']}`",
        "",
        "## Middleware",
        "",
        f"- present: `{report['middleware_inventory']['present']}`",
        f"- broad non-static matcher: `{report['middleware_inventory']['has_broad_non_static_matcher']}`",
        f"- refresh-session call present: `{report['middleware_inventory']['refresh_session_call_present']}`",
    ]
    public_paths = report["middleware_inventory"]["public_authless_paths"]
    if public_paths:
        lines.append(f"- public authless paths: `{', '.join(public_paths)}`")
    else:
        lines.append("- public authless paths: `(none detected)`")
    lines.extend(
        [
            "",
            "## Node Routes",
            "",
        ]
    )
    if report["nodejs_routes"]:
        lines.extend(f"- `{route}`" for route in report["nodejs_routes"])
    else:
        lines.append("- `(none)`")
    lines.extend(
        [
            "",
            "## Watch Targets",
            "",
        ]
    )
    for record in report["watch_targets"]:
        lines.append(f"- `{record['target']}` refs: `{record['references']}`")
    lines.extend(
        [
            "",
            "## Notes",
            "",
        ]
    )
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a no-secret Vercel Hobby guardrail report from repo state.")
    parser.add_argument("--root", default=str(ROOT), help="ATLAS root path")
    parser.add_argument("--repo-id", default="fitness", help="Repo id from stack.yaml")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", help="Optional ATLAS-relative or absolute output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    report = build_report(root=root, repo_id=args.repo_id)
    rendered = json.dumps(report, indent=2) + "\n" if args.format == "json" else render_markdown(report)
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
