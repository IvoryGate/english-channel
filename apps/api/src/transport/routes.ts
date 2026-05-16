import type { FastifyInstance } from "fastify";
import { createTtsJobSchema } from "../schema/tts.js";
import { createTtsService } from "../service/tts-service.js";
import type { Providers } from "../providers/index.js";
import { getJob } from "../repo/job-repo.js";

export function registerRoutes(app: FastifyInstance, providers: Providers) {
  const ttsService = createTtsService(providers);

  app.get("/health", async () => ({ ok: true }));
  app.get("/jobs", async () => ({ jobs: ttsService.list() }));
  app.get("/jobs/:id", async (request, reply) => {
    const { id } = request.params as { id: string };
    const job = getJob(id);
    if (!job) return reply.code(404).send({ error: "job_not_found" });
    return { job };
  });
  app.post("/jobs", async (request, reply) => {
    const payload = createTtsJobSchema.parse(request.body);
    const job = await ttsService.enqueue(payload);
    return reply.code(202).send({ job });
  });
}
