import { existsSync, mkdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const defaultRepoRoot = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  ".."
);

export function resolvePythonCommand({
  repoRoot = defaultRepoRoot,
  platform = process.platform,
  env = process.env,
  exists = existsSync
} = {}) {
  const override = String(env.PYTHON_BIN ?? "").trim();
  if (override) {
    return override;
  }

  const localPython =
    platform === "win32"
      ? join(repoRoot, ".conda-env", "python.exe")
      : join(repoRoot, ".conda-env", "bin", "python");
  if (exists(localPython)) {
    return localPython;
  }
  return platform === "win32" ? "python" : "python3";
}

export function resolvePythonTemp({
  repoRoot = defaultRepoRoot,
  env = process.env
} = {}) {
  const override = String(env.ELR_RUNTIME_TEMP ?? "").trim();
  return override
    ? resolve(repoRoot, override)
    : join(repoRoot, "workspace", "runtime", "tmp", "python");
}

export function runPython(args = process.argv.slice(2)) {
  const python = resolvePythonCommand();
  const temp = resolvePythonTemp();
  mkdirSync(temp, { recursive: true });
  const result = spawnSync(python, args, {
    cwd: defaultRepoRoot,
    env: {
      ...process.env,
      TEMP: temp,
      TMP: temp,
      TMPDIR: temp
    },
    shell: false,
    stdio: "inherit"
  });
  if (result.error) {
    console.error(`Unable to start Python with ${python}: ${result.error.message}`);
    return 1;
  }
  return result.status ?? 1;
}

const invokedUrl = process.argv[1]
  ? pathToFileURL(resolve(process.argv[1])).href
  : "";
if (import.meta.url === invokedUrl) {
  process.exitCode = runPython();
}
