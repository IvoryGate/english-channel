import { JobStatus } from "@english-channel/shared-types";
import { randomUUID } from "node:crypto";
import type { CreateTtsJobInput } from "../schema/tts.js";
import type { JobRecord } from "../types/job.js";

const jobs = new Map<string, JobRecord>();

export function createJob(input: CreateTtsJobInput): JobRecord {
  const now = new Date().toISOString();
  const job: JobRecord = {
    id: randomUUID(),
    chapterId: input.chapterId,
    text: input.text,
    status: JobStatus.queued,
    createdAt: now,
    updatedAt: now
  };
  jobs.set(job.id, job);
  return job;
}

export function listJobs(): JobRecord[] {
  return [...jobs.values()];
}

export function getJob(jobId: string): JobRecord | undefined {
  return jobs.get(jobId);
}

export function markJobRunning(jobId: string) {
  const current = jobs.get(jobId);
  if (!current) return;
  jobs.set(jobId, { ...current, status: JobStatus.running, updatedAt: new Date().toISOString() });
}

export function markJobCompleted(jobId: string, payload: { audioPath: string; tracePath: string; modelId: string }) {
  const current = jobs.get(jobId);
  if (!current) return;
  jobs.set(jobId, {
    ...current,
    status: JobStatus.completed,
    audioPath: payload.audioPath,
    tracePath: payload.tracePath,
    modelId: payload.modelId,
    updatedAt: new Date().toISOString()
  });
}

export function markJobFailed(jobId: string, error: string) {
  const current = jobs.get(jobId);
  if (!current) return;
  jobs.set(jobId, { ...current, status: JobStatus.failed, error, updatedAt: new Date().toISOString() });
}
