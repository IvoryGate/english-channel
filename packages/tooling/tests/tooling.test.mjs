import test from "node:test";
import assert from "node:assert/strict";
import { join, resolve } from "node:path";

import {
  resolvePythonCommand,
  resolvePythonTemp
} from "../scripts/run-python.mjs";

test("tooling smoke", () => {
  assert.equal(1 + 1, 2);
});

test("Python runner honors an explicit runtime", () => {
  assert.equal(
    resolvePythonCommand({
      env: { PYTHON_BIN: "/opt/channel/python" },
      exists: () => false,
      platform: "linux",
      repoRoot: "/repo"
    }),
    "/opt/channel/python"
  );
});

test("Python runner prefers the project environment", () => {
  const expected = "C:\\repo\\.conda-env\\python.exe";
  assert.equal(
    resolvePythonCommand({
      env: {},
      exists: (candidate) => candidate === expected,
      platform: "win32",
      repoRoot: "C:\\repo"
    }),
    expected
  );
});

test("Python runner falls back to a platform command", () => {
  assert.equal(
    resolvePythonCommand({
      env: {},
      exists: () => false,
      platform: "linux",
      repoRoot: "/repo"
    }),
    "python3"
  );
});

test("Python runner keeps temporary files in the project workspace", () => {
  assert.equal(
    resolvePythonTemp({ env: {}, repoRoot: "/repo" }),
    join("/repo", "workspace", "runtime", "tmp", "python")
  );
  assert.equal(
    resolvePythonTemp({
      env: { ELR_RUNTIME_TEMP: "workspace/custom-temp" },
      repoRoot: "/repo"
    }),
    resolve("/repo", "workspace/custom-temp")
  );
});
