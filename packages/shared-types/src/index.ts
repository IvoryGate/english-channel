export enum JobStatus {
  queued = "queued",
  running = "running",
  completed = "completed",
  failed = "failed"
}

export type TtsJobRequest = {
  chapterId: string;
  text: string;
  voiceProfile?: string;
};
