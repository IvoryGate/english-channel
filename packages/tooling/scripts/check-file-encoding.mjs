import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const root = process.cwd();
const ignoredDirs = new Set([
  ".git",
  "node_modules",
  ".venv",
  ".conda-env",
  ".next",
  "dist",
  "artifacts",
  "assets",
  "books",
  "reference",
  "tmp",
  "workspace",
  "pretrained_models",
  ".pytest_cache",
  "__pycache__"
]);
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
const crlfAllowedExtensions = new Set([".cmd", ".bat"]);
const strayUnicodeCarriage = String.fromCodePoint(0x0a0d);

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

const violations = [];

for (const file of walk(root)) {
  const name = file.split(/[\\/]/).pop();
  const ext = extensionOf(file);
  if (!checkedExtensions.has(ext) && !checkedNames.has(name) && !crlfAllowedExtensions.has(ext)) continue;

  const bytes = readFileSync(file);
  const rel = relative(root, file);

  if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
    violations.push(`${rel}: UTF-8 BOM is forbidden`);
  }
  if (bytes.includes(0)) {
    violations.push(`${rel}: null byte found, likely UTF-16`);
  }
  if (!crlfAllowedExtensions.has(ext) && bytes.includes(13)) {
    violations.push(`${rel}: CRLF/CR line ending found; use LF`);
  }
  const text = bytes.toString("utf8");
  if (text.includes(strayUnicodeCarriage)) {
    violations.push(`${rel}: stray U+0A0D character found`);
  }
}

if (violations.length > 0) {
  console.error("Encoding violations found:");
  for (const violation of violations) console.error(`- ${violation}`);
  process.exit(1);
}

console.log("Encoding check passed");