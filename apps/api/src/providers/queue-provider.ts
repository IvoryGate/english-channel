import { Queue } from "bullmq";

export const TTS_QUEUE_NAME = "voxcpm-tts";

export type TtsQueuePayload = {
  jobId: string;
  chapterId: string;
  text: string;
  voiceProfile: string;
};

export function getQueueConnection() {
  return {
    host: process.env.REDIS_HOST ?? "127.0.0.1",
    port: Number(process.env.REDIS_PORT ?? 6379)
  };
}

export function createQueueProvider() {
  const queue = new Queue<TtsQueuePayload>(TTS_QUEUE_NAME, { connection: getQueueConnection() });

  return {
    async enqueueTtsJob(payload: TtsQueuePayload) {
      await queue.add("generate-chapter-audio", payload, {
        attempts: 3,
        removeOnComplete: true
      });
    },
    async close() {
      await queue.close();
    }
  };
}
