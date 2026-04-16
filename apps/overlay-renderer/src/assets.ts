import {
  BroadcasterConnectionResponseSchema,
  createMockStatusClient,
  createStatusClient,
  defaultStatusClientFixtures,
  ObsHealthResponseSchema,
  type CurrentSessionResponse,
  type RuntimeHealthResponse,
  type StatusClient,
  CurrentSessionResponseSchema,
  RecentEventsResponseSchema,
  RuntimeHealthResponseSchema,
} from "../../../packages/status-client/src/index.js";
import type { CoreApiRouteRequest, CoreApiRouteResponse } from "../../../services/core-api/src/routes/index.js";

export interface OverlayRendererRequest extends CoreApiRouteRequest {}

export interface OverlayRendererResponse {
  statusCode: number;
  headers: Record<string, string>;
  body: string;
}

export type OverlayRendererMode = "live" | "mock";
export type OverlayRendererScenario = "degraded" | "live" | "offline" | "unavailable";
export type OverlayRendererLayout = "compact" | "full";
export type OverlayShellState = "degraded" | "live" | "offline" | "runtime-unavailable";

export interface OverlayRendererAssetOptions {
  baseUrl?: string;
  coreApiDispatch?: OverlayRendererRouteDispatch;
  fetch?: typeof globalThis.fetch;
  mode?: OverlayRendererMode;
  pollIntervalMs?: number;
  scenario?: OverlayRendererScenario;
  statusClient?: StatusClient;
}

export interface OverlayRendererRouteDispatch {
  (request: CoreApiRouteRequest): Promise<CoreApiRouteResponse>;
}

interface OverlayRendererSnapshot {
  currentSession: CurrentSessionResponse | null;
  errorMessage: string | null;
  layout: OverlayRendererLayout;
  mode: OverlayRendererMode;
  runtimeHealth: RuntimeHealthResponse | null;
  scenario: OverlayRendererScenario;
  shellState: OverlayShellState;
}

interface StatusRouteResult {
  body: unknown;
  statusCode: number;
}

const DEFAULT_POLL_INTERVAL_MS = 4_000;

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function textResponse(statusCode: number, contentType: string, body: string): OverlayRendererResponse {
  return {
    statusCode,
    headers: {
      "cache-control": "no-store",
      "content-type": contentType,
    },
    body,
  };
}

function jsonResponse(statusCode: number, body: unknown): OverlayRendererResponse {
  return textResponse(statusCode, "application/json; charset=utf-8", JSON.stringify(body, null, 2));
}

function normalizePollInterval(value?: number): number {
  if (value === undefined) {
    return DEFAULT_POLL_INTERVAL_MS;
  }

  if (!Number.isInteger(value) || value <= 0) {
    throw new Error("pollIntervalMs must be a positive integer when provided.");
  }

  return value;
}

function resolveMode(url: URL, options: OverlayRendererAssetOptions): OverlayRendererMode {
  const requested = url.searchParams.get("mode");

  if (requested === "live" || requested === "mock") {
    return requested;
  }

  return options.mode ?? "mock";
}

function resolveScenario(url: URL, options: OverlayRendererAssetOptions): OverlayRendererScenario {
  const requested = url.searchParams.get("scenario");

  if (requested === "live" || requested === "offline" || requested === "degraded" || requested === "unavailable") {
    return requested;
  }

  return options.scenario ?? "live";
}

function resolveLayout(url: URL): OverlayRendererLayout {
  if (url.pathname === "/compact") {
    return "compact";
  }

  if (url.pathname === "/full") {
    return "full";
  }

  return url.searchParams.get("layout") === "compact" ? "compact" : "full";
}

function cloneFixtures() {
  return structuredClone(defaultStatusClientFixtures);
}

