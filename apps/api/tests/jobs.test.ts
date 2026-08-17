import test from "node:test";
import assert from "node:assert/strict";
import { buildServer } from "../src/index.js";
import type { Providers } from "../src/providers/index.js";

function createTestProviders(): Providers {
  return {
    queue: {
      enqueueTtsJob: async () => undefined,
      close: async () => undefined
    },
    tts: {
      runInline: async () => ({
        jobId: "test-job",
        chapterId: "ch-001",
        modelId: "test-model",
        tracePath: "trace.json",
        audioPath: "chapter.wav"
      })
    }
  };
}

test("POST /jobs creates queued job", async () => {
  const app = buildServer(createTestProviders());
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
