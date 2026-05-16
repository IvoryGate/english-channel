import { Queue } from "bullmq";

const queueName = "voxcpm-tts";

export function createQueueProvider() {
  const connection = {
    host: process.env.REDIS_HOST ?? "127.0.0.1",
    port: Number(process.env.REDIS_PORT ?? 6379)
  };
  const queue = new Queue(queueName, { connection });

  return {
    async enqueueTtsJob(payload: { jobId: string; chapterId: string; text: string; voiceProfile?: string }) {
      await queue.add("generate-chapter-audio", payload, {
        attempts: 3,
        removeOnComplete: true
      });
    }
  };
}