function createScenarioClient(scenario: OverlayRendererScenario, options: OverlayRendererAssetOptions): StatusClient | null {
  if (scenario === "unavailable") {
    return null;
  }

  const fixtures = cloneFixtures();

  if (scenario === "offline") {
    fixtures.currentSession.session.id = "idle";
    fixtures.currentSession.session.status = "idle";
    fixtures.currentSession.session.title = null;
    fixtures.currentSession.session.categoryId = null;
    fixtures.currentSession.session.categoryName = null;
    fixtures.currentSession.session.startedAt = null;
    fixtures.currentSession.projection.sessionId = null;
    fixtures.currentSession.projection.sessionStatus = "idle";
    fixtures.currentSession.health.canRender = false;
    fixtures.currentSession.health.needsOperatorAttention = false;
    fixtures.currentSession.health.reasons = ["no-live-session"];
    fixtures.currentSession.vote = {
      status: "idle",
      id: null,
      title: null,
      choices: [],
      openedAt: null,
      closesAt: null,
      closedAt: null,
      winningChoiceId: null,
      winningChoiceLabel: null,
      totalVotes: 0,
      updatedAt: null,
    };
    fixtures.currentSession.surfaces["overlay-renderer"] = {
      surface: "overlay-renderer",
      visibility: "available",
      revision: fixtures.currentSession.surfaces["overlay-renderer"]?.revision ?? 1,
      updatedAt: "2026-04-16T15:55:00.000Z",
      sessionId: null,
      summary: "Overlay renderer is available without an active live session.",
    };
    fixtures.runtimeHealth.projection.sessionId = null;
    fixtures.runtimeHealth.projection.sessionStatus = "idle";
  }

  if (scenario === "degraded") {
    fixtures.currentSession.connections.twitch = {
      platform: "twitch",
      status: "disconnected",
      updatedAt: "2026-04-16T15:58:00.000Z",
      lastHeartbeatAt: "2026-04-16T15:54:00.000Z",
      details: {
        transport: "eventsub-websocket",
        sessionId: "ws-session-001",
      },
    };
    fixtures.currentSession.health.canRender = false;
    fixtures.currentSession.health.needsOperatorAttention = true;
    fixtures.currentSession.health.reasons = ["twitch-not-connected"];
    fixtures.currentSession.surfaces["overlay-renderer"] = {
      surface: "overlay-renderer",
      visibility: "available",
      revision: fixtures.currentSession.surfaces["overlay-renderer"]?.revision ?? 1,
      updatedAt: "2026-04-16T15:58:00.000Z",
      sessionId: fixtures.currentSession.session.id,
      summary: "Overlay renderer is readable, but runtime health is degraded.",
    };
    fixtures.runtimeHealth.status = "degraded";
    fixtures.runtimeHealth.reasons = ["twitch-not-connected"];
  }

  return options.statusClient ?? createMockStatusClient({ fixtures });
}

async function dispatchJson<T>(
  dispatch: OverlayRendererRouteDispatch,
  url: string,
  schema: { parse(value: unknown): T },
): Promise<T> {
  const response = await dispatch({
    method: "GET",
    url,
  });

  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw new Error(`status route failed: ${response.statusCode}`);
  }

  return schema.parse(response.body);
}

function createDispatchStatusClient(dispatch: OverlayRendererRouteDispatch): StatusClient {
  return {
    async getBroadcasterConnection() {
      return dispatchJson(dispatch, "/status/broadcaster-connection", BroadcasterConnectionResponseSchema);
    },

    async getCurrentSession() {
      return dispatchJson(dispatch, "/status/current-session", CurrentSessionResponseSchema);
    },

    async getObsHealth() {
      return dispatchJson(dispatch, "/status/obs-health", ObsHealthResponseSchema);
    },

    async listRecentEvents(limit?: number) {
      const requestPath = limit === undefined ? "/status/recent-events" : `/status/recent-events?limit=${limit}`;
      return dispatchJson(dispatch, requestPath, RecentEventsResponseSchema);
    },

    async getRuntimeHealth() {
      return dispatchJson(dispatch, "/status/runtime-health", RuntimeHealthResponseSchema);
    },
  };
}

function resolveStatusClient(
  mode: OverlayRendererMode,
  scenario: OverlayRendererScenario,
  options: OverlayRendererAssetOptions,
): StatusClient | null {
  if (options.statusClient) {
    return options.statusClient;
  }

  if (mode === "mock") {
    return createScenarioClient(scenario, options);
  }

  if (options.coreApiDispatch) {
    return createDispatchStatusClient(options.coreApiDispatch);
  }

  if (!options.baseUrl || options.baseUrl.trim().length === 0) {
    return null;
  }

  return createStatusClient({
    baseUrl: options.baseUrl,
    ...(options.fetch ? { fetch: options.fetch } : {}),
  });
}

