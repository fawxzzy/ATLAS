#!/usr/bin/env node

import { mkdir, readFile, writeFile, copyFile, stat } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const SCRIPT_DIRECTORY = path.dirname(fileURLToPath(import.meta.url));
const BRANDING_ROOT = path.resolve(SCRIPT_DIRECTORY, "..");
const ATLAS_ROOT = path.resolve(BRANDING_ROOT, "..");
const DEFAULT_MANIFEST_PATH = path.join(BRANDING_ROOT, "manifest.json");

function parseArguments(argv) {
  const options = {
    manifestPath: DEFAULT_MANIFEST_PATH
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--manifest") {
      index += 1;
      const value = argv[index];
      if (!value) {
        throw new Error("Missing value for --manifest.");
      }
      options.manifestPath = path.resolve(process.cwd(), value);
      continue;
    }
    throw new Error(`Unknown argument: ${argument}`);
  }

  return options;
}

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

function resolveAtlasPath(relativePath) {
  return path.resolve(ATLAS_ROOT, relativePath);
}

function ensureString(value, label) {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${label} must be a non-empty string.`);
  }
  return value.trim();
}

function ensureSize(value, label) {
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error(`${label} must be a positive integer.`);
  }
  return value;
}

let sharpPromise;

async function loadSharp() {
  if (!sharpPromise) {
    sharpPromise = (async () => {
      try {
        const module = await import("sharp");
        return module.default;
      } catch {
        const fallbackPath = path.resolve(ATLAS_ROOT, "repos", "fawxzzy-fitness", "node_modules", "sharp", "lib", "index.js");
        try {
          await stat(fallbackPath);
        } catch {
          return null;
        }
        const module = await import(`file:///${fallbackPath.replace(/\\/g, "/")}`);
        return module.default;
      }
    })();
  }

  return sharpPromise;
}

function runPowerShell(script) {
  const executable = process.env.ComSpec?.toLowerCase().includes("system32")
    ? path.join(process.env.WINDIR ?? "C:\\Windows", "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
    : "powershell.exe";

  return new Promise((resolve, reject) => {
    const child = spawn(
      executable,
      [
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script
      ],
      {
        stdio: ["ignore", "pipe", "pipe"]
      }
    );

    let stderr = "";
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk);
    });
    child.stdout.on("data", () => {});
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(stderr.trim() || `PowerShell exited with code ${code}.`));
    });
  });
}

