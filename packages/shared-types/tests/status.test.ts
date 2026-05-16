import test from "node:test";
import assert from "node:assert/strict";
import { JobStatus } from "../src/index.js";

test("JobStatus should expose terminal statuses", () => {
  assert.ok(Object.values(JobStatus).includes("completed"));
  assert.ok(Object.values(JobStatus).includes("failed"));
});