function deriveShellState(snapshot: {
  currentSession: CurrentSessionResponse | null;
  errorMessage: string | null;
  runtimeHealth: RuntimeHealthResponse | null;
}): OverlayShellState {
  if (snapshot.errorMessage) {
    return "runtime-unavailable";
  }

  if (
    snapshot.runtimeHealth?.status === "degraded" ||
    snapshot.currentSession?.health.needsOperatorAttention === true
  ) {
    return "degraded";
  }

  if (snapshot.currentSession?.session.status === "live") {
    return "live";
  }

  return "offline";
}

async function readSnapshot(
  layout: OverlayRendererLayout,
  mode: OverlayRendererMode,
  scenario: OverlayRendererScenario,
  options: OverlayRendererAssetOptions,
): Promise<OverlayRendererSnapshot> {
  const client = resolveStatusClient(mode, scenario, options);

  if (!client) {
    return {
      currentSession: null,
      errorMessage: "Live mode requires FAWXZZY_STREAM_OVERLAY_RENDERER_STATUS_BASE_URL or a local core API dispatch.",
      layout,
      mode,
      runtimeHealth: null,
      scenario,
      shellState: "runtime-unavailable",
    };
  }

  try {
    const [currentSession, runtimeHealth] = await Promise.all([client.getCurrentSession(), client.getRuntimeHealth()]);

    return {
      currentSession,
      errorMessage: null,
      layout,
      mode,
      runtimeHealth,
      scenario,
      shellState: deriveShellState({
        currentSession,
        errorMessage: null,
        runtimeHealth,
      }),
    };
  } catch (error) {
    return {
      currentSession: null,
      errorMessage: error instanceof Error ? error.message : "Failed to read the shared status contract.",
      layout,
      mode,
      runtimeHealth: null,
      scenario,
      shellState: "runtime-unavailable",
    };
  }
}

async function dispatchStatusRoute(
  path: string,
  mode: OverlayRendererMode,
  scenario: OverlayRendererScenario,
  options: OverlayRendererAssetOptions,
  url: URL,
): Promise<StatusRouteResult> {
  const client = resolveStatusClient(mode, scenario, options);

  if (!client) {
    return {
      statusCode: 503,
      body: {
        error: "Live mode requires FAWXZZY_STREAM_OVERLAY_RENDERER_STATUS_BASE_URL or a local core API dispatch.",
      },
    };
  }

  try {
    switch (path) {
      case "/status/broadcaster-connection":
        return {
          statusCode: 200,
          body: await client.getBroadcasterConnection(),
        };
      case "/status/current-session":
        return {
          statusCode: 200,
          body: await client.getCurrentSession(),
        };
      case "/status/obs-health":
        return {
          statusCode: 200,
          body: await client.getObsHealth(),
        };
      case "/status/recent-events": {
        const limitText = url.searchParams.get("limit");

        if (limitText !== null) {
          const limit = Number.parseInt(limitText, 10);

          if (!Number.isFinite(limit) || limit <= 0) {
            return {
              statusCode: 400,
              body: {
                error: "limit must be a positive integer",
              },
            };
          }

          return {
            statusCode: 200,
            body: await client.listRecentEvents(limit),
          };
        }

        return {
          statusCode: 200,
          body: await client.listRecentEvents(),
        };
      }
      case "/status/runtime-health":
        return {
          statusCode: 200,
          body: await client.getRuntimeHealth(),
        };
      default:
        return {
          statusCode: 404,
          body: {
            error: "not-found",
          },
        };
    }
  } catch (error) {
    return {
      statusCode: 503,
      body: {
        error: error instanceof Error ? error.message : "Failed to read the shared status contract.",
      },
    };
  }
}

