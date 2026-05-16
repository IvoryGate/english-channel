import { z } from "zod";

export const createTtsJobSchema = z.object({
  chapterId: z.string().min(1),
  text: z.string().min(10),
  voiceProfile: z.string().default("default-narrator")
});

export type CreateTtsJobInput = z.infer<typeof createTtsJobSchema>;
