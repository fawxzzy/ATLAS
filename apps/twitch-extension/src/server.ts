import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { pathToFileURL } from "node:url";

import {
  createMockStatusClient,
  createStatusClient,
  defaultStatusClientFixtures,
  type BroadcasterConnectionResponse,
  type CurrentSessionResponse,
  type RuntimeHealthResponse,
  type StatusClient,
  type StatusClientFixtureSet,
} from "../../../packages/status-client/src/index.js";

type TwitchExtensionSurface = "config" | "dashboard" | "index" | "overlay" | "panel";
type TwitchExtensionMode = "live" | "mock";
type TwitchExtensionScenario = "degraded" | "live" | "offline" | "runtime-unavailable";
type TwitchExtensionState = "degraded" | "live" | "offline" | "runtime-unavailable";

export interface TwitchExtensionServerOptions {
  hostname?: string;
  mode?: TwitchExtensionMode;
  port?: number;
  pollIntervalMs?: number;
  scenario?: TwitchExtensionScenario;
  statusBaseUrl?: string;
}

export interface TwitchExtensionServerHandle {
  hostname: string;
  port: number;
  server: Server;
  url: string;
  close(): Promise<void>;
}

interface StatusContext {
  mode: TwitchExtensionMode;
  scenario: TwitchExtensionScenario;
  statusBaseUrl: string | null;
}

interface ShellSnapshot {
  broadcasterConnection: BroadcasterConnectionResponse;
  currentSession: CurrentSessionResponse;
  runtimeHealth: RuntimeHealthResponse;
}

interface LoadSnapshotResult {
  kind: "available" | "unavailable";
  snapshot?: ShellSnapshot;
  errorMessage?: string;
}

interface SurfaceDefinition {
  id: TwitchExtensionSurface;
  path: string;
  title: string;
  eyebrow: string;
  description: string;
  backendSurfaceKey?: keyof CurrentSessionResponse["surfaces"];
}

const DEFAULT_HOSTNAME = "127.0.0.1";
const DEFAULT_PORT = 4311;
const DEFAULT_MODE: TwitchExtensionMode = "mock";
const DEFAULT_SCENARIO: TwitchExtensionScenario = "live";

const SURFACES: readonly SurfaceDefinition[] = [
  {
    id: "index",
    path: "/",
    title: "Twitch Extension",
    eyebrow: "Surface map",
    description: "Read-only shells over the shared runtime status contract.",
  },
  {
    id: "config",
    path: "/config",
    title: "Config",
    eyebrow: "Broadcaster config",
    description: "Auth, websocket, and projection status for broadcaster setup.",
    backendSurfaceKey: "twitch-config",
  },
  {
    id: "dashboard",
    path: "/dashboard",
    title: "Live dashboard",
    eyebrow: "Operator view",
    description: "Runtime health plus current-session truth for live monitoring.",
    backendSurfaceKey: "twitch-live-dashboard",
  },
  {
    id: "panel",
    path: "/panel",
    title: "Panel",
    eyebrow: "Viewer panel",
    description: "Offline, live, degraded, and unavailable states in a compact read-only shell.",
    backendSurfaceKey: "twitch-panel",
  },
  {
    id: "overlay",
    path: "/overlay",
    title: "Overlay",
    eyebrow: "Current-session summary",
    description: "The smallest possible live session summary surface.",
    backendSurfaceKey: "twitch-overlay",
  },
] as const;

function normalizePort(value: number | undefined): number {
  if (value === undefined) {
    return DEFAULT_PORT;
  }

  if (!Number.isInteger(value) || value < 0 || value > 65535) {
    throw new Error("Twitch extension port must be an integer between 0 and 65535.");
  }

  return value;
}

function resolveConfiguredPort(port?: number): number {
  if (port !== undefined) {
    return normalizePort(port);
  }

  const fromEnvironment = process.env.FAWXZZY_STREAM_TWITCH_EXTENSION_PORT;

  if (!fromEnvironment) {
    return DEFAULT_PORT;
  }

  return normalizePort(Number.parseInt(fromEnvironment, 10));
}

function resolveConfiguredMode(mode?: TwitchExtensionMode): TwitchExtensionMode {
  const configured = mode ?? (process.env.FAWXZZY_STREAM_TWITCH_EXTENSION_MODE as TwitchExtensionMode | undefined);

  return configured ?? DEFAULT_MODE;
}

function resolveConfiguredScenario(scenario?: TwitchExtensionScenario): TwitchExtensionScenario {
  const configured = scenario ?? (process.env.FAWXZZY_STREAM_TWITCH_EXTENSION_SCENARIO as TwitchExtensionScenario | undefined);

  return configured ?? DEFAULT_SCENARIO;
}

