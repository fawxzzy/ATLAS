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


if __name__ == "__main__":
    unittest.main()