function renderOverlayRendererCss(): string {
  return `:root {
  color-scheme: dark;
  font-family: "IBM Plex Sans", "Aptos", "Segoe UI", sans-serif;
  --bg-panel: rgba(9, 16, 22, 0.78);
  --bg-panel-strong: rgba(9, 16, 22, 0.92);
  --border-muted: rgba(255, 255, 255, 0.14);
  --text-main: #f8f2e7;
  --text-muted: rgba(248, 242, 231, 0.72);
  --accent-amber: #ffd166;
  --accent-teal: #74d8cc;
  --accent-warn: #ff8c69;
  --accent-cool: #8fb8ff;
  --shadow-soft: 0 20px 40px rgba(0, 0, 0, 0.28);
}

* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  min-height: 100%;
  background: transparent;
  color: var(--text-main);
}

body {
  padding: 24px;
}

body[data-layout="compact"] {
  padding: 18px;
}

.overlay-shell {
  width: min(960px, 100%);
  display: grid;
  gap: 16px;
}

body[data-layout="compact"] .overlay-shell {
  width: min(380px, 100%);
  gap: 12px;
}

.state-ribbon,
.session-frame,
.module-card,
.meta-strip {
  background: var(--bg-panel);
  border: 1px solid var(--border-muted);
  border-radius: 22px;
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(16px);
}

.state-ribbon {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  align-items: center;
}

.state-ribbon[data-state="live"] {
  border-color: rgba(116, 216, 204, 0.55);
}

.state-ribbon[data-state="offline"] {
  border-color: rgba(143, 184, 255, 0.35);
}

.state-ribbon[data-state="degraded"] {
  border-color: rgba(255, 140, 105, 0.55);
}

.state-ribbon[data-state="runtime-unavailable"] {
  border-color: rgba(255, 140, 105, 0.7);
}

.state-copy {
  display: grid;
  gap: 4px;
}

.eyebrow {
  margin: 0;
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.state-title {
  margin: 0;
  font-size: 1.45rem;
  line-height: 1;
}

body[data-layout="compact"] .state-title {
  font-size: 1.2rem;
}

.state-note {
  margin: 0;
  font-size: 0.92rem;
  color: var(--text-muted);
}

.session-frame {
  padding: 18px 20px;
  display: grid;
  gap: 14px;
  background:
    radial-gradient(circle at top right, rgba(116, 216, 204, 0.16), transparent 34%),
    linear-gradient(135deg, rgba(255, 209, 102, 0.12), transparent 60%),
    var(--bg-panel-strong);
}

.session-title-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.session-title {
  margin: 0;
  font-size: clamp(1.4rem, 3.8vw, 2.35rem);
  line-height: 1.05;
}

.status-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--border-muted);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: rgba(255, 255, 255, 0.06);
}

.status-chip[data-tone="live"] {
  color: #0d1b16;
  background: var(--accent-teal);
}

.status-chip[data-tone="warn"] {
  color: #2c0d05;
  background: var(--accent-warn);
}

.status-chip[data-tone="cool"] {
  color: #091622;
  background: var(--accent-cool);
}

.session-meta-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

body[data-layout="compact"] .session-meta-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.metric {
  display: grid;
  gap: 4px;
}

.metric-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--text-muted);
}

.metric-value {
  font-size: 1rem;
  font-weight: 600;
}

.module-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
}

body[data-layout="compact"] .module-grid {
  grid-template-columns: 1fr;
  gap: 12px;
}

.module-column {
  display: grid;
  gap: 16px;
}

body[data-layout="compact"] .module-column {
  gap: 12px;
}

.module-card {
  padding: 16px;
  display: grid;
  gap: 12px;
}

.module-card h2 {
  margin: 0;
  font-size: 1.02rem;
}

.module-subtitle {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.stack-list,
.split-list {
  display: grid;
  gap: 10px;
}

.stack-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

body[data-layout="compact"] .stack-list {
  grid-template-columns: 1fr;
}

.path-list,
.breakdown-list {
  display: grid;
  gap: 8px;
}

.path-item,
.breakdown-item {
  display: grid;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.path-label,
.breakdown-label {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: baseline;
  font-weight: 600;
}

.path-summary,
.breakdown-note,
.empty-note {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.choice-bar {
  position: relative;
  overflow: hidden;
}

.choice-fill {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(255, 209, 102, 0.28), rgba(116, 216, 204, 0.16));
  border-radius: inherit;
}

.choice-content {
  position: relative;
  display: grid;
  gap: 4px;
}

.binary-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.binary-chip {
  padding: 7px 10px;
  border-radius: 999px;
  font-size: 0.82rem;
  border: 1px solid var(--border-muted);
  background: rgba(255, 255, 255, 0.04);
}

.binary-chip[data-state="yes"] {
  border-color: rgba(116, 216, 204, 0.5);
  color: var(--accent-teal);
}

.binary-chip[data-state="no"] {
  border-color: rgba(255, 140, 105, 0.4);
  color: var(--accent-warn);
}

.meta-strip {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  font-size: 0.8rem;
  color: var(--text-muted);
}

body[data-layout="compact"] .meta-strip {
  display: grid;
  gap: 6px;
}

.meta-strong {
  color: var(--text-main);
}

@media (max-width: 720px) {
  body {
    padding: 16px;
  }

  .overlay-shell {
    width: 100%;
  }

  .session-meta-grid,
  .module-grid,
  .stack-list {
    grid-template-columns: 1fr;
  }
}`;
}

