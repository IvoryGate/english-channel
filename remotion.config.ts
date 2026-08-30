import {Config} from '@remotion/cli/config';

const requestedConcurrency = Number.parseInt(process.env.ELR_REMOTION_CONCURRENCY ?? '4', 10);
const renderConcurrency = Number.isFinite(requestedConcurrency)
  ? Math.min(8, Math.max(1, requestedConcurrency))
  : 4;

Config.setVideoImageFormat('png');
Config.setOverwriteOutput(true);
Config.setConcurrency(renderConcurrency);
