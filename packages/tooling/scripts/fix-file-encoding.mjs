import { readFileSync, writeFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const ignoredDirs = new Set([".git", "node_modules", ".venv", ".conda-env", ".next", "dist", "artifacts", "pretrained_models"]);
const checkedExtensions = new Set([
  ".md",
  ".json",
  ".ts",
  ".tsx",
  ".mjs",
  ".js",
  ".css",
  ".yml",
  ".yaml",
  ".toml",
  ".py",
  ".txt",
  ".ps1",
  ".env"
]);
const checkedNames = new Set([".gitignore", ".editorconfig"]);

function walk(dir, files = []) {
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    const stat = statSync(fullPath);
    if (stat.isDirectory()) {
      if (!ignoredDirs.has(entry)) walk(fullPath, files);
      continue;
    }
    files.push(fullPath);
  }
  return files;
}

function extensionOf(path) {
  const match = path.match(/\.[^.\\/]+$/);
  return match ? match[0] : "";
}

function likelyUtf16Le(bytes) {
  if (bytes.length < 4) return false;
  let nulls = 0;
  const sample = Math.min(bytes.length, 2000);
  for (let i = 1; i < sample; i += 2) {
    if (bytes[i] === 0) nulls += 1;
  }
  return nulls > sample / 6;
}

let changed = 0;

for (const file of walk(root)) {
  const name = file.split(/[\\/]/).pop();
  const ext = extensionOf(file);
  if (!checkedExtensions.has(ext) && !checkedNames.has(name)) continue;

  const bytes = readFileSync(file);
  let text;
  if (bytes.length >= 2 && bytes[0] === 0xff && bytes[1] === 0xfe) {
    text = bytes.subarray(2).toString("utf16le");
  } else if (likelyUtf16Le(bytes)) {
    text = bytes.toString("utf16le");
  } else if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
    text = bytes.subarray(3).toString("utf8");
  } else {
    text = bytes.toString("utf8");
  }

  const normalized = text.replace(/\u{0A0D}/gu, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const output = Buffer.from(normalized, "utf8");
  if (!bytes.equals(output)) {
    writeFileSync(file, output);
    changed += 1;
  }
}

console.log(`Normalized ${changed} files to UTF-8 LF`);