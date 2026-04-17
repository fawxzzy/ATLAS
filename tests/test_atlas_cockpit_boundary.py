from __future__ import annotations

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from ops.atlas import cockpit, serve_awareness


SAMPLE_PAYLOAD = {
    "generated_at": "2026-04-17T00:00:00Z",
    "overview": {
        "active_conversation_count": 1,
        "active_initiative_count": 1,
        "attention_item_count": 0,
        "review_queue_count": 0,
        "pending_proposal_count": 1,
        "lock_frozen": False,
        "dirty_repo_count": 2,
        "verta_visible_untrusted": True,
    },
    "conversation_state": {
        "active_session": {
            "task_id": "cockpit-boundary",
            "session_id": "session-1",
            "session_state": "active",
            "resume_status": "pending",
            "automation_level": "observe",
            "worker_id": "worker-1",
            "assignment_id": "assignment-1",
            "initiative_ref": "initiative:initiative-1",
            "updated_at": "2026-04-17T00:00:00Z",
        },
        "conversations": {
            "recent_items": [
                {
                    "conversation_id": "conversation-1",
                    "status": "active",
                    "mode": "observe",
                    "turn_count": 3,
                    "last_turn_at": "2026-04-17T00:00:00Z",
                    "active_initiative_refs": ["initiative:initiative-1"],
                    "active_session_refs": ["session-1"],
                }
            ]
        },
    },
    "active_initiatives": {
        "items": [
            {
                "title": "Boundary patch",
                "id": "initiative-1",
                "status": "active",
                "blessing_state": "pending_manual_review",
                "branch_ref": "codex/cockpit-boundary",
                "summary": "Close the host/auth gap without changing the source of truth.",
                "next_step": "review",
                "follow_up": "merge auth patch",
                "waiting_on": ["ops"],
                "repo_refs": ["repo:stack"],
                "proposal_ref": "proposal:initiative-1",
            }
        ]
    },
    "attention_queue": {
        "items": [
            {
                "summary": "Cockpit remote bind needs auth",
                "kind": "boundary",
                "severity": "high",
                "source_ref": "review:boundary",
            }
        ]
    },
    "review_queue": {
        "items": [
            {
                "title": "Blessing review",
                "id": "review-1",
                "blessing_state": "pending_manual_review",
                "next_step": "approve",
                "follow_up": "after auth patch",
                "waiting_on": ["ops"],
                "repo_refs": ["repo:stack"],
            }
        ]
    },
    "latest_governed_proposal": {
        "title": "Cockpit auth boundary",
        "session_id": "session-proposed-1",
        "proposal_ref": "proposal:initiative-1",
        "session_state": "pending",
        "scenario": "boundary-fix",
        "blessing_state": "pending_manual_review",
        "initiative_id": "initiative-1",
        "initiative_title": "Boundary patch",
        "updated_at": "2026-04-17T00:00:00Z",
        "next_step": "review",
        "follow_up": "merge auth patch",
        "repo_refs": ["repo:stack"],
    },
    "proposal_only_state": {
        "items": [
            {
                "summary": "Proposal-only turn remains visible",
                "turn_id": "turn-1",
                "severity": "medium",
                "intent": "proposal",
                "conversation_id": "conversation-1",
                "source_ref": "turn:1",
            }
        ]
    },
    "featured_paths": [
        {
            "title": "Operator path",
            "initiative_id": "initiative-1",
            "branch_ref": "codex/cockpit-boundary",
            "blessing_state": "pending_manual_review",
            "next_step": "review",
            "initiative_ref": "initiative:initiative-1",
            "attention": {"summary": "Cockpit remote bind needs auth"},
            "proposal_session": {
                "session_id": "session-proposed-1",
                "proposal_ref": "proposal:initiative-1",
            },
            "waiting_on": ["ops"],
            "repo_refs": ["repo:stack"],
        }
    ],
    "repo_inventory": {
        "item_count": 1,
        "dirty_item_count": 0,
        "release_eligible_count": 1,
        "excluded_surface_count": 1,
        "items": [
            {
                "logical_id": "stack",
                "branch": "codex/cockpit-boundary",
                "dirty": True,
                "trust_class": "trusted",
                "local_path": "ops",
                "release_eligible": False,
                "related_initiative_refs": ["initiative:initiative-1"],
            }
        ],
    },
    "lock_worktree_hygiene": {
        "status": "restricted",
        "dirty_repo_count": 2,
        "drifted_component_count": 1,
        "drifted_excluded_surface_count": 0,
        "lock_frozen": False,
        "stack_root": {
            "dirty_effective": True,
            "self_refresh_only": False,
            "modified_paths": ["ops/atlas/cockpit.py"],
        },
        "stack_lock_ref": "stack.lock.yaml",
        "stack_lock_digest": "digest-lock",
        "generated_lock_digest": "digest-generated",
        "drifted_component_ids": ["atlas"],
        "drifted_excluded_surface_ids": [],
        "metadata_drift_fields": ["trust_posture"],
        "dirty_repos": [
            {
                "logical_id": "stack",
                "dirty": True,
                "ref": "repo:stack",
                "path": "ops",
            }
        ],
    },
    "trust_posture": {
        "status": "restricted",
        "item_count": 1,
        "untrusted_item_count": 1,
        "metadata_only_item_count": 1,
        "items": [
            {
                "archive_id": "personal--verta-core",
                "trust_class": "untrusted",
                "read_mode": "restricted",
                "promotion_status": "not_promoted",
                "knowledge_ref": "knowledge:verta",
                "indexing_profile": "metadata_only",
                "source_ref": "archive:verta",
            }
        ],
    },
}


