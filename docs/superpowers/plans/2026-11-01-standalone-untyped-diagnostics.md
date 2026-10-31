# Standalone unresolved-type diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Warn on unresolved external types by default, and add opt-in `--require-types` preflight failure before standalone output is copied.

**Architecture:** Inspect a parsed `InputFileSpec` in `Command.Standalone.command'`, using the same `addMissingIdentifiers` function used by generation. Keep `commandLogic` and other backends unchanged; carry a boolean from the standalone CLI to the core command options. Use existing HUnit tests and a native CLI smoke job to establish observed stderr/exit/output behavior.

**Tech Stack:** Haskell, Cabal, HUnit, optparse-applicative; GitHub Actions GHC 9.2.8 / Cabal 3.14.

**Spec:** `docs/superpowers/specs/2026-11-01-standalone-untyped-diagnostics-design.md`

## Global Constraints

- Branch from `nasa/ogma@08b384b4335cce324fac74577adc7f08e61b7cce` in `metalogiclabs/ogma`; never mutate `develop` or upstream.
- Preserve default `standalone` exit status and generated source; stderr warning may be new.
- Strict check only for external variable types empty after implicit identifiers are added.
- No changes to the shared generator signature used by ROS, cFS, and F´.
- Do not infer Haskell types or assert C monitor compilation.

## Review Focus

- Two missing external identifiers in one property: warning/error lists each exactly once.
- Explicit `type:""` in `Other_variables`: same strict rejection as synthesized types.
- Mapped Boolean `sensor_ok`: strict acceptance without a warning.
- Legacy permissive `fcs_good.json`: default success unchanged.
- Missing-type strict error: output directory does not receive a generated `Copilot.hs`.

---

### Task 1: Core preflight and result semantics

**Files:**
- Create: `ogma-core/tests/fcs-untyped-sensor.json`
- Create: `ogma-core/tests/fcs-typed-sensor.json`
- Modify: `ogma-core/tests/Main.hs`
- Modify: `ogma-core/src/Command/Standalone.hs`

**Interfaces:** `CommandOptions.commandRequireTypes :: Bool`; `Command.Standalone.command :: CommandOptions -> IO (Result ErrorCode)`. No change to `commandLogic` type.

- [ ] Add HUnit test cases for default unmapped success, strict unmapped error naming `sensor_ok`, strict mapped success, and explicit empty type rejection.
- [ ] Run the test suite in CI *before* implementation and observe RED due to the missing `commandRequireTypes` option / strict behavior (not a setup failure).
- [ ] Implement a pure unresolved external-name extraction from the parsed standalone spec; print warning to stderr in permissive mode and return an `ErrorTriplet` in strict mode before template copy. Keep other backends untouched.
- [ ] Rerun HUnit suite and require GREEN, including existing tests.
- [ ] Commit with the tests and core behavior together after GREEN.

### Task 2: CLI flag and end-to-end smoke

**Files:**
- Modify: `ogma-cli/src/CLI/CommandStandalone.hs`
- Create: `ogma-cli/tests/standalone-require-types.sh`
- Create: `.github/workflows/research-standalone-types.yml`

**Interfaces:** `standaloneRequireTypes :: Bool` maps to `Command.Standalone.commandRequireTypes`; new CLI flag `--require-types`.

- [ ] Add executable CLI smoke assertions: default unmapped warns and generates, `--require-types` unmapped exits nonzero with `sensor_ok` and no generated file, strict mapped exits zero without warning.
- [ ] Run CLI smoke before the parser flag exists and observe expected RED (`unrecognized option` or failed required behavior).
- [ ] Add the optparse-applicative `switch` parser, propagate its value in both normal and `--project` option constructors.
- [ ] Run CLI smoke and core suite; require GREEN.
- [ ] Commit the CLI, smoke test, and research CI workflow.

### Task 3: Bounded verification and documentation

**Files:**
- Modify: `ogma-cli/README.md` if present, else add a research-only documentation note near the new smoke test.
- Modify: `docs/superpowers/specs/2026-11-01-standalone-untyped-diagnostics-design.md` only if the implementation forces a documented ruling.

**Interfaces:** user-facing `ogma standalone --require-types`; default warning remains documented.

- [ ] Run targeted native HUnit + CLI test workflow in GitHub Actions; capture exact run ID, exit codes, and artifacts.
- [ ] Run broad feasible project tests or record precisely which existing workflows do not run on this branch.
- [ ] Review the complete diff against the pinned base for accidental effects on ROS/cFS/F´ and generated templates.
- [ ] Commit documentation and hand over the research branch, evidence, and remaining unknowns without upstream PR.
