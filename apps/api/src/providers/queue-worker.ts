import { Worker } from "bullmq";
import { markJobCompleted, markJobFailed, markJobRunning } from "../repo/job-repo.js";
import { getQueueConnection, TTS_QUEUE_NAME, type TtsQueuePayload } from "./queue-provider.js";
import type { TtsProvider } from "./tts-provider.js";

export async function processTtsQueueJob(payload: TtsQueuePayload, tts: TtsProvider) {
  markJobRunning(payload.jobId);
  try {
    const trace = await tts.runInline(payload);
    markJobCompleted(payload.jobId, {
      audioPath: trace.audioPath,
      tracePath: trace.tracePath,
      modelId: trace.modelId
    });
    return trace;
  } catch (error) {
    markJobFailed(payload.jobId, error instanceof Error ? error.message : "unknown worker error");
    throw error;
  }
}

export function startTtsQueueWorker(tts: TtsProvider) {
  return new Worker<TtsQueuePayload>(
    TTS_QUEUE_NAME,
    async (job) => processTtsQueueJob(job.data, tts),
    { connection: getQueueConnection() }
  );
}
