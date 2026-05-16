import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

const apiRoot = join(process.cwd(), "apps", "api", "src");
const layerOrder = ["types", "schema", "repo", "service", "transport"];
const layerIndex = Object.fromEntries(layerOrder.map((layer, index) => [layer, index]));
const importPattern = /from\s+["']\.\.\/([^/"']+)/g;

function collectFiles(dir, files = []) {
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    if (statSync(fullPath).isDirectory()) {
      collectFiles(fullPath, files);
      continue;
    }
    if (fullPath.endsWith(".ts")) files.push(fullPath);
  }
  return files;
}

const violations = [];

for (const filePath of collectFiles(apiRoot)) {
  const source = readFileSync(filePath, "utf8");
  const srcRelative = relative(apiRoot, filePath);
  const currentLayer = srcRelative.split(sep)[0];
  if (!currentLayer || !(currentLayer in layerIndex)) continue;

  for (const match of source.matchAll(importPattern)) {
    const importedLayer = match[1];
    if (!(importedLayer in layerIndex)) continue;
    if (layerIndex[importedLayer] > layerIndex[currentLayer]) {
      violations.push(`${filePath} imports forbidden forward layer "${importedLayer}"`);
    }
  }
}

if (violations.length > 0) {
  console.error("Architecture violations found:");
  for (const violation of violations) {
    console.error(`- ${violation}`);
  }
  process.exit(1);
}

console.log("Architecture check passed");
