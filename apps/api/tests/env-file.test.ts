import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadEnvFile } from "../src/env-file.js";

test("loadEnvFile fills gaps and keeps existing process env", () => {
  const dir = mkdtempSync(join(tmpdir(), "env-file-"));
  const file = join(dir, "sample.env");
  writeFileSync(
    file,
    "# comment line\nLOADENV_EXISTING=fromfile\nLOADENV_NEW=fromfile\n",
    "utf8",
  );
  process.env.LOADENV_EXISTING = "fromenv";
  try {
    loadEnvFile(file);
    assert.equal(process.env.LOADENV_EXISTING, "fromenv");
    assert.equal(process.env.LOADENV_NEW, "fromfile");
  } finally {
    delete process.env.LOADENV_EXISTING;
    delete process.env.LOADENV_NEW;
    rmSync(dir, { recursive: true, force: true });
  }
});

test("loadEnvFile ignores a missing file without throwing", () => {
  loadEnvFile(join(tmpdir(), "definitely-missing-env-file.env"));
  assert.ok(true);
});
