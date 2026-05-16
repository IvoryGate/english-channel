import process from "node:process";

const maxIterations = Number(process.env.AGENT_MAX_ITERATIONS ?? "2");
const currentIteration = Number(process.env.AGENT_CURRENT_ITERATION ?? "1");
const fallbackReviewer = process.env.AGENT_FALLBACK_REVIEWER ?? "human-maintainer";

if (currentIteration > maxIterations) {
  console.log(JSON.stringify({ action: "handoff", reason: "max_iterations_reached", reviewer: fallbackReviewer }));
  process.exit(0);
}

console.log(
  JSON.stringify({
    action: "agent_review",
    iteration: currentIteration,
    nextIteration: currentIteration + 1,
    hint: "Run automated review and bounded auto-fix cycle."
  })
);
