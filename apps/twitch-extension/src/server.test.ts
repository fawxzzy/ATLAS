import { createServer } from "node:http";

import { afterEach, describe, expect, it } from "vitest";

import { defaultStatusClientFixtures } from "../../../packages/status-client/src/index.js";
import { dispatchTwitchExtensionRequest } from "./server.js";

interface StubServerHandle {
  close(): Promise<void>;
  url: string;
}

async function startStatusStubServer(): Promise<StubServerHandle> {
  const server = createServer((request, response) => {
    const url = new URL(request.url ?? "/", "http://stub.local");
    const bodyByPath: Record<string, unknown> = {
      "/status/broadcaster-connection": defaultStatusClientFixtures.broadcasterConnection,
      "/status/current-session": defaultStatusClientFixtures.currentSession,
      "/status/runtime-health": defaultStatusClientFixtures.runtimeHealth,
    };

    const body = bodyByPath[url.pathname];

    if (!body) {
      response.writeHead(404, {
        "cache-control": "no-store",
        "content-type": "text/plain; charset=utf-8",
      });
      response.end("not-found");
      return;
    }

    response.writeHead(200, {
      "cache-control": "no-store",
      "content-type": "application/json; charset=utf-8",
    });
    response.end(JSON.stringify(body));
  });

  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      server.off("error", reject);
      resolve();
    });
  });

  const address = server.address();

  if (!address || typeof address === "string") {
    throw new Error("Stub status server failed to bind.");
  }

  return {
    url: `http://127.0.0.1:${address.port}`,
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

function buildRequestUrl(path: string, params: Record<string, string> = {}): string {
  const searchParams = new URLSearchParams(params);
  const query = searchParams.toString();

  return query.length > 0 ? `${path}?${query}` : path;
}

describe("dispatchTwitchExtensionRequest", () => {
  let stubServer: StubServerHandle | undefined;

  afterEach(async () => {
    await stubServer?.close();
    stubServer = undefined;
  });

  it("renders the config shell in mock mode", async () => {
    const response = await dispatchTwitchExtensionRequest({
      method: "GET",
      url: buildRequestUrl("/config", {
        mode: "mock",
      }),
    });

    expect(response.statusCode).toBe(200);
    expect(response.headers["content-type"]).toContain("text/html");
    expect(response.body).toContain("Config");
    expect(response.body).toContain("Broadcaster setup is readable.");
    expect(response.body).toContain("auth");
    expect(response.body).toContain("active");
  });

  it("renders the panel offline shell in mock mode", async () => {
    const response = await dispatchTwitchExtensionRequest({
      method: "GET",
      url: buildRequestUrl("/panel", {
        mode: "mock",
        scenario: "offline",
      }),
    });

    expect(response.statusCode).toBe(200);
    expect(response.body).toContain("Panel");
    expect(response.body).toContain("offline");
    expect(response.body).toContain("No live session is active");
    expect(response.body).toContain("Panel shell shows the offline runtime state.");
  });

  it("renders the overlay shell with the current-session summary", async () => {
    const response = await dispatchTwitchExtensionRequest({
      method: "GET",
      url: buildRequestUrl("/overlay", {
        mode: "mock",
      }),
    });

    expect(response.statusCode).toBe(200);
    expect(response.body).toContain("Overlay");
    expect(response.body).toContain("Current-session summary");
    expect(response.body).toContain("Wednesday control room smoke (live)");
    expect(response.body).toContain("Overlay summary is ready.");
  });

  it("renders the dashboard from live status endpoints", async () => {
    stubServer = await startStatusStubServer();

    const response = await dispatchTwitchExtensionRequest({
      method: "GET",
      url: buildRequestUrl("/dashboard", {
        mode: "live",
        statusBaseUrl: stubServer.url,
      }),
    });

    expect(response.statusCode).toBe(200);
    expect(response.body).toContain("Live dashboard");
    expect(response.body).toContain("Current runtime health is visible.");
    expect(response.body).toContain("healthy");
    expect(response.body).toContain("Wednesday control room smoke (live)");
  });

  it("renders the runtime-unavailable state when live mode lacks a status base url", async () => {
    const response = await dispatchTwitchExtensionRequest({
      method: "GET",
      url: buildRequestUrl("/config", {
        mode: "live",
      }),
    });

    expect(response.statusCode).toBe(200);
    expect(response.body).toContain("runtime-unavailable");
    expect(response.body).toContain("Live mode requires FAWXZZY_STREAM_TWITCH_EXTENSION_STATUS_BASE_URL or ?statusBaseUrl=");
  });
});
