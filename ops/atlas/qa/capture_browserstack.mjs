import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import childProcess from "node:child_process";

function parseArgs(argv) {
  const args = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (!item.startsWith("--")) {
      continue;
    }
    const key = item.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      args.set(key, true);
      continue;
    }
    args.set(key, value);
    index += 1;
  }
  return args;
}

function sha256(value) {
  return `sha256:${createHash("sha256").update(value).digest("hex")}`;
}

function localPlaywrightVersion() {
  try {
    return childProcess.execSync("npx playwright --version", { stdio: ["ignore", "pipe", "ignore"] }).toString().trim().split(" ")[1] || "1.latest";
  } catch {
    return "1.latest";
  }
}

function isAndroid(config) {
  return String(config.osName || "").toLowerCase().startsWith("android");
}

function isIos(config) {
  return String(config.osName || "").toLowerCase().startsWith("ios");
}

function isLoopbackSourceUrl(config) {
  try {
    const parsed = new URL(String(config.sourceUrl || ""));
    const hostname = parsed.hostname.trim().toLowerCase();
    return hostname === "127.0.0.1" || hostname === "localhost" || hostname === "::1";
  } catch {
    return false;
  }
}

function shouldEnableBrowserStackLocal(config, env = process.env) {
  const explicit = String(env.BROWSERSTACK_LOCAL || "").trim().toLowerCase();
  if (explicit === "1" || explicit === "true" || explicit === "yes") {
    return true;
  }
  if (explicit === "0" || explicit === "false" || explicit === "no") {
    return false;
  }
  return isLoopbackSourceUrl(config);
}

export function resolveBrowserStackNavigationUrl(config, env = process.env) {
  const sourceUrl = String(config.sourceUrl || "");
  if (!shouldEnableBrowserStackLocal(config, env) || isAndroid(config)) {
    return sourceUrl;
  }
  try {
    const parsed = new URL(sourceUrl);
    const hostname = parsed.hostname.trim().toLowerCase();
    if (hostname === "127.0.0.1" || hostname === "localhost" || hostname === "::1") {
      parsed.hostname = "bs-local.com";
      return parsed.toString();
    }
  } catch {
    return sourceUrl;
  }
  return sourceUrl;
}

export function resolveBrowserStackWaitUntil(config) {
  const waitUntil = String(config.waitUntil || "networkidle").trim() || "networkidle";
  if (config.readySelector && waitUntil === "networkidle") {
    return "domcontentloaded";
  }
  return waitUntil;
}

function resolveBrowserStackLocalIdentifier(env = process.env) {
  const identifier = String(env.BROWSERSTACK_LOCAL_IDENTIFIER || "").trim();
  return identifier || null;
}

function resolveReadyState(config) {
  const allowedStates = new Set(["attached", "detached", "hidden", "visible"]);
  const requestedState = String(config.readyState || "visible").toLowerCase();
  if (!allowedStates.has(requestedState)) {
    throw new Error(`Unsupported readyState: ${config.readyState}`);
  }
  return requestedState;
}

export function buildCapabilities(providerPayload, config, env = process.env) {
  const defaults = {
    project: "ATLAS QA LLEL",
    build: config.runId,
    name: `${config.scenarioId}:${config.lensId}`,
    "browserstack.username": env.BROWSERSTACK_USERNAME,
    "browserstack.accessKey": env.BROWSERSTACK_ACCESS_KEY,
    "browserstack.networkLogs": "true",
    "browserstack.debug": "true",
    "browserstack.playwrightVersion": "1.latest",
    "client.playwrightVersion": localPlaywrightVersion(),
  };
  if (shouldEnableBrowserStackLocal(config, env)) {
    defaults["browserstack.local"] = "true";
    const localIdentifier = resolveBrowserStackLocalIdentifier(env);
    if (localIdentifier) {
      defaults["browserstack.localIdentifier"] = localIdentifier;
    }
  }
  const browserName = String(config.browserName || config.browserEngine || "chrome").toLowerCase();
  if (isAndroid(config)) {
    return {
      ...defaults,
      browser: browserName === "chromium" ? "chrome" : browserName,
      deviceName: config.deviceModel,
      osVersion: config.osVersion,
      realMobile: "true",
      "browserstack.console": "info",
    };
  }
  if (isIos(config)) {
    return {
      ...defaults,
      browser: browserName === "webkit" ? "safari" : browserName,
      deviceName: config.deviceModel,
      osVersion: config.osVersion,
      realMobile: "true",
    };
  }
  return {
    ...defaults,
    "browserstack.console": "info",
    os: config.osName || "Windows",
    os_version: config.osVersion || "11",
    browser: browserName === "chromium" ? "chrome" : browserName,
    browser_version: config.browserVersion || "latest",
  };
}

