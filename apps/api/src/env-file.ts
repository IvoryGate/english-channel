import { existsSync } from "node:fs";

/**
 * Load `KEY=value` pairs from an env file into `process.env`.
 *
 * Values already present in the real process environment always win; the
 * file only fills gaps (verified against `process.loadEnvFile` semantics),
 * which keeps CI-provided variables authoritative. A missing file is a
 * no-op so fresh clones and CI runners need no setup.
 */
export function loadEnvFile(path: string): void {
  if (!existsSync(path)) return;
  process.loadEnvFile(path);
}
