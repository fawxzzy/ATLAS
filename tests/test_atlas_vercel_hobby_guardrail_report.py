from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas.vercel_hobby_guardrail_report import GuardrailReportError, build_report, main


class AtlasVercelHobbyGuardrailReportTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "repos" / "fawxzzy-fitness" / ".vercel").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "fawxzzy-fitness" / "src" / "app" / "api" / "discord" / "interactions").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "fawxzzy-fitness" / "src" / "app" / "auth" / "session-sync").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "fawxzzy-fitness" / "src" / "components").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "fawxzzy-fitness" / "src" / "lib").mkdir(parents=True, exist_ok=True)
        (root / "docs").mkdir(exist_ok=True)
        (root / "ops").mkdir(exist_ok=True)
        (root / "stack.yaml").write_text(
            "\n".join(
                [
                    "repo_registry:",
                    "  fitness:",
                    "    path: repos/fawxzzy-fitness",
                    "    role: application",
                    "    status: unmanaged",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").write_text(
            json.dumps(
                {
                    "projectId": "prj_test",
                    "orgId": "team_test",
                    "projectName": "fawxzzy-fitness",
                }
            ),
            encoding="utf-8",
        )
        (root / "repos" / "fawxzzy-fitness" / "vercel.json").write_text(
            json.dumps({"git": {"deploymentEnabled": False}}),
            encoding="utf-8",
        )
        (root / "repos" / "fawxzzy-fitness" / "src" / "middleware.ts").write_text(
            "\n".join(
                [
                    'import { recoverSupabaseSessionFromCookies } from "@/lib/supabase/session-recovery";',
                    "export const config = {",
                    '  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],',
                    "};",
                ]
            ),
            encoding="utf-8",
        )
        (root / "repos" / "fawxzzy-fitness" / "src" / "lib" / "auth-session.ts").write_text(
            "\n".join(
                [
                    'const PUBLIC_AUTHLESS_PATHS = new Set([',
                    '  "/api/app-version",',
                    '  "/api/discord/interactions",',
                    "]);",
                ]
            ),
            encoding="utf-8",
        )
        (root / "repos" / "fawxzzy-fitness" / "src" / "app" / "api" / "discord" / "interactions" / "route.ts").write_text(
            "\n".join(
                [
                    'export const runtime = "nodejs";',
                    'export const dynamic = "force-dynamic";',
                    "export async function GET() { return Response.json({ ok: true }); }",
                    "export async function POST() { return Response.json({ ok: true }); }",
                ]
            ),
            encoding="utf-8",
        )
        (root / "repos" / "fawxzzy-fitness" / "src" / "app" / "auth" / "session-sync" / "route.ts").write_text(
            "\n".join(
                [
                    "export async function DELETE() { return Response.json({ ok: true }); }",
                ]
            ),
            encoding="utf-8",
        )
        (root / "repos" / "fawxzzy-fitness" / "src" / "components" / "ServiceWorkerBootstrap.tsx").write_text(
            "\n".join(
                [
                    'void fetch("/auth/session-keepalive", { method: "GET" });',
                    'void fetch("/api/app-version", { method: "GET" });',
                ]
            ),
            encoding="utf-8",
        )
        (root / "repos" / "fawxzzy-fitness" / "src" / "lib" / "spotify.ts").write_text(
            'await fetch("https://api.spotify.com/v1/me");\n',
            encoding="utf-8",
        )
        return root

    def test_build_report_collects_repo_local_guardrail_summary(self) -> None:
        root = self._temp_root()

        report = build_report(root=root, repo_id="fitness")

        self.assertEqual("atlas.vercel_hobby_guardrail.v1", report["report_version"])
        self.assertEqual("fitness", report["repo_id"])
        self.assertEqual("prj_test", report["project_link"]["project_id"])
        self.assertEqual(2, report["summary"]["total_routes"])
        self.assertEqual(1, report["summary"]["api_routes"])
        self.assertEqual(1, report["summary"]["auth_routes"])
        self.assertEqual(1, report["summary"]["nodejs_routes"])
        self.assertEqual(1, report["summary"]["force_dynamic_routes"])
        self.assertEqual(3, report["summary"]["fetch_inventory"]["total_fetch_sites"])
        self.assertEqual(2, report["summary"]["fetch_inventory"]["internal_fetch_sites"])
        self.assertEqual(1, report["summary"]["fetch_inventory"]["external_or_dynamic_fetch_sites"])
        self.assertEqual("ok", report["guardrail_posture"]["deployment_posture"])
        self.assertEqual("watch", report["guardrail_posture"]["middleware_pressure_posture"])
        self.assertIn("/api/discord/interactions", report["nodejs_routes"])
        self.assertEqual(
            ["/api/app-version", "/api/discord/interactions"],
            report["middleware_inventory"]["public_authless_paths"],
        )

    def test_main_can_write_json_output(self) -> None:
        root = self._temp_root()
        output_ref = "runtime/receipts/vercel-hobby/fitness.latest.json"

        exit_code = main(["--root", str(root), "--repo-id", "fitness", "--format", "json", "--output", output_ref])

        self.assertEqual(0, exit_code)
        payload = json.loads((root / output_ref).read_text(encoding="utf-8"))
        self.assertEqual("vercel-hobby-guardrail-fitness", payload["report_id"])

    def test_build_report_fails_closed_when_project_link_missing(self) -> None:
        root = self._temp_root()
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").unlink()

        with self.assertRaises(GuardrailReportError):
            build_report(root=root, repo_id="fitness")

    def test_build_report_uses_fallback_project_link_when_local_link_absent(self) -> None:
        # Hosted CI / dry-run checkouts are never `vercel link`-ed, so
        # .vercel/project.json never exists there. The repo-committed
        # fallback lets the guardrail report still be generated in that
        # environment instead of failing closed every time.
        root = self._temp_root()
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").unlink()
        fallback_dir = root / "docs" / "registry" / "vercel-project-links"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        (fallback_dir / "fitness.json").write_text(
            json.dumps(
                {
                    "contract_version": "atlas.vercel-project-link.v1",
                    "repo_id": "fitness",
                    "project_id": "prj_fallback",
                    "team_id": "team_fallback",
                    "project_name": "fawxzzy-fitness",
                }
            ),
            encoding="utf-8",
        )

        report = build_report(root=root, repo_id="fitness")

        self.assertEqual("prj_fallback", report["project_link"]["project_id"])
        self.assertEqual(
            "docs/registry/vercel-project-links/fitness.json",
            report["project_link"]["path"],
        )

    def test_build_report_local_project_link_accepts_snake_case_keys(self) -> None:
        # The committed fallback is strictly schema-governed (snake_case
        # required, closed shape) -- but the LOCAL .vercel/project.json is
        # provider-owned, Vercel's own file, and _parse_project_link_payload
        # still tolerates either camelCase (Vercel's native shape) or
        # snake_case for it.
        root = self._temp_root()
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").write_text(
            json.dumps({"project_id": "prj_snake", "team_id": "team_snake", "project_name": "fawxzzy-fitness"}),
            encoding="utf-8",
        )

        report = build_report(root=root, repo_id="fitness")

        self.assertEqual("prj_snake", report["project_link"]["project_id"])
        self.assertEqual("team_snake", report["project_link"]["team_id"])

    def test_build_report_fails_closed_when_both_project_link_sources_missing(self) -> None:
        root = self._temp_root()
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").unlink()

        with self.assertRaises(GuardrailReportError) as ctx:
            build_report(root=root, repo_id="fitness")
        self.assertIn(".vercel", str(ctx.exception))
        self.assertIn("fitness.json", str(ctx.exception))

    def test_build_report_local_and_fallback_matching_uses_local_and_records_match(self) -> None:
        root = self._temp_root()
        fallback_dir = root / "docs" / "registry" / "vercel-project-links"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        (fallback_dir / "fitness.json").write_text(
            json.dumps(
                {
                    "contract_version": "atlas.vercel-project-link.v1",
                    "repo_id": "fitness",
                    "project_id": "prj_test",
                    "team_id": "team_test",
                    "project_name": "fawxzzy-fitness",
                }
            ),
            encoding="utf-8",
        )

        report = build_report(root=root, repo_id="fitness")

        self.assertEqual("prj_test", report["project_link"]["project_id"])
        self.assertTrue(report["project_link"]["project_link_match"])
        self.assertEqual(
            "repos/fawxzzy-fitness/.vercel/project.json",
            report["project_link"]["observed_project_link_ref"],
        )
        self.assertEqual(
            "docs/registry/vercel-project-links/fitness.json",
            report["project_link"]["expected_project_link_ref"],
        )

    def test_build_report_fails_closed_on_project_link_identity_mismatch(self) -> None:
        # The whole point of the expected/observed split: a local link
        # pointing at a DIFFERENT Vercel project than the committed
        # expectation must never be silently trusted just because it's
        # present on this machine.
        root = self._temp_root()
        fallback_dir = root / "docs" / "registry" / "vercel-project-links"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        (fallback_dir / "fitness.json").write_text(
            json.dumps(
                {
                    "contract_version": "atlas.vercel-project-link.v1",
                    "repo_id": "fitness",
                    "project_id": "prj_DIFFERENT",
                    "team_id": "team_test",
                    "project_name": "fawxzzy-fitness",
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(GuardrailReportError) as ctx:
            build_report(root=root, repo_id="fitness")
        self.assertIn("mismatch", str(ctx.exception))

    def test_build_report_fails_closed_on_malformed_local_project_link(self) -> None:
        root = self._temp_root()
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").write_text(
            json.dumps({"projectId": "prj_test"}),  # missing orgId / projectName
            encoding="utf-8",
        )

        with self.assertRaises(GuardrailReportError):
            build_report(root=root, repo_id="fitness")

    def test_build_report_fails_closed_on_malformed_fallback_project_link(self) -> None:
        root = self._temp_root()
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").unlink()
        fallback_dir = root / "docs" / "registry" / "vercel-project-links"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        (fallback_dir / "fitness.json").write_text(
            json.dumps({"projectId": "prj_test"}),  # missing orgId / projectName
            encoding="utf-8",
        )

        with self.assertRaises(GuardrailReportError):
            build_report(root=root, repo_id="fitness")

    def test_build_report_honors_repo_path_override(self) -> None:
        # --repo-path lets an operator point the report at an exact local
        # checkout (e.g. a specific SHA) instead of whatever stack.yaml's
        # registry currently resolves to.
        root = self._temp_root()
        override_root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(override_root, ignore_errors=True))
        for name in ("src/app/api/health", ".vercel"):
            (override_root / name).mkdir(parents=True, exist_ok=True)
        (override_root / "src" / "app" / "api" / "health" / "route.ts").write_text(
            'export async function GET() { return Response.json({ ok: true }); }\n',
            encoding="utf-8",
        )
        (override_root / ".vercel" / "project.json").write_text(
            json.dumps({"projectId": "prj_override", "orgId": "team_override", "projectName": "fawxzzy-fitness"}),
            encoding="utf-8",
        )
        (override_root / "vercel.json").write_text(json.dumps({"git": {"deploymentEnabled": False}}), encoding="utf-8")

        report = build_report(root=root, repo_id="fitness", repo_root_override=override_root)

        self.assertEqual("prj_override", report["project_link"]["project_id"])


if __name__ == "__main__":
    unittest.main()
