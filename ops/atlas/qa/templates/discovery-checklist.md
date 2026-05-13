# QA Adapter Discovery Checklist

Use this checklist before copying a template into a child repo.

Common fields:
- Repo id from `stack.yaml`
- Root-relative repo path
- Adapter id
- Scenario id
- Optional prepare or dependency-install command for CI evidence lanes
- Repo-local verify command
- Repo-local QA commands that already exist and should be wrapped instead of replaced

Web repo checklist:
- Start command for local or preview-backed verification
- Default URL
- Ready path
- App-ready selector or page stabilization strategy
- Visual smoke routes
- Auth strategy
- Seed strategy
- Required visual lenses
- Required nonvisual artifacts such as trace, console log, network log, and executable report
- Real-device certification strategy if promotion policy requires it

API or package checklist:
- Canonical contract, smoke, or integration command
- Optional local service start command
- Healthcheck endpoint if the service is runnable
- API or package entrypoint path used as the scenario anchor
- Required contract artifacts such as `api_report` or `executable_report`
- Whether any browser-backed docs or preview surface exists
- Required lenses under the current schema, even if the scenario is nonvisual

Docs-only checklist:
- Canonical docs verify command
- Optional docs preview command and root path
- Required executable artifacts
- Any manual notes required for release review
- Whether visual evidence is intentionally out of scope
- Minimal proof lens declaration required by the current schema

Replacement rules:
- Replace all example ids before adoption.
- Keep root-owned refs root-relative.
- Do not copy root pipeline scripts into child repos.
- Do not add screenshots to nonvisual templates unless the repo truly has a visual release surface.
