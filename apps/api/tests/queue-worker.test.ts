import test from "node:test";
import assert from "node:assert/strict";
import { createJob, getJob } from "../src/repo/job-repo.js";
import { processTtsQueueJob } from "../src/providers/queue-worker.js";

test("BullMQ processor runs Python TTS and records completion", async () => {
  const created = createJob({
    chapterId: `queue-worker-${Date.now()}`,
    text: "A queue worker hands the request to the Python VoxCPM process.",
    voiceProfile: "default-narrator"
  });

  await processTtsQueueJob(
    { jobId: created.id, chapterId: created.chapterId, text: created.text, voiceProfile: "default-narrator" },
    {
      runInline: async (payload) => ({
        jobId: payload.jobId,
        chapterId: payload.chapterId,
        modelId: "test-model",
        tracePath: "artifacts/trace.json",
        audioPath: "artifacts/chapter.wav"
      })
    }
  );

  const completed = getJob(created.id);
  assert.equal(completed?.status, "completed");
  assert.equal(completed?.modelId, "test-model");
});
