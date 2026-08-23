import Fastify from "fastify";
import { registerRoutes } from "./transport/routes.js";
import type { Providers } from "./providers/index.js";

export function buildServer(providers: Providers) {
  const app = Fastify({ logger: true });
  registerRoutes(app, providers);
  return app;
}
