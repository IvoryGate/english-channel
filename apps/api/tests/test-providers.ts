import type { Providers } from "../src/providers/index.js";

export function createTestProviders(): Providers {
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