class CockpitBoundaryTests(unittest.TestCase):
    def test_awareness_remote_bind_still_rejects_without_auth(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            serve_awareness.main(["--host", "0.0.0.0", "--port", "0"])
        self.assertEqual(exc.exception.code, 2)

    def test_cockpit_remote_bind_rejected_without_server_auth(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            cockpit.main(["--host", "0.0.0.0", "--port", "0"])
        self.assertEqual(exc.exception.code, 2)

    def test_cockpit_remote_bind_allowed_with_server_auth(self) -> None:
        with patch("ops.atlas.cockpit.CockpitServer") as server_cls:
            server = server_cls.return_value
            server.serve_forever.side_effect = KeyboardInterrupt
            result = cockpit.main(
                [
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "0",
                    "--server-auth-token",
                    "secret-token",
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(server.server_auth_tokens, ["secret-token"])

    def test_cockpit_denies_unauthorized_requests_on_html_and_json_routes(self) -> None:
        server = cockpit.CockpitServer(("127.0.0.1", 0), cockpit.CockpitHandler)
        server.awareness_endpoint = None
        server.auth_token = None
        server.refresh_seconds = 60
        server.server_auth_tokens = ["secret-token"]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            for path in ("/", "/api/cockpit"):
                with self.subTest(path=path):
                    request = Request(f"http://127.0.0.1:{port}{path}")
                    with self.assertRaises(HTTPError) as exc:
                        urlopen(request, timeout=5)
                    self.assertEqual(exc.exception.code, 401)
                    self.assertEqual(exc.exception.headers.get("WWW-Authenticate"), 'Bearer realm="atlas-cockpit"')

            with patch("ops.atlas.cockpit.cockpit_status", return_value=SAMPLE_PAYLOAD):
                html_request = Request(
                    f"http://127.0.0.1:{port}/",
                    headers={"Authorization": "Bearer secret-token"},
                )
                with urlopen(html_request, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    html = response.read().decode("utf-8")
                self.assertIn("ATLAS Cockpit", html)

                json_request = Request(
                    f"http://127.0.0.1:{port}/api/cockpit",
                    headers={"Authorization": "Bearer secret-token"},
                )
                with urlopen(json_request, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    payload = json.loads(response.read().decode("utf-8"))
                self.assertEqual(payload["generated_at"], SAMPLE_PAYLOAD["generated_at"])
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_rendered_html_stays_read_only_and_surfaces_negative_posture(self) -> None:
        html = cockpit._render_html(SAMPLE_PAYLOAD, refresh_seconds=60)

        self.assertIn("value danger'>False</div>", html)
        self.assertIn("value warn'>restricted</div>", html)
        self.assertIn("value ok'>0</div>", html)
        self.assertIn('badge danger">dirty: True</span>', html)

        lowered = html.lower()
        self.assertNotIn("<button", lowered)
        self.assertNotIn("<form", lowered)
        self.assertNotIn("type=\"submit\"", lowered)
        self.assertNotIn("method=\"post\"", lowered)


if __name__ == "__main__":
    unittest.main()
