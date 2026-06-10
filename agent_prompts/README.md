# Agent Prompt Pack

This folder contains role prompts for running the Runtime Policy Enforcement Gate build in a gstack-style workflow.

The idea is not to run a complex autonomous multi-agent system. The idea is to use specialist role prompts as checkpoints:

```text
Architect → Implementer → Reviewer → QA → Release Manager
```

Optional roles:

```text
Spec Guardian → used when product/spec ambiguity appears
Demo Reviewer → used for UI, README, demo script, and buyer-facing narrative
```

## How to use with web Codex

Start a new Codex task and paste the relevant role prompt at the top of the task.

Typical sequence:

1. Use `architect.md` to produce a task brief.
2. Use `implementer.md` to implement exactly one task.
3. Use `reviewer.md` to inspect the diff.
4. Use `qa.md` to verify behaviour.
5. Use `release_manager.md` to decide whether the human can mark the task `DONE`.

## Recommended first workflow

For T01:

```text
1. Architect: select T01 and produce a brief.
2. Implementer: implement T01 only.
3. Reviewer: review T01 diff only.
4. QA: run/inspect T01 verification.
5. Human: mark T01 DONE if satisfied.
```

## Important

These prompts assume the repo contains:

- `AGENTS.md`
- `MASTER_SPEC.md`
- `TASK_LEDGER.md`

They are designed around a strict pipeline. Only the Implementer should modify code, and only for the current task.
