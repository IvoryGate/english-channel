import { JobStatus } from "@english-channel/shared-types";
import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import type { CreateTtsJobInput } from "../schema/tts.js";
import type { JobRecord } from "../types/job.js";

const jobStorePath = resolve(process.env.JOB_STORE_PATH ?? "artifacts/jobs.json");
const jobs = loadJobs();

function loadJobs(): Map<string, JobRecord> {
  if (!existsSync(jobStorePath)) return new Map();
  const records = JSON.parse(readFileSync(jobStorePath, "utf8")) as JobRecord[];
  return new Map(records.map((job) => [job.id, job]));
}

function persistJobs() {
  mkdirSync(dirname(jobStorePath), { recursive: true });
  writeFileSync(jobStorePath, JSON.stringify([...jobs.values()], null, 2), "utf8");
}

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
  persistJobs();
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
  persistJobs();
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
  persistJobs();
}

export function markJobFailed(jobId: string, error: string) {
  const current = jobs.get(jobId);
  if (!current) return;
  jobs.set(jobId, { ...current, status: JobStatus.failed, error, updatedAt: new Date().toISOString() });
  persistJobs();
}
