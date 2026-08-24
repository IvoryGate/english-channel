import test from "node:test";
import assert from "node:assert/strict";
import { buildServer } from "../src/index.js";
import { createTestProviders } from "./test-providers.js";

test("GET /health returns ok", async () => {
  const app = buildServer(createTestProviders());
  const response = await app.inject({ method: "GET", url: "/health" });
  assert.equal(response.statusCode, 200);
  assert.deepEqual(response.json(), { ok: true });
  await app.close();
});
