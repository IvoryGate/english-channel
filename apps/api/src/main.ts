import { buildServer } from "./index.js";
import { createProviders } from "./providers/index.js";
import { startTtsQueueWorker } from "./providers/queue-worker.js";

const providers = createProviders();
const app = buildServer(providers);
const queueWorker =
  (process.env.JOB_EXECUTION_MODE ?? "queue") === "queue"
    ? startTtsQueueWorker(providers.tts)
    : undefined;

app.addHook("onClose", async () => {
  await queueWorker?.close();
  await providers.queue.close();
});

app.listen({ port: 4000, host: "0.0.0.0" }).catch((err) => {
  app.log.error(err);
  process.exit(1);
});