async function safePageDebugValue(getValue, fallback = null) {
  try {
    return await getValue();
  } catch {
    return fallback;
  }
}

export function isBrowserStackSocketFailure(error) {
  const message = error instanceof Error ? error.message : String(error || "");
  return /socket idle from a long time|playwright connection closed|browser has been closed|target closed/i.test(message);
}

async function writeFailureDebug({ page, config, outputDir, error }) {
  const screenshotPath = path.join(outputDir, "failure.png");
  const debugPath = path.join(outputDir, "failure.debug.json");
  await fs.mkdir(outputDir, { recursive: true });

  const skipPageProbes = isBrowserStackSocketFailure(error);
  if (!skipPageProbes) {
    await safePageDebugValue(() => page.screenshot({ path: screenshotPath, fullPage: true, timeout: 10000 }));
  }
  const payload = {
    capturedAt: new Date().toISOString(),
    sourceUrl: String(config.sourceUrl || ""),
    currentUrl: skipPageProbes ? "" : await safePageDebugValue(() => page.url(), ""),
    title: skipPageProbes ? "" : await safePageDebugValue(() => page.title(), ""),
    readySelector: String(config.readySelector || ""),
    readyState: resolveReadyState(config),
    errorMessage: error instanceof Error ? error.message : String(error),
    documentReadyState: skipPageProbes ? null : await safePageDebugValue(() => page.evaluate(() => document.readyState), null),
    htmlDataset: skipPageProbes ? null : await safePageDebugValue(() => page.evaluate(() => ({ ...document.documentElement.dataset })), null),
    bodyDataset: skipPageProbes ? null : await safePageDebugValue(() => page.evaluate(() => document.body ? ({ ...document.body.dataset }) : null), null),
    bodyTextPreview: skipPageProbes ? "" : await safePageDebugValue(
      () => page.evaluate(() => (document.body?.innerText || "").slice(0, 500)),
      "",
    ),
    pageProbesSkipped: skipPageProbes,
  };
  await fs.writeFile(debugPath, JSON.stringify(payload, null, 2) + "\n", "utf8");
  return {
    debugPath,
    screenshotPath,
    currentUrl: payload.currentUrl,
    title: payload.title,
  };
}

