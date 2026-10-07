# Browser Image Generation Pathway

## Goal

Give the production loop a concrete, agent-runnable image generation step:
a persistent Chromium session plus a CLI that drives the web ChatGPT image
generator and writes deterministic output files, ported from the proven
vibecut implementation. This closes the gap left after the research pass
decided against any API-key image tool.

## Scope

Included:

- `apps/worker-py/worker/imagegen/` package:
  - `session.py`: daily persistent Chromium + CDP (default port 9334 to
    avoid colliding with vibecut's 9333) with the login profile stored under
    the ignored `workspace/runtime/imagegen/chromium-profile/`.
  - `chatgpt.py`: attach-mode generation CLI adapted from vibecut
    (`--prompt`/`--prompt-file`, `--chat new|continue|<URL>`,
    `--standalone` first-login mode), anti-fingerprint behavior preserved
    verbatim (segmented typing, secrets-based pauses, challenge backoff),
    output written to an explicit `--out` path with a sidecar
    `*.meta.json` recording prompt, chat URL, mime, size, sha256, and
    timestamps for traceability.
- Thin entry scripts `apps/worker-py/scripts/imagegen_session.py` and
  `apps/worker-py/scripts/generate_image.py` following the existing
  `sys.path` convention.
- Deterministic unit tests for the pure parts (chunking, jitter bounds,
  mime mapping, parser, CDP probes) — no browser in CI.
- `docs/IMAGEGEN_BROWSER.md` (session workflow, anti-fingerprint rules,
  integration with `render_episode_thumbnail.py` and Shorts `visualBrief`)
  plus a link from `docs/shows/VIDEO_PIPELINE.md`'s cover section.

Explicit non-goals:

- No automation of login, account operations, or any write beyond image
  generation; the human logs in once per profile.
- No image generation in CI; no new Python dependencies beyond the
  playwright already present in the runtime.
- No pipeline orchestration changes: cover/shorts steps keep calling this
  CLI as an external tool.

## System Boundaries

- `apps/worker-py/worker/imagegen/` — new package (session + CLI library).
- `apps/worker-py/scripts/` — two new entry scripts.
- `apps/worker-py/tests/test_imagegen.py` — new unit tests.
- `docs/IMAGEGEN_BROWSER.md` — new doc; `docs/shows/VIDEO_PIPELINE.md`
  cover step gains the concrete command.
- Ignored runtime state: `workspace/runtime/imagegen/chromium-profile/`.
- Explicitly untouched: `.gitignore`, package manifests, CI config,
  the workspace-side `render_episode_thumbnail.py` tool, Shorts config
  schemas.

## Status

- Owner: OpenCode agent.
- Started: 2026-10-07.
- State: completed 2026-10-07. Package, entry scripts, tests (7), docs,
  and live smoke evidence all done (lint exit 0, Python 222/222); archived
  in this PR.

## Plan

1. Branch and this plan.
2. Package + entry scripts + tests.
3. Docs (`IMAGEGEN_BROWSER.md`, VIDEO_PIPELINE link).
4. Gates, PR, CI green, merge; archive this plan in the same PR.

## Validation

- `npm run lint` (encoding + `compileall` over `worker/` and `scripts/`)
  exits 0.
- `npm run test` green including the new imagegen unit tests.
- Live smoke (all passed on the production host): session starts on the
  blank-tab recipe and answers `/json/version`; the CLI without a session
  fails with the explicit "start it first" message; an attached CLI
  navigates to chatgpt.com, runs the login check and exits 1 with
  "login expired" on the fresh profile (the one human step); a second
  attach probe after that navigation still connects (the wedge-free
  recipe), and a repeated CLI run is stable. Generation itself requires
  the human login and stays a manual exercise.

## Risks And Decisions

- Decision: port from vibecut rather than rewrite — the anti-fingerprint
  behavior (segmented typing, real-entropy pauses, challenge backoff) is
  tuned and proven; selector strings stay Chinese because the session runs
  with `--lang=zh-CN`.
- Decision: profile lives under ignored `workspace/runtime/`, so no
  `.gitignore` change is needed and login state survives cleanup.
- Decision: CDP default port 9334, overridable via
  `EN_CHANNEL_CDP_PORT`, so a vibecut session (9333) can coexist.
- Decision (discovered during the live smoke): the session browser must
  start on a **blank tab**, not on chatgpt.com. Verified on this machine
  that a startup-URL navigation with no CDP client attached wedges the
  DevTools endpoint permanently (Chrome 151, both bundled builds), while
  client-driven `page.goto` keeps the session attachable. Navigation
  therefore belongs to `select_attached_page`, which already runs after
  every attach.
- Risk: ChatGPT UI changes break selectors. Mitigation: fail loudly with
  the existing explicit error paths; selectors are centralized at module
  top.
- Risk: `render_episode_thumbnail.py` lives in the ignored workspace tree
  and is not part of this repo's gates; the doc links the workflow but the
  integration is verified manually.

## Archive Criteria

- Merged PR with green gates, live smoke evidence recorded above, and this
  plan moved to `docs/exec-plans/completed/` in the same PR.
