import { JobStatus } from "@english-channel/shared-types";

export type JobRecord = {
  id: string;
  chapterId: string;
  text: string;
  status: JobStatus;
  tracePath?: string;
  audioPath?: string;
  modelId?: string;
  error?: string;
  createdAt: string;
  updatedAt: string;
};
