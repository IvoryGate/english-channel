import { createQueueProvider } from "./queue-provider.js";
import { createTtsProvider, type TtsProvider } from "./tts-provider.js";

export type Providers = {
  queue: ReturnType<typeof createQueueProvider>;
  tts: TtsProvider;
};

export function createProviders(): Providers {
  return {
    queue: createQueueProvider(),
    tts: createTtsProvider()
  };
}