async function captureScreenshotWithFallbacks({ page, config, screenshotPath, outputDir }) {
  const timeout = Number.isFinite(Number(config.screenshotTimeoutMs)) ? Number(config.screenshotTimeoutMs) : 20000;
  const attempts = [
    async () => {
      await page.screenshot({ path: screenshotPath, fullPage: Boolean(config.fullPage), timeout });
      return "page";
    },
    async () => {
      const body = page.locator("body");
      await body.screenshot({ path: screenshotPath, timeout });
      return "body";
    },
    async () => {
      const html = page.locator("html");
      await html.screenshot({ path: screenshotPath, timeout });
      return "html";
    },
  ];

  let lastError = null;
  for (const attempt of attempts) {
    try {
      return await attempt();
    } catch (error) {
      lastError = error;
      if (isBrowserStackSocketFailure(error)) {
        break;
      }
    }
  }

  const debug = await writeFailureDebug({ page, config, outputDir, error: lastError });
  const detail = [
    `Provider screenshot failed for lens ${config.lensId}.`,
    `currentUrl=${debug.currentUrl || String(config.sourceUrl || "")}`,
    debug.title ? `title=${debug.title}` : null,
    `debug=${debug.debugPath}`,
    `screenshot=${debug.screenshotPath}`,
    lastError instanceof Error ? `reason=${lastError.message}` : null,
  ].filter(Boolean).join(" ");
  throw new Error(detail);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const configPath = args.get("config");
  if (typeof configPath !== "string") {
    throw new Error("Missing required --config argument.");
  }
  const payload = JSON.parse(await fs.readFile(configPath, "utf8"));
  const providerPayload = payload.provider;
  const config = payload.config;
  const repoRoot = path.resolve(config.repoRoot);
  const requireFromRepo = createRequire(path.join(repoRoot, "package.json"));
  const playwright = requireFromRepo("playwright");
  const outputDir = path.resolve(config.outputDir);
  await fs.mkdir(outputDir, { recursive: true });

  if (!process.env.BROWSERSTACK_USERNAME || !process.env.BROWSERSTACK_ACCESS_KEY) {
    throw new Error("BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY are required.");
  }

  const capabilities = buildCapabilities(providerPayload, config);
  const endpoint = `wss://cdp.browserstack.com/playwright?caps=${encodeURIComponent(JSON.stringify(capabilities))}`;
  const androidSession = isAndroid(config);
  const navigationConfig = { ...config, sourceUrl: resolveBrowserStackNavigationUrl(config) };
  const browserType = String(config.browserEngine || "").toLowerCase() === "webkit" ? playwright.webkit : playwright.chromium;
  const browser = androidSession ? null : await browserType.connect({ wsEndpoint: endpoint });
  const device = androidSession ? await playwright._android.connect(endpoint) : null;
  if (device) {
    try {
      await device.shell("am force-stop com.android.chrome");
    } catch {
      // Best effort only.
    }
  }
  const context = androidSession
    ? await device.launchBrowser()
    : await browser.newContext({
      viewport: {
        width: config.viewport.width,
        height: config.viewport.height,
      },
    });
  context.setDefaultTimeout(20000);
  const page = await context.newPage();
  const consoleLines = [];
  const networkEntries = [];

  page.on("console", (message) => {
    consoleLines.push({ type: message.type(), text: message.text() });
  });
  page.on("response", async (response) => {
    networkEntries.push({
      url: response.url(),
      status: response.status(),
      ok: response.ok(),
      requestMethod: response.request().method(),
      resourceType: response.request().resourceType(),
    });
  });

  try {
    await page.goto(navigationConfig.sourceUrl, { waitUntil: resolveBrowserStackWaitUntil(navigationConfig) });
    if (navigationConfig.readySelector) {
      await page.waitForSelector(navigationConfig.readySelector, {
        state: resolveReadyState(navigationConfig),
        timeout: navigationConfig.readyTimeoutMs || 30000,
      });
    }
    if (navigationConfig.settleMs) {
      await page.waitForTimeout(navigationConfig.settleMs);
    }
  } catch (error) {
    const debug = await writeFailureDebug({ page, config: navigationConfig, outputDir, error });
    const detail = [
      `Provider capture failed before ready state for lens ${config.lensId}.`,
      `currentUrl=${debug.currentUrl || String(navigationConfig.sourceUrl || "")}`,
      debug.title ? `title=${debug.title}` : null,
      `debug=${debug.debugPath}`,
      `screenshot=${debug.screenshotPath}`,
    ].filter(Boolean).join(" ");
    throw new Error(detail);
  }

  const screenshotPath = path.join(outputDir, "screenshot.png");
  const consolePath = path.join(outputDir, "console.log");
  const networkPath = path.join(outputDir, "network.json");
  const screenshotStrategy = await captureScreenshotWithFallbacks({ page, config: navigationConfig, screenshotPath, outputDir });
  await fs.writeFile(consolePath, consoleLines.map((item) => `[${item.type}] ${item.text}`).join("\n"), "utf8");
  await fs.writeFile(networkPath, JSON.stringify(networkEntries, null, 2) + "\n", "utf8");

  try {
    await page.evaluate(
      (_) => {},
      `browserstack_executor: ${JSON.stringify({ action: "setSessionStatus", arguments: { status: "passed", reason: "ATLAS QA provider capture completed" } })}`,
    );
  } catch {
    // Best effort only.
  }

  const metadata = {
    contract_version: "atlas.qa.capture_receipt.v1",
    run_id: config.runId,
    scenario_id: config.scenarioId,
    adapter_id: config.adapterId,
    repo_id: config.repoId,
    git_sha: config.gitSha,
    lens_id: config.lensId,
    lens_profile_id: config.lensProfileId,
    captured_at: new Date().toISOString(),
    source_url: page.url(),
    capture_backend: "browserstack-playwright",
    capture_method: "provider_automation",
    provider_id: providerPayload.provider_id,
    provider_run_id: `${config.runId}:${config.lensId}`,
    device_model: String(config.deviceModel || ""),
    os_name: String(config.osName || ""),
    os_version: String(config.osVersion || ""),
    browser_name: String(config.browserName || config.browserEngine || ""),
    browser_version: String(config.browserVersion || ""),
    viewport: config.viewport,
    outputs: {
      screenshot: screenshotPath,
      console_log: consolePath,
      network_log: networkPath,
    },
    screenshot_strategy: screenshotStrategy,
  };
  const metadataPath = path.join(outputDir, "capture.metadata.json");
  const metadataBody = JSON.stringify(metadata, null, 2) + "\n";
  await fs.writeFile(metadataPath, metadataBody, "utf8");

  await context.close();
  if (device) {
    await device.close();
  } else if (browser) {
    await browser.close();
  }

  process.stdout.write(
    JSON.stringify({
      provider_id: providerPayload.provider_id,
      provider_run_id: metadata.provider_run_id,
      metadata_path: metadataPath,
      metadata_sha256: sha256(Buffer.from(metadataBody, "utf8")),
      outputs: metadata.outputs,
    }),
  );
}

const isDirectExecution = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (isDirectExecution) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack || error.message : String(error));
    process.exitCode = 1;
  });
}
