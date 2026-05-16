import { spawn } from "node:child_process";
import { join } from "node:path";

type TtsResult = {
  jobId: string;
  chapterId: string;
  modelId: string;
  tracePath: string;
  audioPath: string;
};

export function createTtsProvider() {
  return {
    runInline(payload: { jobId: string; chapterId: string; text: string; voiceProfile: string }) {
      const pythonCmd =
        process.env.PYTHON_BIN ??
        (process.platform === "win32" ? ".\\.conda-env\\python.exe" : "python");
      const modulePath = "worker.main";
      const workerRoot = process.env.WORKER_ROOT ?? "apps/worker-py";
      return new Promise<TtsResult>((resolve, reject) => {
        const child = spawn(pythonCmd, ["-m", modulePath], {
          cwd: workerRoot,
          env: {
            ...process.env,
            PYTHONPATH: ".",
            VOXCPM_MODEL_ID: process.env.VOXCPM_MODEL_ID ?? "pretrained_models/VoxCPM2",
            SAMPLE_PAYLOAD: JSON.stringify(payload)
          }
        });
        let stdout = "";
        let stderr = "";
        child.stdout.on("data", (d) => (stdout += d.toString()));
        child.stderr.on("data", (d) => (stderr += d.toString()));
        child.on("close", (code) => {
          if (code !== 0) return reject(new Error(stderr || `worker exited ${code}`));
          try {
            resolve(JSON.parse(stdout) as TtsResult);
          } catch (e) {
            reject(e);
          }
        });
      });
    }
  };
}
