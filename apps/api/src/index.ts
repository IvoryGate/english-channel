import Fastify from "fastify";
import { registerRoutes } from "./transport/routes.js";
import { createProviders, type Providers } from "./providers/index.js";
import { startTtsQueueWorker } from "./providers/queue-worker.js";

export function buildServer(providers: Providers = createProviders()) {
  const app = Fastify({ logger: true });
  registerRoutes(app, providers);
  return app;
}

if (process.env.NODE_ENV !== "test") {
  const providers = createProviders();
  const app = buildServer(providers);
  const queueWorker =
    (process.env.JOB_EXECUTION_MODE ?? "queue") === "queue" ? startTtsQueueWorker(providers.tts) : undefined;
  app.addHook("onClose", async () => {
    await queueWorker?.close();
    await providers.queue.close();
  });
  app.listen({ port: 4000, host: "0.0.0.0" }).catch((err) => {
    app.log.error(err);
    process.exit(1);
  });
}
