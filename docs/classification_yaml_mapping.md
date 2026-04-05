# Classification YAML Mapping

This document explains how [`/Users/lucadematteis/coachV3/backend/config/classification.yaml`](/Users/lucadematteis/coachV3/backend/config/classification.yaml) relates to the uploaded template [`/Users/lucadematteis/Downloads/stage_modules_template_v3.yaml`](/Users/lucadematteis/Downloads/stage_modules_template_v3.yaml), while remaining compatible with the current engine in [`/Users/lucadematteis/coachV3/backend/engine.py`](/Users/lucadematteis/coachV3/backend/engine.py).

## Goal

The current project file is now intentionally a hybrid:

- template-aligned sections are present so the next engine rewrite can consume a richer schema
- current-engine compatibility keys are still present so nothing breaks now

## Current Engine Contract

Today, the engine reads only these root-level keys from [`/Users/lucadematteis/coachV3/backend/config/classification.yaml`](/Users/lucadematteis/coachV3/backend/config/classification.yaml):

- `prompt`
- `state_instructions`
- `criteria`
- `heuristics`
- `outputs`

Everything else in the YAML is currently ignored by code, but retained intentionally for the next engine step.

## Template Alignment

Because this is a stage-specific file, the template's `stages.classification.*` content is flattened to the root of [`/Users/lucadematteis/coachV3/backend/config/classification.yaml`](/Users/lucadematteis/coachV3/backend/config/classification.yaml) instead of being nested under `stages.classification`.

That means the current file keeps the template's concepts, but not the exact outer wrapper.

## Mapping Table

| Uploaded template path | Current classification.yaml path | Consumed by current engine | Notes |
| --- | --- | --- | --- |
| `version` | `version` | No | Preserved directly for future schema/versioning. |
| `meta.description` | `meta.description` | No | Preserved directly. |
| `meta.source_of_truth_note` | `meta.source_of_truth_note` | No | Preserved directly. |
| `shared.llm_defaults` | `shared.llm_defaults` | No | Preserved directly for future engine use. |
| `shared.prompt_build.components_in_order` | `shared.prompt_build.components_in_order` | No | Preserved directly for future prompt assembly logic. |
| `shared.output_contracts.classification_eval` | `shared.output_contracts.classification_eval` | No | Preserved directly; future engine can read this instead of the current prompt shim. |
| `stages.classification.enabled` | `enabled` | No | Flattened because this file is classification-only. |
| `stages.classification.purpose` | `purpose` | No | Flattened and preserved directly. |
| `stages.classification.stage_notes` | `stage_notes` | No | Flattened and preserved directly. |
| `stages.classification.prompt_assets.system_identity` | `prompt_assets.system_identity` | No | Preserved directly. |
| `stages.classification.prompt_assets.stage_purpose` | `prompt_assets.stage_purpose` | No | Preserved directly. |
| `stages.classification.prompt_assets.stage_rules` | `prompt_assets.stage_rules` | No | Preserved directly. |
| `stages.classification.prompt_assets.output_contract_ref` | `prompt_assets.output_contract_ref` | No | Preserved directly. |
| `stages.classification.signals.valid_signals` | `signals.valid_signals` | No | Preserved directly. |
| `stages.classification.signals.ambiguous_signals` | `signals.ambiguous_signals` | No | Preserved directly. |
| `stages.classification.signals.invalid_signals` | `signals.invalid_signals` | No | Preserved directly. |
| `stages.classification.states.evaluating.prompt_context` | `states.evaluating.prompt_context` | No | Preserved directly. |
| `stages.classification.states.evaluating.prompt_hints` | `states.evaluating.prompt_hints` | No | Preserved directly. |
| `stages.classification.states.ambiguous.prompt_context` | `states.ambiguous.prompt_context` | No | Preserved directly. |
| `stages.classification.states.ambiguous.prompt_hints` | `states.ambiguous.prompt_hints` | No | Preserved directly. |
| `stages.classification.states.completed` | `states.completed` | No | Preserved directly. |
| `stages.classification.states.cancelled` | `states.cancelled` | No | Preserved directly. |
| `stages.classification.examples.valid` | `examples.valid` | No | Preserved directly. |
| `stages.classification.examples.ambiguous` | `examples.ambiguous` | No | Preserved directly. |
| `stages.classification.examples.invalid` | `examples.invalid` | No | Preserved directly. |

## Compatibility Shim Mapping

These root keys exist only because the current engine still expects them:

| Current compatibility key | Derived from template-aligned sections | Used now |
| --- | --- | --- |
| `prompt.system` | `prompt_assets.system_identity` + `prompt_assets.stage_purpose` | Yes |
| `prompt.output_schema` | `shared.output_contracts.classification_eval` | Yes |
| `state_instructions.evaluating` | `states.evaluating.prompt_context` + `states.evaluating.prompt_hints` | Yes |
| `state_instructions.ambiguous` | `states.ambiguous.prompt_context` + `states.ambiguous.prompt_hints` | Yes |
| `criteria.valid` | `signals.valid_signals` | Yes |
| `criteria.ambiguous` | `signals.ambiguous_signals` | Yes |
| `criteria.invalid` | `signals.invalid_signals` | Yes |
| `outputs.valid/ambiguous/invalid` | No exact template equivalent | Yes |
| `heuristics` | No exact template equivalent | Yes |

## Intentional Differences

- The uploaded template is a multi-stage file; the project file is classification-only.
- `heuristics` is not part of the uploaded template. It remains because the current engine uses deterministic rules instead of a live LLM.
- `outputs` is also a current-engine convenience section. The uploaded template defines an output contract, but not the exact canned response text used by the current deterministic implementation.

## Recommended Next Engine Step

When rewriting [`/Users/lucadematteis/coachV3/backend/engine.py`](/Users/lucadematteis/coachV3/backend/engine.py), the migration path should be:

1. Read `prompt_assets`, `states`, `signals`, `examples`, and `shared.output_contracts` directly.
2. Treat `prompt`, `state_instructions`, and `criteria` as temporary compatibility keys.
3. Keep `heuristics` only if deterministic fallback remains part of the design.
4. Decide whether `outputs` should remain as reusable copy assets or move into a richer prompt/response policy section.
