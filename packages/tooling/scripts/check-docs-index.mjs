import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");

const requiredDocs = [
  "ARCHITECTURE.md",
  "FRONTEND.md",
  "BACKEND.md",
  "TTS_PIPELINE.md",
  "QUALITY_SCORE.md",
  "RELIABILITY.md",
  "SECURITY.md",
  "PLANS.md",
  "GIT_WORKFLOW.md",
  "LOCAL_RUNTIME.md",
  "ENCODING.md"
];

const docsRoot = join(repoRoot, "docs");
const readmePath = join(repoRoot, "README.md");
const agentsPath = join(repoRoot, "AGENTS.md");

const missing = requiredDocs.filter((file) => !existsSync(join(docsRoot, file)));
if (missing.length > 0) {
  console.error(`Missing required docs: ${missing.join(", ")}`);
  process.exit(1);
}

if (!existsSync(readmePath) || !existsSync(agentsPath)) {
  console.error("README.md and AGENTS.md must exist");
  process.exit(1);
}

const agents = readFileSync(agentsPath, "utf8");
if (!agents.includes("docs/")) {
  console.error("AGENTS.md must point to docs/ as system of record");
  process.exit(1);
}
if (!agents.includes("docs/ENCODING.md")) {
  console.error("AGENTS.md must reference docs/ENCODING.md");
  process.exit(1);
}
if (agents.split("\n").length > 120) {
  console.error("AGENTS.md should stay concise (<= 120 lines)");
  process.exit(1);
}

console.log("Docs index check passed");