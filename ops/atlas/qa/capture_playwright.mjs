import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";

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

function resolveReadyState(config) {
  const allowedStates = new Set(["attached", "detached", "hidden", "visible"]);
  const requestedState = String(config.readyState || "visible").toLowerCase();
  if (!allowedStates.has(requestedState)) {
    throw new Error(`Unsupported readyState: ${config.readyState}`);
  }
  return requestedState;
}

async function waitForVisibleImages(page, timeoutMs = 10000) {
  await page.waitForFunction(
    () => Array.from(document.images)
      .filter((image) => {
        const rect = image.getBoundingClientRect();
        const style = window.getComputedStyle(image);
        return rect.width > 0
          && rect.height > 0
          && style.visibility !== "hidden"
          && style.display !== "none";
      })
      .every((image) => image.complete && image.naturalWidth > 0),
    undefined,
    { timeout: timeoutMs },
  );
}

function captureRetryUrl(sourceUrl) {
  try {
    const parsed = new URL(String(sourceUrl || ""));
    parsed.searchParams.set("__atlas_capture_retry", String(Date.now()));
    parsed.searchParams.delete("app-recovery");
    parsed.searchParams.delete("app-build");
    return parsed.toString();
  } catch {
    return sourceUrl;
  }
}

async function navigateToReadyPage(page, config, sourceUrl) {
  await page.goto(sourceUrl, { waitUntil: config.waitUntil || "networkidle" });
  if (config.readySelector) {
    await page.waitForSelector(config.readySelector, {
      state: resolveReadyState(config),
      timeout: config.readyTimeoutMs || 30000,
    });
  }
  if (config.settleMs) {
    await page.waitForTimeout(config.settleMs);
  }
  await waitForVisibleImages(page, config.imageReadyTimeoutMs || 10000);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const configPath = args.get("config");
  if (typeof configPath !== "string") {
    throw new Error("Missing required --config argument.");
  }
  const config = JSON.parse(await fs.readFile(configPath, "utf8"));
  const repoRoot = path.resolve(config.repoRoot);
  const requireFromRepo = createRequire(path.join(repoRoot, "package.json"));
  let playwright;
  try {
    playwright = requireFromRepo("playwright");
  } catch (error) {
    const requireFromRunner = createRequire(import.meta.url);
    playwright = requireFromRunner("playwright");
  }
  const browserType = playwright[config.browserEngine];
  if (!browserType) {
    throw new Error(`Unsupported browser engine: ${config.browserEngine}`);
  }

  const outputDir = path.resolve(config.outputDir);
  await fs.mkdir(outputDir, { recursive: true });

  const browser = await browserType.launch({ headless: true });
  const context = await browser.newContext({
    viewport: {
      width: config.viewport.width,
      height: config.viewport.height,
    },
    deviceScaleFactor: config.viewport.device_scale_factor,
    isMobile: config.mobile,
    hasTouch: config.hasTouch,
    userAgent: config.userAgent || undefined,
  });
  const page = await context.newPage();
  const consoleLines = [];
  const networkEntries = [];

  page.on("console", (message) => {
    consoleLines.push({
      type: message.type(),
      text: message.text(),
    });
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
  page.on("requestfailed", (request) => {
    networkEntries.push({
      url: request.url(),
      status: 0,
      ok: false,
      requestMethod: request.method(),
      resourceType: request.resourceType(),
      failureText: request.failure()?.errorText || "request_failed",
    });
  });

  if (config.disableAnimations) {
    await page.addInitScript(() => {
      const style = document.createElement("style");
      style.innerHTML = `
        *,
        *::before,
        *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
          scroll-behavior: auto !important;
        }
      `;
      document.documentElement.appendChild(style);
    });
  }

  const wantsTrace = config.artifactKinds.includes("trace");
  if (wantsTrace) {
    await context.tracing.start({ screenshots: true, snapshots: true });
  }

  try {
    await navigateToReadyPage(page, config, config.sourceUrl);
  } catch (error) {
    if (!String(page.url()).includes("app-recovery=chunk-load-error")) {
      throw error;
    }
    await navigateToReadyPage(page, config, captureRetryUrl(config.sourceUrl));
  }

  const outputs = {};
  if (config.artifactKinds.includes("screenshot")) {
    const screenshotPath = path.join(outputDir, "screenshot.png");
    await page.screenshot({ path: screenshotPath, fullPage: Boolean(config.fullPage) });
    outputs.screenshot = screenshotPath;
  }
  if (config.artifactKinds.includes("console_log")) {
    const consolePath = path.join(outputDir, "console.log");
    await fs.writeFile(consolePath, consoleLines.map((item) => `[${item.type}] ${item.text}`).join("\n"), "utf8");
    outputs.console_log = consolePath;
  }
  if (config.artifactKinds.includes("network_log")) {
    const networkPath = path.join(outputDir, "network.json");
    await fs.writeFile(networkPath, JSON.stringify(networkEntries, null, 2) + "\n", "utf8");
    outputs.network_log = networkPath;
  }
  if (wantsTrace) {
    const tracePath = path.join(outputDir, "trace.zip");
    await context.tracing.stop({ path: tracePath });
    outputs.trace = tracePath;
  }

  const capturedAt = new Date().toISOString();
  const metadata = {
    contract_version: "atlas.qa.capture_receipt.v1",
    run_id: config.runId,
    scenario_id: config.scenarioId,
    adapter_id: config.adapterId,
    repo_id: config.repoId,
    git_sha: config.gitSha,
    lens_id: config.lensId,
    lens_profile_id: config.lensProfileId,
    viewport: config.viewport,
    browser_engine: config.browserEngine,
    captured_at: capturedAt,
    source_url: page.url(),
    capture_backend: "playwright",
    capture_method: "browser_emulation",
    outputs,
  };
  const metadataPath = path.join(outputDir, "capture.metadata.json");
  const metadataBody = JSON.stringify(metadata, null, 2) + "\n";
  await fs.writeFile(metadataPath, metadataBody, "utf8");

  await context.close();
  await browser.close();

  const result = {
    metadata_path: metadataPath,
    metadata_sha256: sha256(Buffer.from(metadataBody, "utf8")),
    outputs,
  };
  process.stdout.write(JSON.stringify(result));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exitCode = 1;
});