function renderOverlayRendererScript(): string {
  return "";
}

function renderPage(snapshot: OverlayRendererSnapshot, options: OverlayRendererAssetOptions): string {
  const pollIntervalMs = normalizePollInterval(options.pollIntervalMs);
  const bootstrap = {
    layout: snapshot.layout,
    mode: snapshot.mode,
    pollIntervalMs,
    scenario: snapshot.scenario,
    snapshot,
  };

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Overlay Renderer v0</title>
    <link rel="stylesheet" href="/overlay-renderer.css" />
  </head>
  <body data-layout="${escapeHtml(snapshot.layout)}">
    <main id="overlay-shell" class="overlay-shell" aria-live="polite">
      <section id="state-ribbon" class="state-ribbon" data-state="${escapeHtml(snapshot.shellState)}"></section>
      <section id="session-frame" class="session-frame"></section>
      <section class="module-grid">
        <div id="left-column" class="module-column"></div>
        <div id="right-column" class="module-column"></div>
      </section>
      <footer id="meta-strip" class="meta-strip"></footer>
    </main>
    <script id="overlay-bootstrap" type="application/json">${escapeHtml(JSON.stringify(bootstrap))}</script>
    <script src="/overlay-renderer.js" defer></script>
  </body>
</html>`;
}

async function renderRoute(url: URL, options: OverlayRendererAssetOptions): Promise<OverlayRendererResponse> {
  const layout = resolveLayout(url);
  const mode = resolveMode(url, options);
  const scenario = resolveScenario(url, options);
  const snapshot = await readSnapshot(layout, mode, scenario, options);
  return textResponse(200, "text/html; charset=utf-8", renderPage(snapshot, options));
}

export async function dispatchOverlayRendererRequest(
  request: OverlayRendererRequest,
  options: OverlayRendererAssetOptions = {},
): Promise<OverlayRendererResponse> {
  const url = new URL(request.url, "http://overlay-renderer.local");

  if (request.method !== "GET") {
    return textResponse(405, "text/plain; charset=utf-8", "method-not-allowed");
  }

  switch (url.pathname) {
    case "/":
    case "/index.html":
    case "/compact":
    case "/full":
      return renderRoute(url, options);
    case "/overlay-renderer.css":
      return textResponse(200, "text/css; charset=utf-8", renderOverlayRendererCss());
    case "/overlay-renderer.js":
      return textResponse(200, "text/javascript; charset=utf-8", renderOverlayRendererScript());
    case "/favicon.ico":
      return {
        statusCode: 204,
        headers: {
          "cache-control": "no-store",
        },
        body: "",
      };
    case "/status/broadcaster-connection":
    case "/status/current-session":
    case "/status/obs-health":
    case "/status/recent-events":
    case "/status/runtime-health": {
      const mode = resolveMode(url, options);
      const scenario = resolveScenario(url, options);
      const result = await dispatchStatusRoute(url.pathname, mode, scenario, options, url);
      return jsonResponse(result.statusCode, result.body);
    }
    default:
      return textResponse(404, "text/plain; charset=utf-8", "not-found");
  }
}
