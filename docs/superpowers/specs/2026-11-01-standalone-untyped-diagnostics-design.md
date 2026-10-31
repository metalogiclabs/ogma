# Standalone Copilot unresolved-type diagnostics — design

Date: 2026-11-01 (NZ). Research-only branch; no upstream issue or PR.

## Intent

Make `ogma standalone` honest about missing external signal types. FRET legitimately exports a Copilot specification with no variable mappings; Ogma adds an external declaration with type `_`, returns success, and its complete generated `Copilot.hs` fails GHC type checking. A flight-software CI pipeline must be able to reject that incomplete output without breaking users who deliberately generate editable scaffolding.

## Scope and contract

- Default standalone generation remains permissive, returns success, and writes the same generated source, but emits an actionable warning to stderr listing all unresolved external variable names.
- New boolean `--require-types` CLI option makes `standalone` fail with a nonzero result before copying any generated template if at least one external variable has an empty type after `addMissingIdentifiers`. The error lists names; mapped external types pass.
- Both explicit `type:""` records and identifiers inferred from requirement expressions are subject to the same rule. Deduplicate missing names, preserve input ordering, and do not infer a type from a formula.
- Diagram-only input remains unaffected. The rule applies to the standalone command, not the shared `commandLogic` called by ROS, cFS or F´ backends.
- This is an *external-type completeness check*, not a promise that all Haskell code will compile or that C code can be generated; unknown non-empty types and internal-variable bodies remain separately unverified.

## Approaches and tradeoffs

1. **Chosen: default warning + opt-in fail-closed validation.** Maintains current success contract and provides a CI assurance gate. Introduces a new flag and a warning, but no type guesses.
2. Default error on any missing type: simplest fail-closed semantics but would invalidate FRET's documented optional mapping workflow and existing permissive Ogma fixtures.
3. Enable `PartialTypeSignatures` or infer types: may compile the narrow Boolean case but risks accidental defaults or ambiguity for other external signals; needs a larger type-soundness argument.

## Evidence and acceptance

- Pinned Ogma `08b384b4335cce324fac74577adc7f08e61b7cce`; FRET `cf0f913cc15c41705e803593297e89cd6056b839`.
- [Ogma native generation](https://github.com/metalogiclabs/fret/actions/runs/41241267388) accepts an unmapped FRET JSON and emits `sensor_ok :: Stream (_)`.
- [Full unmodified monitor type-check control](https://github.com/metalogiclabs/fret/actions/runs/41246554279): mapped exit 0, unmapped exit 1 under GHC 9.2.8 / Copilot 4.7.1.
- Default unmapped: success, generated output, warning mentions `sensor_ok`.
- Strict unmapped: nonzero error mentions `sensor_ok`, no generated source copied.
- Strict mapped: success, no unresolved-type warning.
- Existing standalone successful cases keep their default success behavior.

## Non-goals

No upstream PR/contact; no changes to FRET; no automatic type inference; no runtime monitor semantics claim; no global changes to `addMissingIdentifiers` or non-standalone backends.
