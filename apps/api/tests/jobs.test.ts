import test from "node:test";
import assert from "node:assert/strict";
import { buildServer } from "../src/index.js";

test("POST /jobs creates queued job", async () => {
  const app = buildServer();
  const response = await app.inject({
    method: "POST",
    url: "/jobs",
    payload: {
      chapterId: "ch-001",
      text: "Chapter one opens with rain and distant thunder over the old town.",
      voiceProfile: "default-narrator"
    }
  });
  assert.equal(response.statusCode, 202);
  const body = response.json() as { job: { chapterId: string; status: string } };
  assert.equal(body.job.chapterId, "ch-001");
  assert.equal(body.job.status, "queued");
  await app.close();
});