async function resizePng(sourcePath, targetPath, size) {
  const sharp = await loadSharp();
  if (sharp) {
    const source = await readFile(sourcePath);
    await mkdir(path.dirname(targetPath), { recursive: true });
    await sharp(source)
      .resize(size, size, {
        fit: "contain",
        background: { r: 0, g: 0, b: 0, alpha: 1 }
      })
      .png({ quality: 100, compressionLevel: 9 })
      .toFile(targetPath);
    return;
  }

  await mkdir(path.dirname(targetPath), { recursive: true });
  const escapedSource = sourcePath.replace(/'/g, "''");
  const escapedTarget = targetPath.replace(/'/g, "''");
  const script = `
    Add-Type -AssemblyName System.Drawing
    $sourcePath = '${escapedSource}'
    $targetPath = '${escapedTarget}'
    $size = ${size}
    $source = [System.Drawing.Image]::FromFile($sourcePath)
    try {
      $bitmap = New-Object System.Drawing.Bitmap $size, $size
      $bitmap.SetResolution($source.HorizontalResolution, $source.VerticalResolution)
      $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
      try {
        $graphics.Clear([System.Drawing.Color]::Transparent)
        $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
        $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $scale = [Math]::Min($size / $source.Width, $size / $source.Height)
        $drawWidth = [Math]::Round($source.Width * $scale)
        $drawHeight = [Math]::Round($source.Height * $scale)
        $x = [Math]::Floor(($size - $drawWidth) / 2)
        $y = [Math]::Floor(($size - $drawHeight) / 2)
        $graphics.DrawImage($source, $x, $y, $drawWidth, $drawHeight)
        $bitmap.Save($targetPath, [System.Drawing.Imaging.ImageFormat]::Png)
      } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
      }
    } finally {
      $source.Dispose()
    }
  `;
  await runPowerShell(script);
}

function buildIcoBuffer(frameBuffers) {
  const header = Buffer.alloc(6);
  header.writeUInt16LE(0, 0);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(frameBuffers.length, 4);

  const directory = Buffer.alloc(frameBuffers.length * 16);
  let offset = header.length + directory.length;

  frameBuffers.forEach(({ size, buffer }, index) => {
    const entryOffset = index * 16;
    directory.writeUInt8(size >= 256 ? 0 : size, entryOffset);
    directory.writeUInt8(size >= 256 ? 0 : size, entryOffset + 1);
    directory.writeUInt8(0, entryOffset + 2);
    directory.writeUInt8(0, entryOffset + 3);
    directory.writeUInt16LE(1, entryOffset + 4);
    directory.writeUInt16LE(32, entryOffset + 6);
    directory.writeUInt32LE(buffer.length, entryOffset + 8);
    directory.writeUInt32LE(offset, entryOffset + 12);
    offset += buffer.length;
  });

  return Buffer.concat([header, directory, ...frameBuffers.map(({ buffer }) => buffer)]);
}

async function createIco(sourcePath, targetPath, sizes) {
  const frameBuffers = [];
  const tempDirectory = path.join(ATLAS_ROOT, "tmp", "branding-build");
  await mkdir(tempDirectory, { recursive: true });

  for (const size of sizes) {
    const tempPath = path.join(tempDirectory, `${path.basename(targetPath, ".ico")}-${size}.png`);
    await resizePng(sourcePath, tempPath, size);
    frameBuffers.push({
      size,
      buffer: await readFile(tempPath)
    });
  }

  await mkdir(path.dirname(targetPath), { recursive: true });
  await writeFile(targetPath, buildIcoBuffer(frameBuffers));
}

async function validateManifest(manifest) {
  if (manifest?.schemaVersion !== 1) {
    throw new Error("Only manifest schemaVersion 1 is supported.");
  }

  const canonical = manifest?.brand?.canonical ?? {};
  const png = resolveAtlasPath(ensureString(canonical.png, "brand.canonical.png"));
  const ico = resolveAtlasPath(ensureString(canonical.ico, "brand.canonical.ico"));
  await stat(png);

  const outputs = Array.isArray(manifest.outputs) ? manifest.outputs : [];
  if (outputs.length === 0) {
    throw new Error("Manifest must define at least one output.");
  }

  return {
    canonicalPngPath: png,
    canonicalIcoPath: ico,
    outputs: outputs.map((output, index) => {
      const kind = ensureString(output.kind, `outputs[${index}].kind`);
      const target = resolveAtlasPath(ensureString(output.target, `outputs[${index}].target`));
      if (kind === "png") {
        return {
          id: ensureString(output.id, `outputs[${index}].id`),
          kind,
          size: ensureSize(output.size, `outputs[${index}].size`),
          target
        };
      }
      if (kind === "ico") {
        const sizes = Array.isArray(output.sizes) ? output.sizes.map((size, sizeIndex) => ensureSize(size, `outputs[${index}].sizes[${sizeIndex}]`)) : [];
        if (sizes.length === 0) {
          throw new Error(`outputs[${index}].sizes must include at least one size for ico outputs.`);
        }
        return {
          id: ensureString(output.id, `outputs[${index}].id`),
          kind,
          sizes,
          target
        };
      }
      throw new Error(`Unsupported output kind: ${kind}`);
    })
  };
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const manifest = await readJson(options.manifestPath);
  const validated = await validateManifest(manifest);

  await createIco(validated.canonicalPngPath, validated.canonicalIcoPath, [32, 48, 64, 128, 256]);
  console.log(`built ${path.relative(ATLAS_ROOT, validated.canonicalIcoPath)}`);

  for (const output of validated.outputs) {
    if (output.kind === "png") {
      if (output.size === 1024) {
        await mkdir(path.dirname(output.target), { recursive: true });
        await copyFile(validated.canonicalPngPath, output.target);
      } else {
        await resizePng(validated.canonicalPngPath, output.target, output.size);
      }
      console.log(`built ${path.relative(ATLAS_ROOT, output.target)}`);
      continue;
    }

    await createIco(validated.canonicalPngPath, output.target, output.sizes);
    console.log(`built ${path.relative(ATLAS_ROOT, output.target)}`);
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
