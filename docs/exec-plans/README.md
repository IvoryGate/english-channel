# Execution Plans

This directory stores durable implementation plans for agent-driven work.

`active/` contains work that is planned or in progress. `completed/` contains plans whose scope has shipped or is otherwise closed. Plans are repository state, not chat notes; future agents should be able to read them and understand what is being built, why it matters, what decisions were made, and what validation remains.

For full rules, see `docs/PLANS.md` and `AGENTS.md`.

## When To Create A Plan

Create an active plan when work:

- spans more than a small single-file change,
- touches multiple apps, packages, infrastructure, runtime setup, or docs,
- changes workflow rules or agent behavior,
- needs phased implementation across sessions,
- carries meaningful validation or rollback risk.

Skip execution plans for trivial edits, generated artifacts, downloaded model weights, scratch notes, and local-only experiment output.

## Minimal Template

```markdown
# YYYY-MM-DD Short Topic

## Goal

## Scope

## System Boundaries

## Status

## Plan

## Validation

## Risks And Decisions

## Archive Criteria
```