function resolveConfiguredStatusBaseUrl(statusBaseUrl?: string): string | null {
  if (statusBaseUrl !== undefined) {
    return statusBaseUrl.length > 0 ? statusBaseUrl : null;
  }

  const fromEnvironment = process.env.FAWXZZY_STREAM_TWITCH_EXTENSION_STATUS_BASE_URL;

  return fromEnvironment && fromEnvironment.length > 0 ? fromEnvironment : null;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function text(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  return escapeHtml(String(value));
}

function formatJson(value: unknown): string {
  return escapeHtml(JSON.stringify(value, null, 2));
}

function formatQueryParams(mode: TwitchExtensionMode, scenario: TwitchExtensionScenario, statusBaseUrl: string | null): string {
  const searchParams = new URLSearchParams({
    mode,
    scenario,
  });

  if (statusBaseUrl) {
    searchParams.set("statusBaseUrl", statusBaseUrl);
  }

  const query = searchParams.toString();

  return query.length > 0 ? `?${query}` : "";
}

function surfaceHref(surface: Exclude<TwitchExtensionSurface, "index">, context: StatusContext): string {
  const definition = SURFACES.find((entry) => entry.id === surface);

  return `${definition?.path ?? "/"}${formatQueryParams(context.mode, context.scenario, context.statusBaseUrl)}`;
}

function createUnavailableStatusClient(errorMessage: string): StatusClient {
  const fail = async () => {
    throw new Error(errorMessage);
  };

  return {
    getBroadcasterConnection: fail,
    getCurrentSession: fail,
    getRuntimeHealth: fail,
    listRecentEvents: fail,
  };
}

function cloneFixtures(): StatusClientFixtureSet {
  return structuredClone(defaultStatusClientFixtures);
}

function buildMockFixtures(scenario: TwitchExtensionScenario): StatusClientFixtureSet {
  const fixtures = cloneFixtures();

  if (scenario === "runtime-unavailable") {
    return fixtures;
  }

  if (scenario === "offline") {
    fixtures.currentSession.session = {
      ...fixtures.currentSession.session,
      id: "session-offline",
      status: "idle",
      title: "No live session is active",
      startedAt: null,
      endedAt: null,
    };
    fixtures.currentSession.projection = {
      ...fixtures.currentSession.projection,
      sessionId: null,
      sessionStatus: "idle",
      lastEventAt: null,
    };
    fixtures.currentSession.connections = {
      ...fixtures.currentSession.connections,
      twitch: {
        platform: "twitch",
        status: "connected",
        updatedAt: "2026-04-14T18:11:00.000Z",
        lastHeartbeatAt: "2026-04-14T18:11:00.000Z",
        details: {
          transport: "eventsub-websocket",
          sessionId: "ws-session-001",
        },
      },
    };
    fixtures.currentSession.surfaces = {
      ...fixtures.currentSession.surfaces,
      "twitch-config": {
        surface: "twitch-config",
        visibility: "available",
        revision: 2,
        updatedAt: "2026-04-14T18:12:00.000Z",
        sessionId: null,
        summary: "Config shell can read broadcaster connection state while offline.",
      },
      "twitch-live-dashboard": {
        surface: "twitch-live-dashboard",
        visibility: "available",
        revision: 2,
        updatedAt: "2026-04-14T18:12:00.000Z",
        sessionId: null,
        summary: "Dashboard shell stays readable when the session is offline.",
      },
      "twitch-overlay": {
        surface: "twitch-overlay",
        visibility: "available",
        revision: 2,
        updatedAt: "2026-04-14T18:12:00.000Z",
        sessionId: null,
        summary: "Overlay shell has no live session to summarize.",
      },
      "twitch-panel": {
        surface: "twitch-panel",
        visibility: "available",
        revision: 2,
        updatedAt: "2026-04-14T18:12:00.000Z",
        sessionId: null,
        summary: "Panel shell shows the offline runtime state.",
      },
    };
    fixtures.currentSession.health = {
      canRender: false,
      needsOperatorAttention: false,
      reasons: ["no-live-session"],
    };
    fixtures.runtimeHealth = {
      ...fixtures.runtimeHealth,
      status: "healthy",
      reasons: [],
      observedAt: "2026-04-14T18:12:00.000Z",
    };
    fixtures.broadcasterConnection = {
      ...fixtures.broadcasterConnection,
      websocket: {
        ...fixtures.broadcasterConnection.websocket,
        status: "connected",
        lastKeepaliveAt: "2026-04-14T18:11:00.000Z",
      },
      projection: {
        ...fixtures.broadcasterConnection.projection,
        sessionId: null,
        sessionStatus: "idle",
        lastEventAt: null,
      },
    };

    return fixtures;
  }

  if (scenario === "degraded") {
    fixtures.currentSession.connections = {
      ...fixtures.currentSession.connections,
      twitch: {
        platform: "twitch",
        status: "error",
        updatedAt: "2026-04-14T18:12:00.000Z",
        lastHeartbeatAt: null,
        details: {
          transport: "eventsub-websocket",
          lastError: "Twitch EventSub websocket reconnect is pending.",
        },
      },
    };
    fixtures.currentSession.surfaces = {
      ...fixtures.currentSession.surfaces,
      "twitch-config": {
        surface: "twitch-config",
        visibility: "available",
        revision: 2,
        updatedAt: "2026-04-14T18:12:00.000Z",
        sessionId: "sess-2026-04-14-a",
        summary: "Config shell is readable, but the runtime needs attention.",
      },
      "twitch-live-dashboard": {
        surface: "twitch-live-dashboard",
        visibility: "live",
        revision: 2,
        updatedAt: "2026-04-14T18:12:00.000Z",
        sessionId: "sess-2026-04-14-a",
        summary: "Dashboard shell mirrors a live session with a degraded runtime.",
      },
      "twitch-overlay": {
        surface: "twitch-overlay",
        visibility: "live",
        revision: 2,
        updatedAt: "2026-04-14T18:12:00.000Z",
        sessionId: "sess-2026-04-14-a",
        summary: "Overlay shell still shows the current live session summary.",
      },
      "twitch-panel": {
        surface: "twitch-panel",
        visibility: "live",
        revision: 2,
        updatedAt: "2026-04-14T18:12:00.000Z",
        sessionId: "sess-2026-04-14-a",
        summary: "Panel shell should show live state with attention required.",
      },
    };
    fixtures.currentSession.health = {
      canRender: false,
      needsOperatorAttention: true,
      reasons: ["twitch-not-connected"],
    };
    fixtures.runtimeHealth = {
      ...fixtures.runtimeHealth,
      status: "degraded",
      reasons: ["websocket-disconnected"],
      observedAt: "2026-04-14T18:12:00.000Z",
      websocket: {
        ...fixtures.runtimeHealth.websocket,
        status: "disconnected",
        disconnectedAt: "2026-04-14T18:12:00.000Z",
        lastKeepaliveAt: "2026-04-14T18:11:00.000Z",
      },
      metrics: {
        ...fixtures.runtimeHealth.metrics,
        lastSuccessfulReconcileAt: "2026-04-14T18:11:30.000Z",
      },
    };
    fixtures.broadcasterConnection = {
      ...fixtures.broadcasterConnection,
      websocket: {
        ...fixtures.broadcasterConnection.websocket,
        status: "disconnected",
        disconnectedAt: "2026-04-14T18:12:00.000Z",
        lastKeepaliveAt: "2026-04-14T18:11:00.000Z",
      },
      projection: {
        ...fixtures.broadcasterConnection.projection,
        lastEventAt: "2026-04-14T18:11:30.000Z",
      },
    };

    return fixtures;
  }

  return fixtures;
}

function createStatusClientForContext(context: StatusContext): StatusClient {
  if (context.mode === "live") {
    if (!context.statusBaseUrl) {
      return createUnavailableStatusClient("Live mode requires FAWXZZY_STREAM_TWITCH_EXTENSION_STATUS_BASE_URL or ?statusBaseUrl=");
    }

    return createStatusClient({
      baseUrl: context.statusBaseUrl,
    });
  }

  if (context.scenario === "runtime-unavailable") {
    return createUnavailableStatusClient("Mock runtime is intentionally unavailable.");
  }

  return createMockStatusClient({
    fixtures: buildMockFixtures(context.scenario),
  });
}

function resolveContext(requestUrl: URL, options: TwitchExtensionServerOptions = {}): StatusContext {
  const modeText = requestUrl.searchParams.get("mode");
  const scenarioText = requestUrl.searchParams.get("scenario");
  const baseUrlText = requestUrl.searchParams.get("statusBaseUrl");
  const mode = (modeText ?? resolveConfiguredMode(options.mode)) as TwitchExtensionMode;
  const scenario = (scenarioText ?? resolveConfiguredScenario(options.scenario)) as TwitchExtensionScenario;
  const statusBaseUrl = resolveConfiguredStatusBaseUrl(baseUrlText ?? options.statusBaseUrl);

  if (mode !== "live" && mode !== "mock") {
    throw new Error("mode must be either live or mock.");
  }

  if (scenario !== "live" && scenario !== "offline" && scenario !== "degraded" && scenario !== "runtime-unavailable") {
    throw new Error("scenario must be one of live, offline, degraded, or runtime-unavailable.");
  }

  return {
    mode,
    scenario,
    statusBaseUrl,
  };
}

async function loadSnapshot(statusClient: StatusClient): Promise<LoadSnapshotResult> {
  try {
    const [broadcasterConnection, currentSession, runtimeHealth] = await Promise.all([
      statusClient.getBroadcasterConnection(),
      statusClient.getCurrentSession(),
      statusClient.getRuntimeHealth(),
    ]);

    return {
      kind: "available",
      snapshot: {
        broadcasterConnection,
        currentSession,
        runtimeHealth,
      },
    };
  } catch (error) {
    return {
      kind: "unavailable",
      errorMessage: error instanceof Error ? error.message : "unknown-error",
    };
  }
}

function classifyState(snapshot: ShellSnapshot | undefined): TwitchExtensionState {
  if (!snapshot) {
    return "runtime-unavailable";
  }

  if (snapshot.runtimeHealth.status === "degraded") {
    return "degraded";
  }

  if (snapshot.currentSession.health.needsOperatorAttention || snapshot.currentSession.health.reasons.length > 0) {
    return "degraded";
  }

  if (snapshot.currentSession.session.status === "live" && snapshot.currentSession.health.canRender) {
    return "live";
  }

  return "offline";
}

function classifyStatusTone(state: TwitchExtensionState): string {
  switch (state) {
    case "live":
      return "live";
    case "offline":
      return "offline";
    case "degraded":
      return "degraded";
    case "runtime-unavailable":
      return "unavailable";
  }
}

function describeState(state: TwitchExtensionState): string {
  switch (state) {
    case "live":
      return "The shell is reading a live, renderable session.";
    case "offline":
      return "The shell is readable, but no live session is active.";
    case "degraded":
      return "The shell is readable, but the runtime needs operator attention.";
    case "runtime-unavailable":
      return "The backend status contract could not be read.";
  }
}

function surfaceStatusText(snapshot: ShellSnapshot | undefined, surface: TwitchExtensionSurface): string {
  if (!snapshot) {
    return "runtime-unavailable";
  }

  if (surface === "index") {
    return classifyState(snapshot);
  }

  const definition = SURFACES.find((entry) => entry.id === surface);
  const surfaceKey = definition?.backendSurfaceKey;
  const surfaceView = surfaceKey ? snapshot.currentSession.surfaces[surfaceKey] : null;

  return surfaceView ? surfaceView.visibility : "hidden";
}

function renderMetric(label: string, value: unknown, note?: string): string {
  return `
        <div class="metric-card">
          <span class="metric-label">${escapeHtml(label)}</span>
          <strong class="metric-value">${text(value)}</strong>
          ${note ? `<p class="metric-note">${escapeHtml(note)}</p>` : ""}
        </div>`;
}

function renderStateBanner(state: TwitchExtensionState, title: string, body: string, details: string[]): string {
  return `
      <section class="state-banner state-banner--${classifyStatusTone(state)}">
        <p class="state-eyebrow">${escapeHtml(state.replace("-", " "))}</p>
        <h2>${escapeHtml(title)}</h2>
        <p class="state-copy">${escapeHtml(body)}</p>
        ${details.length > 0 ? `<p class="state-details">${details.map((detail) => escapeHtml(detail)).join(" · ")}</p>` : ""}
      </section>`;
}

function renderJsonBlock(label: string, value: unknown): string {
  return `
      <details class="payload">
        <summary>${escapeHtml(label)}</summary>
        <pre>${formatJson(value)}</pre>
      </details>`;
}

function renderSurfaceLinks(context: StatusContext, active: TwitchExtensionSurface): string {
  return `
      <nav class="surface-links" aria-label="Twitch extension surfaces">
        ${SURFACES.filter((surface) => surface.id !== "index")
          .map((surface) => {
            const activeClass = surface.id === active ? " is-active" : "";
            return `<a class="surface-link${activeClass}" href="${surfaceHref(surface.id, context)}">
              <span class="surface-link__eyebrow">${escapeHtml(surface.eyebrow)}</span>
              <span class="surface-link__title">${escapeHtml(surface.title)}</span>
            </a>`;
          })
          .join("")}
      </nav>`;
}

function renderIndexCards(snapshot: ShellSnapshot | undefined, context: StatusContext): string {
  return SURFACES.filter((surface) => surface.id !== "index")
    .map((surface) => {
      const state = classifyState(snapshot);
      const status = surfaceStatusText(snapshot, surface.id);

      return `
        <a class="surface-card" href="${surfaceHref(surface.id, context)}">
          <span class="surface-card__eyebrow">${escapeHtml(surface.eyebrow)}</span>
          <strong class="surface-card__title">${escapeHtml(surface.title)}</strong>
          <p class="surface-card__description">${escapeHtml(surface.description)}</p>
          <dl class="surface-card__meta">
            <div>
              <dt>state</dt>
              <dd>${escapeHtml(state)}</dd>
            </div>
            <div>
              <dt>surface</dt>
              <dd>${escapeHtml(status)}</dd>
            </div>
          </dl>
        </a>`;
    })
    .join("");
}

function renderSurfaceMetrics(snapshot: ShellSnapshot, surface: TwitchExtensionSurface): string {
  const currentSession = snapshot.currentSession;
  const runtimeHealth = snapshot.runtimeHealth;
  const broadcasterConnection = snapshot.broadcasterConnection;
  const surfaceKey = SURFACES.find((entry) => entry.id === surface)?.backendSurfaceKey;
  const surfaceView = surfaceKey ? currentSession.surfaces[surfaceKey] : null;

  switch (surface) {
    case "config":
      return [
        renderMetric("auth", broadcasterConnection.auth.status, broadcasterConnection.auth.providerAccountId ?? "missing account"),
        renderMetric("websocket", broadcasterConnection.websocket.status, broadcasterConnection.websocket.currentSessionId ?? "no socket session"),
        renderMetric("subscriptions", `${broadcasterConnection.subscriptions.activeCount}/${broadcasterConnection.subscriptions.desiredCount}`, `total ${broadcasterConnection.subscriptions.totalCount}`),
        renderMetric("projection", `rev ${broadcasterConnection.projection.revision}`, `high-water mark ${broadcasterConnection.projection.highWaterMark}`),
      ].join("");
    case "dashboard":
      return [
        renderMetric("runtime", runtimeHealth.status, runtimeHealth.reasons.length > 0 ? runtimeHealth.reasons.join(", ") : "no operator issues"),
        renderMetric("session", currentSession.session.status, currentSession.session.id),
        renderMetric("health", currentSession.health.canRender ? "canRender=true" : "canRender=false", currentSession.health.reasons.length > 0 ? currentSession.health.reasons.join(", ") : "no reasons"),
        renderMetric("surface", surfaceView?.visibility ?? "hidden", surfaceView?.summary ?? "no surface summary"),
      ].join("");
    case "panel":
      return [
        renderMetric("session", currentSession.session.status, currentSession.session.title ?? "untitled"),
        renderMetric("runtime", runtimeHealth.status, runtimeHealth.reasons.length > 0 ? runtimeHealth.reasons.join(", ") : "no operator issues"),
        renderMetric("surface", surfaceView?.visibility ?? "hidden", surfaceView?.summary ?? "no surface summary"),
        renderMetric("last event", currentSession.lastEventAt ?? "none", `projection ${currentSession.projection.revision}`),
      ].join("");
    case "overlay":
      return [
        renderMetric("session", currentSession.session.status, currentSession.session.title ?? "untitled"),
        renderMetric("summary", surfaceView?.summary ?? "no summary", currentSession.session.id),
        renderMetric("broadcaster", currentSession.session.broadcasterId ?? "unknown", currentSession.session.categoryName ?? "uncategorized"),
      ].join("");
    case "index":
      return [
        renderMetric("runtime", runtimeHealth.status, runtimeHealth.reasons.length > 0 ? runtimeHealth.reasons.join(", ") : "no operator issues"),
        renderMetric("session", currentSession.session.status, currentSession.session.id),
        renderMetric("broadcaster", broadcasterConnection.broadcaster.displayName ?? "unknown", broadcasterConnection.broadcaster.login ?? "unknown"),
        renderMetric("surface", surfaceView?.visibility ?? "hidden", surfaceView?.summary ?? "surface map"),
      ].join("");
  }
}

function renderSurfaceContent(
  surface: TwitchExtensionSurface,
  snapshot: ShellSnapshot | undefined,
  context: StatusContext,
  loadResult: LoadSnapshotResult,
): string {
  const definition = SURFACES.find((entry) => entry.id === surface);

  if (!definition) {
    return "";
  }

  if (!snapshot) {
    return `
      <main class="shell shell--${surface}">
        <header class="page-header">
          <div>
            <p class="eyebrow">${escapeHtml(definition.eyebrow)}</p>
            <h1>${escapeHtml(definition.title)}</h1>
            <p class="lede">${escapeHtml(definition.description)}</p>
          </div>
          ${renderSurfaceLinks(context, surface)}
        </header>
        ${renderStateBanner("runtime-unavailable", definition.title, "The backend status contract could not be read.", [loadResult.errorMessage ?? "unknown-error"])}
        ${renderJsonBlock("Runtime error", {
          mode: context.mode,
          scenario: context.scenario,
          statusBaseUrl: context.statusBaseUrl,
          error: loadResult.errorMessage ?? "unknown-error",
        })}
      </main>`;
  }

  const state = classifyState(snapshot);
  const titleBySurface: Record<Exclude<TwitchExtensionSurface, "index">, string> = {
    config: "Broadcaster setup is readable.",
    dashboard: "Current runtime health is visible.",
    panel: "Panel state matches the current session truth.",
    overlay: "Overlay summary is ready.",
  };
  const bodyByState: Record<TwitchExtensionState, string> = {
    degraded: "The backend is readable, but at least one signal requires attention.",
    live: "The backend is healthy enough to render the live shell.",
    offline: "The backend is healthy, but no live session is active.",
    runtime-unavailable: "The backend status contract could not be read.",
  };
  const details: string[] = [];

  if (surface !== "index" && definition.backendSurfaceKey) {
    const surfaceView = snapshot.currentSession.surfaces[definition.backendSurfaceKey];

    if (surfaceView) {
      details.push(`backend surface: ${surfaceView.surface}`);
      details.push(`visibility: ${surfaceView.visibility}`);
      details.push(`revision: ${String(surfaceView.revision)}`);
    }
  }

  details.push(`mode: ${context.mode}`);
  details.push(`scenario: ${context.scenario}`);

  const currentSession = snapshot.currentSession;
  const runtimeHealth = snapshot.runtimeHealth;
  const broadcasterConnection = snapshot.broadcasterConnection;
  const surfaceView = definition.backendSurfaceKey ? currentSession.surfaces[definition.backendSurfaceKey] : null;

  const bannerDetails = [
    ...details,
    ...(state === "degraded" ? runtimeHealth.reasons : []),
    ...(currentSession.health.reasons.length > 0 ? currentSession.health.reasons : []),
  ];

  return `
      <main class="shell shell--${surface}">
        <header class="page-header">
          <div>
            <p class="eyebrow">${escapeHtml(definition.eyebrow)}</p>
            <h1>${escapeHtml(definition.title)}</h1>
            <p class="lede">${escapeHtml(definition.description)}</p>
          </div>
          ${renderSurfaceLinks(context, surface)}
        </header>

        ${renderStateBanner(state, titleBySurface[surface as Exclude<TwitchExtensionSurface, "index">], bodyByState[state], bannerDetails)}

        <section class="surface-grid">
          ${renderSurfaceMetrics(snapshot, surface)}
        </section>

        ${surface === "config" ? renderJsonBlock("Broadcaster connection", broadcasterConnection) : ""}
        ${surface === "dashboard" ? renderJsonBlock("Runtime health", runtimeHealth) : ""}
        ${surface === "dashboard" || surface === "panel" || surface === "overlay" ? renderJsonBlock("Current session", currentSession) : ""}
        ${surfaceView ? renderJsonBlock("Surface record", surfaceView) : ""}
      </main>`;
}

function renderIndexPage(snapshot: ShellSnapshot | undefined, context: StatusContext, loadResult: LoadSnapshotResult): string {
  const state = classifyState(snapshot);
  const definition = SURFACES[0];

  if (!snapshot) {
    return `
      <main class="shell shell--index">
        <header class="page-header">
          <div>
            <p class="eyebrow">${escapeHtml(definition.eyebrow)}</p>
            <h1>${escapeHtml(definition.title)}</h1>
            <p class="lede">${escapeHtml(definition.description)}</p>
          </div>
          ${renderSurfaceLinks(context, "index")}
        </header>
        ${renderStateBanner("runtime-unavailable", "Status contract unavailable", "The extension shell could not load runtime state.", [loadResult.errorMessage ?? "unknown-error"])}
      </main>`;
  }

  const summary = [
    `session: ${snapshot.currentSession.session.status}`,
    `runtime: ${snapshot.runtimeHealth.status}`,
    `auth: ${snapshot.broadcasterConnection.auth.status}`,
  ];

  return `
      <main class="shell shell--index">
        <header class="page-header">
          <div>
            <p class="eyebrow">${escapeHtml(definition.eyebrow)}</p>
            <h1>${escapeHtml(definition.title)}</h1>
            <p class="lede">${escapeHtml(definition.description)}</p>
          </div>
          ${renderSurfaceLinks(context, "index")}
        </header>

        ${renderStateBanner(state, "Shell overview", describeState(state), summary)}

        <section class="surface-grid">
          ${renderIndexCards(snapshot, context)}
        </section>

        <section class="metric-grid">
          ${renderSurfaceMetrics(snapshot, "index")}
        </section>

        ${renderJsonBlock("Current session", snapshot.currentSession)}
        ${renderJsonBlock("Runtime health", snapshot.runtimeHealth)}
        ${renderJsonBlock("Broadcaster connection", snapshot.broadcasterConnection)}
      </main>`;
}

function renderDocument(surface: TwitchExtensionSurface, snapshot: ShellSnapshot | undefined, context: StatusContext, loadResult: LoadSnapshotResult): string {
  const definition = SURFACES.find((entry) => entry.id === surface);
  const title = definition ? `${definition.title} | Fawxzzy Stream` : "Fawxzzy Stream";
  const state = classifyState(snapshot);
  const body = surface === "index" ? renderIndexPage(snapshot, context, loadResult) : renderSurfaceContent(surface, snapshot, context, loadResult);

  return `<!doctype html>
<html lang="en" data-surface="${escapeHtml(surface)}" data-mode="${escapeHtml(context.mode)}" data-scenario="${escapeHtml(context.scenario)}" data-state="${escapeHtml(state)}">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(title)}</title>
    <style>${renderStyles()}</style>
  </head>
  <body>
${body}
  </body>
</html>`;
}

function renderStyles(): string {
  return `:root {
  color-scheme: light;
  --bg: #f5f2ea;
  --bg-accent: #e8eef5;
  --panel: #ffffff;
  --panel-strong: #0f172a;
  --text: #152033;
  --muted: #5f6b7c;
  --line: rgba(21, 32, 51, 0.14);
  --live: #1f7a4f;
  --offline: #5f6b7c;
  --degraded: #a86400;
  --unavailable: #9a2f2f;
  --shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
  font-family: "IBM Plex Sans", "Aptos", "Segoe UI", sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  color: var(--text);
  background:
    radial-gradient(circle at top left, rgba(31, 122, 79, 0.08), transparent 28%),
    radial-gradient(circle at top right, rgba(168, 100, 0, 0.08), transparent 26%),
    linear-gradient(180deg, var(--bg), var(--bg-accent));
}

a {
  color: inherit;
  text-decoration: none;
}

.shell {
  width: min(1120px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 28px 0 40px;
}

.page-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 20px;
  margin-bottom: 22px;
}

.eyebrow {
  margin: 0 0 10px;
  color: var(--muted);
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

h1,
h2,
p {
  margin: 0;
}

h1 {
  font-size: clamp(2rem, 4vw, 3.5rem);
  line-height: 0.95;
  letter-spacing: -0.05em;
}

.lede {
  max-width: 60ch;
  margin-top: 12px;
  color: var(--muted);
  line-height: 1.55;
}

.surface-links {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.surface-link,
.surface-card,
.state-banner,
.metric-card,
.payload {
  border: 1px solid var(--line);
  border-radius: 20px;
  background: color-mix(in srgb, var(--panel) 92%, transparent);
  box-shadow: var(--shadow);
}

.surface-link {
  display: grid;
  gap: 4px;
  padding: 14px 16px;
}

.surface-link.is-active {
  border-color: rgba(31, 122, 79, 0.38);
  box-shadow: 0 18px 40px rgba(31, 122, 79, 0.08);
}

.surface-link__eyebrow,
.surface-card__eyebrow,
.state-eyebrow,
.metric-label,
dt {
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.surface-link__title,
.surface-card__title {
  font-size: 1rem;
  font-weight: 700;
}

.surface-card {
  display: grid;
  gap: 10px;
  padding: 18px;
}

.surface-card__description,
.state-copy,
.state-details,
.metric-note {
  color: var(--muted);
  line-height: 1.5;
}

.surface-card__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.surface-card__meta div,
.metric-card {
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.65);
}

dt {
  margin-bottom: 4px;
}

dd {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
}

.state-banner {
  padding: 18px 20px;
  margin: 20px 0;
  border-left-width: 4px;
}

.state-banner--live {
  border-left-color: var(--live);
}

.state-banner--offline {
  border-left-color: var(--offline);
}

.state-banner--degraded {
  border-left-color: var(--degraded);
}

.state-banner--unavailable {
  border-left-color: var(--unavailable);
}

.state-banner h2 {
  margin-top: 6px;
  font-size: 1.35rem;
  line-height: 1.15;
}

.state-copy {
  margin-top: 8px;
}

.state-details {
  margin-top: 10px;
  font-size: 0.92rem;
}

.surface-grid,
.metric-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.metric-card {
  display: grid;
  gap: 6px;
}

.metric-value {
  font-size: 1.2rem;
  line-height: 1.1;
}

.payload {
  margin-top: 16px;
  padding: 0;
  overflow: hidden;
}

.payload summary {
  cursor: default;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
  font-size: 0.9rem;
  font-weight: 700;
}

.payload pre {
  margin: 0;
  padding: 16px;
  overflow: auto;
  background: var(--panel-strong);
  color: #e5eefb;
  font-family: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
  font-size: 0.84rem;
  line-height: 1.5;
}

@media (max-width: 760px) {
  .shell {
    width: min(100vw - 20px, 100%);
    padding: 18px 0 30px;
  }

  .surface-card__meta {
    grid-template-columns: 1fr;
  }
}`;
}

export async function dispatchTwitchExtensionRequest(
  request: IncomingMessage | { method?: string; url?: string },
  options: TwitchExtensionServerOptions = {},
): Promise<{ statusCode: number; headers: Record<string, string>; body: string }> {
  const url = new URL(request.url ?? "/", "http://twitch-extension.local");

  if ((request.method ?? "GET") !== "GET") {
    return {
      statusCode: 405,
      headers: {
        "cache-control": "no-store",
        "content-type": "text/plain; charset=utf-8",
      },
      body: "method-not-allowed",
    };
  }

  const route = normalizeRoute(url.pathname);

  if (!route) {
    return {
      statusCode: 404,
      headers: {
        "cache-control": "no-store",
        "content-type": "text/plain; charset=utf-8",
      },
      body: "not-found",
    };
  }

  const context = resolveContext(url, options);
  const statusClient = createStatusClientForContext(context);
  const loadResult = await loadSnapshot(statusClient);
  const snapshot = loadResult.kind === "available" ? loadResult.snapshot : undefined;

  return {
    statusCode: 200,
    headers: {
      "cache-control": "no-store",
      "content-type": "text/html; charset=utf-8",
    },
    body: renderDocument(route, snapshot, context, loadResult),
  };
}

function normalizeRoute(pathname: string): TwitchExtensionSurface | null {
  switch (pathname) {
    case "/":
    case "/index.html":
      return "index";
    case "/config":
    case "/config.html":
      return "config";
    case "/dashboard":
    case "/dashboard.html":
      return "dashboard";
    case "/panel":
    case "/panel.html":
      return "panel";
    case "/overlay":
    case "/overlay.html":
      return "overlay";
    default:
      return null;
  }
}

export async function startTwitchExtensionServer(
  options: TwitchExtensionServerOptions = {},
): Promise<TwitchExtensionServerHandle> {
  const hostname = options.hostname ?? DEFAULT_HOSTNAME;
  const port = resolveConfiguredPort(options.port);

  const server = createServer((request, response) => {
    void dispatchTwitchExtensionRequest(request, options)
      .then((result) => {
        response.writeHead(result.statusCode, result.headers);
        response.end(result.body);
      })
      .catch((error: unknown) => {
        response.writeHead(500, {
          "cache-control": "no-store",
          "content-type": "text/plain; charset=utf-8",
        });
        response.end(error instanceof Error ? error.message : "unknown-error");
      });
  });

  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, hostname, () => {
      server.off("error", reject);
      resolve();
    });
  });

  const address = server.address();

  if (!address || typeof address === "string") {
    throw new Error("Twitch extension server failed to bind to an address.");
  }

  const resolvedHostname = hostname.includes(":") ? `[${hostname}]` : hostname;
  const url = `http://${resolvedHostname}:${address.port}`;

  return {
    hostname,
    port: address.port,
    server,
    url,
    close() {
      return new Promise<void>((resolve, reject) => {
        server.close((error) => {
          if (error) {
            reject(error);
            return;
          }

          resolve();
        });
      });
    },
  };
}

async function main(): Promise<void> {
  const extension = await startTwitchExtensionServer();
  console.log(`twitch-extension listening on ${extension.url}`);
}

const invokedPath = process.argv[1] ? pathToFileURL(process.argv[1]).href : undefined;

if (invokedPath && import.meta.url === invokedPath) {
  void main().catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
}
