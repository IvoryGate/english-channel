import type { CreateTtsJobInput } from "../schema/tts.js";
import {
  createJob,
  listJobs,
  markJobCompleted,
  markJobFailed,
  markJobRunning
} from "../repo/job-repo.js";
import type { Providers } from "../providers/index.js";

export function createTtsService(providers: Providers) {
  return {
    async enqueue(input: CreateTtsJobInput) {
      const job = createJob(input);
      if ((process.env.JOB_EXECUTION_MODE ?? "queue") === "inline") {
        try {
          markJobRunning(job.id);
          const trace = await providers.tts.runInline({
            jobId: job.id,
            chapterId: job.chapterId,
            text: job.text,
            voiceProfile: input.voiceProfile
          });
          markJobCompleted(job.id, {
            audioPath: trace.audioPath,
            tracePath: trace.tracePath,
            modelId: trace.modelId
          });
        } catch (err) {
          markJobFailed(job.id, err instanceof Error ? err.message : "unknown worker error");
        }
      } else {
        await providers.queue.enqueueTtsJob({
          jobId: job.id,
          chapterId: job.chapterId,
          text: job.text,
          voiceProfile: input.voiceProfile
        });
      }
      return job;
    },
    list: listJobs
  };
}
