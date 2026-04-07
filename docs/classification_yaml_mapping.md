# Classification YAML Mapping

[`/Users/lucadematteis/coachV3/backend/config/classification.yaml`](/Users/lucadematteis/coachV3/backend/config/classification.yaml) now follows the stage YAML format defined by [`/Users/lucadematteis/coachV3/backend/config/stage_template.yaml`](/Users/lucadematteis/coachV3/backend/config/stage_template.yaml).

## Runtime Contract

The refactored engine reads only these top-level sections:

- `experience`
- `stage`
- `states`

`description` fields are ignored during prompt assembly and exist only for maintainers.

## Prompt Assembly

Evaluation prompts are assembled in this exact order:

1. `experience.prompt_preamble`
2. `experience.role`
3. `experience.global_rules`
4. `experience.shared_output_rules`
5. `experience.evaluation`
6. `stage.prompt_preamble`
7. `stage.purpose`
8. `stage.rules`
9. `stage.shared_output_rules`
10. `stage.evaluation`
11. `states.<current_state>.prompt_preamble`
12. `states.<current_state>.purpose`
13. `states.<current_state>.rules`
14. `states.<current_state>.shared_output_rules`
15. `states.<current_state>.evaluation`

Coaching prompts use the same order, but use `coaching` instead of `evaluation` in the experience, stage, and state sections.

## Runtime Payload

Conversation history, context payload, latest user message, and optional output instructions are appended after the YAML prompt text. They are not part of the fixed YAML assembly order.

## Removed Old Assumptions

The previous hybrid compatibility keys are no longer part of `classification.yaml`:

- `prompt`
- `state_instructions`
- `criteria`
- `heuristics`
- `outputs`

The engine no longer depends on that old YAML structure.
