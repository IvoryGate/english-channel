import Fastify from "fastify";
import { registerRoutes } from "./transport/routes.js";
import { createProviders } from "./providers/index.js";

export function buildServer() {
  const app = Fastify({ logger: true });
  const providers = createProviders();
  registerRoutes(app, providers);
  return app;
}

if (process.env.NODE_ENV !== "test") {
  const app = buildServer();
  app.listen({ port: 4000, host: "0.0.0.0" }).catch((err) => {
    app.log.error(err);
    process.exit(1);
  });
}
