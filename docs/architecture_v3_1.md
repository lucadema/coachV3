# POC v3.1 — Source-of-Truth Design Spec

## 1. Core design principles

### 1.1 Session is the single source of truth

There is no separate stage handoff artifact model.

Stages do not pass artifacts to each other. Each stage reads what it needs from the session.

### 1.2 Evaluation only evaluates

Evaluation is internal only.

It may:

- assess the current input
- update internal assessment fields
- update flags, counters, or scores
- decide state transition
- decide completion or cancellation

It does not generate user-facing text.

### 1.3 Coaching is the only text-generation step

All user-visible generated text is produced by coaching through `coach_message`.

This includes:

- questions
- clarification prompts
- redirect/cancel explanations
- synthesis text
- pathways text
- closure text

### 1.4 State transitions are state-driven

A transition that requires judgement must go through evaluation. A deterministic transition does not require evaluation.

### 1.5 Not every state uses both engine steps

Each state declares one behavioural type:

- evaluative
- production
- waiting
- terminal

### 1.6 Stages read directly from current session fields

This corrects the earlier misconception.

- Coaching can read not only message history and evaluation results, but also the current `user_message` directly.
- Pathways does not need a separate synthesis artifact; it can read the synthesis from the latest relevant `coach_message`, which is also present in session history.
- In Pathways presenting, UI feedback is injected through `user_message` as a pre-determined flag/value, and the stage interprets that directly.

## 2. Revised stage map

### 2.1 Classification

#### Purpose

Validate whether the opening user input belongs in this flow.

#### Entry

Starts with:

- `user_message` containing the user’s first message

#### Reads from session

- `user_message`
- message history if needed
- counters / flags

#### Writes to session

- `evaluation_message`
- `coach_message` if clarification, redirect, or explanation is needed
- `state`
- `completed`
- `canceled`

#### Ends when

- problem is validated and stage completes, or
- session is canceled / redirected

### 2.2 Coaching

#### Purpose

Guide the user through the exploration loop until the problem is sufficiently defined.

#### Entry

Starts after Classification completes.

#### Reads from session

- current `user_message`
- message history
- latest `evaluation_message`
- stage flags / counters

This corrects the earlier wording: Coaching does not rely only on session history. It may also read the current `user_message` directly.

#### Writes to session

- `evaluation_message`
- `coach_message`
- `state`
- `completed`
- `canceled`

#### Ends when

- readiness for Synthesis is reached, or
- session is canceled

### 2.3 Synthesis

#### Purpose

Produce the synthesis from the accumulated context.

#### Entry

Starts with no special artifact. It reads directly from the session.

#### Reads from session

- message history
- latest relevant coaching/evaluation context
- counters / flags

#### Writes to session

- `coach_message` containing the synthesis
- `state`
- `completed`
- `canceled`

#### Ends when

- synthesis is accepted, or
- synthesis is refined once and then finalized, or
- session is canceled

### 2.4 Pathways

#### Purpose

Generate pathways from the validated synthesis and capture user selection feedback.

#### Entry

Starts after Synthesis completes.

#### Reads from session

- latest relevant `coach_message` containing the synthesis
- message history
- current `user_message`

This corrects the earlier wording: Pathways does not need a passed synthesis artifact. It can read the synthesis from the last synthesis `coach_message`, which is already part of the session.

#### Writes to session

- `coach_message` containing the pathways
- `state`
- `completed`
- `canceled`

#### User feedback

After pathways are presented, the UI asks for selection feedback and injects a pre-determined flag/value into `user_message`.

That UI-injected value is the input used by the stage to interpret the user’s selection.

#### Ends when

- pathways are presented and user feedback is captured, or
- session is canceled

### 2.5 Closure

#### Purpose

Close the session with a final message.

#### Entry

Starts after Pathways completes.

#### Reads from session

- message history
- latest relevant `user_message`
- latest relevant `coach_message`

#### Writes to session

- `coach_message` containing the closing text
- `state`
- `completed`

#### Ends when

- final closing message is produced

## 3. State-type matrix

### 3.1 Classification

- `evaluating` → evaluative
- `ambiguous` → waiting, then returns to evaluative when new `user_message` arrives
- `completed` → terminal
- `canceled` → terminal

### 3.2 Coaching

- `guiding` → evaluative
- `completed` → terminal
- `canceled` → terminal

### 3.3 Synthesis

- `preparing` → production
- `validating` → waiting
- `refining` → production
- `completed` → terminal
- `canceled` → terminal

### 3.4 Pathways

- `preparing` → production
- `presenting` → waiting
- `completed` → terminal
- `canceled` → terminal

### 3.5 Closure

- `preparing` → production
- `completed` → terminal

## 4. State execution rules by stage

### 4.1 Classification

#### `evaluating`

Runs:

- evaluation required
- coaching optional after evaluation

Evaluation decides:

- valid → completed
- ambiguous → ambiguous
- invalid / distress / abort → canceled

Coaching may then:

- ask a clarification question
- explain redirect/cancel
- optionally emit a brief transition message

#### `ambiguous`

Waits for a new `user_message`.

When the next user input arrives:

- return to evaluation
- decide completed or canceled

### 4.2 Coaching

#### `guiding`

Runs:

- evaluation usually required
- coaching optional after evaluation

Evaluation decides:

- remain guiding
- move to completed
- move to canceled

Coaching may then:

- ask the next question
- explain cancellation
- optionally emit a transition message

### 4.3 Synthesis

#### `preparing`

Runs:

- no evaluation
- coaching directly

Coaching generates the synthesis in `coach_message`.

Then:

- `preparing -> validating`

#### `validating`

