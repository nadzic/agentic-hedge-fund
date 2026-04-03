# Agents Eval (Minimal)

This folder contains a minimal evaluation baseline for the agents workflow.

## Minimal structure

- `datasets/nodes`: Golden cases for node-level behavior.
- `datasets/graph`: Golden cases for routing / edge-level behavior.
- `datasets/e2e`: Golden cases for full workflow scenarios.
- `runners`: Starter runners for each evaluation layer.
- `metrics`: Shared metric helpers.
- `configs`: Thresholds and run profiles.

## Current scope

This is a contract-first setup:

- versioned datasets in git
- schema/contract checks with pytest
- placeholders for execution runners

## Run checks

```bash
uv run pytest -q evals/agents --no-cov
```

## Next step

Implement runners to execute real graph calls and output:

- pass rate by layer
- safety violations
- latency p50/p95
- top failure reasons
