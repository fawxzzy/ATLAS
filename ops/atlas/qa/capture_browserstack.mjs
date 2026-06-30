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

export function buildCapabilities(providerPayload, config) {
  const defaults = {
    project: "ATLAS QA LLEL",
    build: config.runId,
    name: `${config.scenarioId}:${config.lensId}`,
    "browserstack.username": process.env.BROWSERSTACK_USERNAME,
    "browserstack.accessKey": process.env.BROWSERSTACK_ACCESS_KEY,
    "browserstack.networkLogs": "true",
    "browserstack.debug": "true",
    "browserstack.playwrightVersion": "1.latest",
    "client.playwrightVersion": localPlaywrightVersion(),
  };
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

  await page.goto(config.sourceUrl, { waitUntil: config.waitUntil || "networkidle" });
  if (config.readySelector) {
    await page.waitForSelector(config.readySelector, { state: "visible", timeout: config.readyTimeoutMs || 30000 });
  }
  if (config.settleMs) {
    await page.waitForTimeout(config.settleMs);
  }

  const screenshotPath = path.join(outputDir, "screenshot.png");
  const consolePath = path.join(outputDir, "console.log");
  const networkPath = path.join(outputDir, "network.json");
  await page.screenshot({ path: screenshotPath, fullPage: Boolean(config.fullPage) });
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