Waits for `user_message`.

No evaluation is required.

User input causes deterministic transition:

- validate / accept → completed
- comment → refining
- cancel / abort → canceled

#### `refining`

Runs:

- no evaluation
- coaching directly

Coaching regenerates the synthesis using the user’s comment.

Then:

- `refining -> completed`

No second validation cycle is required.

### 4.4 Pathways

#### `preparing`

Runs:

- no evaluation
- coaching directly

Coaching generates the pathways in `coach_message`.

Then:

- `preparing -> presenting`

#### `presenting`

Waits for `user_message`.

No evaluation is required.

`user_message` may contain:

- plain user feedback text, or
- a UI-injected pre-determined selection flag/value

Transition is deterministic:

- valid selection / acknowledgement / continue → completed
- cancel / abort → canceled

### 4.5 Closure

#### `preparing`

Runs:

- no evaluation
- coaching directly

Coaching generates the closing text in `coach_message`.

Then:

- `preparing -> completed`

## 5. Controller rules

The controller owns macro-stage routing and state dispatch.

For each turn:

1. Read current `stage` and `state` from session.
2. Load the corresponding stage module.
3. Determine the current state type:
   - evaluative
   - production
   - waiting
   - terminal
4. Execute according to state type.

### 5.1 Evaluative state

The controller:

- calls `evaluate(...)`
- stores the result in `evaluation_message`
- applies any state/flag/counter changes
- if the resulting state requires a user-facing message, calls `coach(...)`
- stores the result in `coach_message`

Typical stages:

- Classification evaluating
- Coaching guiding

### 5.2 Production state

The controller:

- skips evaluation
- calls `coach(...)` directly
- stores the result in `coach_message`
- applies the deterministic next state

Typical stages:

- Synthesis preparing
- Synthesis refining
- Pathways preparing
- Closure preparing

### 5.3 Waiting state

The controller:

- does not call evaluation or coaching immediately
- waits for new `user_message`
- when input arrives, applies deterministic transition or re-enters evaluative flow if that state requires it

Typical states:

- Classification ambiguous
- Synthesis validating
- Pathways presenting

### 5.4 Terminal state

The controller:

- performs no engine call
- either advances to the next stage or ends the session

## 6. Engine contract

The engine exposes only two capabilities:

### 6.1 `evaluate(...)`

#### Purpose

Assess the current input and current state.

It may return/update:

- `evaluation_message`
- transition decision
- flags
- counters
- completion/cancel status

It does not produce user-facing text.

### 6.2 `coach(...)`

#### Purpose

Generate the next user-facing output.

It may return/update:

- `coach_message`

It does not itself decide judgement-based transitions unless the transition is deterministic and owned by the stage logic around the call.

## 7. Stage-module contract

Each stage module is responsible for:

- defining its states
- declaring each state type
- deciding whether evaluation is required
- deciding whether coaching is required
- defining deterministic transitions
- reading the correct session fields for each state

Each stage module must therefore answer:

- what state am I in?
- what state type is this?
- what session fields do I need?
- do I call evaluation?
- do I call coaching?
- what transition follows?

## 8. Session field roles

These are the formal roles of the existing session fields.

### 8.1 `user_message`

The current turn input.

It may contain:

- normal free-text input from the user
- a UI-injected pre-determined flag/value
- a structured selection signal encoded through the UI

Used by:

- Classification
- Coaching
- Synthesis validation
- Pathways selection
- Closure if needed

### 8.2 `evaluation_message`

The evaluator’s internal assessment output for the current turn.

Examples of use:

- classification result
- readiness result
- cancel reason
- assessment flags
- internal transition rationale

It is not a handoff artifact and not a user-visible response.

### 8.3 `coach_message`

The current turn’s user-facing generated output.

Examples:

- question
- clarification prompt
- redirect explanation
- cancel explanation
- synthesis
- pathways
- closure

The latest relevant synthesis is found here after Synthesis produces it. The latest relevant pathways are found here after Pathways produces them.

### 8.4 Message history

The durable conversation record.

Used by all later stages for context reconstruction. This includes prior `user_message` and `coach_message` content over time.

### 8.5 `stage`

Current macro-stage:

- classification
- coaching
- synthesis
- pathways
- closure

### 8.6 `state`

Current local state inside the active stage.

### 8.7 `completed`

Indicates that the current stage, or the full flow if applicable, is complete.

### 8.8 `canceled`

Indicates that the current stage or session has been canceled.

### 8.9 `turn_count`

Recommended addition.

Purpose:

- total turn count in the session

### 8.10 `stage_turn_count`

Recommended addition.

Purpose:

- turn count within the current stage

These two counters are the only additions recommended at this stage.

## 9. Final simplified flow

### Classification

- reads current `user_message`
- evaluates validity
- may emit clarification or redirect through `coach_message`

### Coaching

- reads current `user_message`, message history, and latest `evaluation_message`
- evaluates progress
- may emit the next coaching question through `coach_message`

### Synthesis

- reads session context directly
- generates synthesis through `coach_message`
- waits for user validation/comment in `user_message`

### Pathways

- reads the synthesis from the latest relevant `coach_message`
- generates pathways through `coach_message`
- waits for UI/user selection in `user_message`

### Closure

- reads session context directly
- generates final closing text through `coach_message`

## 10. Bottom-line model

The clean v3.1 model is now:

- session is the only persistent carrier
- evaluation only assesses
- coaching only generates user-facing text
- states determine whether evaluation, coaching, both, or neither are required
- later stages read what they need directly from session fields
- `user_message` can also carry UI-injected control/selection flags
- `coach_message` is the user-visible output, including synthesis and pathways
