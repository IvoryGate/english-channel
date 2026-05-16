import { createQueueProvider } from "./queue-provider.js";
import { createTtsProvider } from "./tts-provider.js";

export type Providers = {
  queue: ReturnType<typeof createQueueProvider>;
  tts: ReturnType<typeof createTtsProvider>;
};

export function createProviders(): Providers {
  return {
    queue: createQueueProvider(),
    tts: createTtsProvider()
  };
}
