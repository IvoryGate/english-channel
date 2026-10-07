import { fileURLToPath } from "node:url";
import { loadEnvFile } from "./env-file.js";

// Side-effect module. It MUST stay the first import in `main.ts`:
// `job-repo.ts` resolves JOB_STORE_PATH at module scope, so the repo root
// `.env` has to be loaded before any module that reads `process.env`.
// The path resolves from `import.meta.url`, so `src/` (tsx dev) and `dist/`
// (node start) both reach the repo root regardless of the npm cwd.
loadEnvFile(fileURLToPath(new URL("../../../.env", import.meta.url)));
