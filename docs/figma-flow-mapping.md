# Figma to Glimpse Flow Mapping

This document is the source of truth for mapping Figma screens to the Glimpse React frontend states, UI modes, backend process stages, user actions and transition logic.

It is intended to guide the staged migration from the existing Streamlit frontend to the React + TypeScript frontend in `glimpse/`.

## Global rules

- Do not assume one backend stage equals one React screen.
- Backend `session.stage` and `session.state` represent process state, not visual layout.
- React `App/UI state` controls which main screen is shown.
- `UI mode/substate` represents visual variants, panels, expanded cards, dropdowns, local modes or component states inside a screen.
- API calls belong in `glimpse/src/api/coachClient.ts`.
- Backend response interpretation and screen resolution belong in `glimpse/src/flow/sessionFlow.ts`.
- Pure frontend state updates from backend responses belong in `glimpse/src/flow/sessionState.ts`.
- Individual screen components should not interpret backend stages directly.
- Individual screen components should collect/display user input and pass events upward through props.
- Figma visual variants such as `05a_Discussion_A1`, `05a_Discussion_A2`, `07b_Pathways_extended` and `08b_Survey_dropdown` are UI modes/components, not backend stages.
- Preserve the existing Streamlit behaviour first; improve visual fidelity screen by screen.
- Keep every migration increment small, testable and easy to revert.

## PDF generation rule

The pathways download button should generate a client-side PDF using `jsPDF`.

PDF generation must be isolated from screen components:

- PDF types should live under `glimpse/src/pdf/`
- PDF layout/composition should live under `glimpse/src/pdf/`
- `PathwaysScreen` should only expose an `onDownloadPdf` action
- No backend call is required for PDF generation in the current iteration
- Required PDF content:
  - original problem statement
  - synthesis text
  - pathways

## Backend endpoints currently used by the Streamlit reference frontend

- `GET /session_initialise` creates/initialises a backend session.
- `POST /user_message` sends a user turn with `{ session_id, user_message }`.
- `GET /debug_trace/{session_id}` retrieves debug trace data for development/diagnosis.

## Existing Streamlit stage-to-screen mapping

| Backend `session.stage` | Streamlit/UI screen |
|---|---|
| `classification` | `coaching` |
| `coaching` | `coaching` |
| `synthesis` | `synthesis_review` |
| `pathways` | `pathways` |
| `closure` | `feedback` |
| `unknown/fallback` | `coaching` |

Special case: when backend returns `session.stage == "pathways"` and `session.state == "preparing"` after synthesis refinement, the UI should remain on `synthesis_review` with mode/substate `awaiting_pathways_after_refinement` until the user continues to pathways.

## Summary table

| Figma screen | App/UI state | UI mode/substate | Backend stage/state |
|---|---|---|---|
| 01_Launch | launch | splash_timer | None |
| 02_Welcome | welcome | welcome_intro | None |
| 03_Confidentiality | confidentiality | consent_required | None |
| 04_Information | intro | pre_session_information | None before action. Session created on action. |
| 05a_Discussion_Q1 | problem_input | initial_problem_entry | Session exists, but no user problem has been submitted yet. |
| 05a_Discussion_A1 | problem_input or coaching | message_display_variant | Depends on surrounding conversation state. |
| 05a_Discussion_Q2 | coaching | active_discussion_input | classification or coaching |
| 05a_Discussion_A2 | coaching | coach_reply_display_variant | classification or coaching |
| 06a_Problem statement | synthesis_review | review_synthesis | synthesis |
| 06b_Problem statement_refinement | synthesis_review | refinement_open or awaiting_pathways_after_refinement | Usually synthesis; special case can be pathways + preparing. |
| 07a_Pathways_options | pathways | cards_collapsed | pathways |
| 07b_Pathways_extended | pathways | expanded_pathway | pathways |
| 08a_Survey | feedback | survey | closure |
| 08b_Survey_dropdown | feedback | dropdown_open | closure |
| 09_Close | closed | final | Session complete or locally closed. |
| No direct Figma equivalent yet | pathways_review | read_only_cached_pathways | Usually none; uses cached frontend pathways text. |

## Full mapping table

| Figma screen | App/UI state | UI mode/substate | Backend stage/state | Backend call / actions | Next screen logic | Notes and risks |
|---|---|---|---|---|---|---|
| 01_Launch | launch | splash_timer | None | No backend call. Pure local UI. | Auto-advance to welcome, or move on via local timer/action depending on Figma behaviour. | New React-only state. Streamlit did not have this separate screen. Keep isolated as an onboarding screen. No session should exist yet. |
| 02_Welcome | welcome | welcome_intro | None | No backend call. Pure local UI. | Move locally to confidentiality. | Equivalent to Streamlit welcome, but React may have richer visual treatment. Do not initialise backend here. |
| 03_Confidentiality | confidentiality | consent_required | None | No backend call. User must tick/confirm consent before continuing. | If consent confirmed, move locally to intro. | Same behavioural role as Streamlit confidentiality screen. Button should remain disabled until consent is confirmed. |
| 04_Information | intro | pre_session_information | None before action. Session created on action. | On primary action, call GET /session_initialise. Store returned session_id and initial session data. | If session initialisation succeeds, move to problem_input. If it fails, remain on intro and show recoverable error. | This is the first backend interaction. Keep loading and error state explicit. Do not let user proceed to problem input without a valid session. |
| 05a_Discussion_Q1 | problem_input | initial_problem_entry | Session exists, but no user problem has been submitted yet. | On Continue, call POST /user_message with { session_id, user_message }. | Use the shared React flow helper to resolve next screen from backend response. Usually this will go to coaching, but do not hard-code it in the screen. | This is the first real conversation input. This screen should not decide whether the problem is valid. Backend owns classification. |
| 05a_Discussion_A1 | problem_input or coaching | message_display_variant | Depends on surrounding conversation state. | No separate backend call. This is a visual/component variant only. | No direct screen transition. It should be rendered as part of the discussion layout if needed. | Do not implement as a standalone route/page unless the Figma design truly requires it. Treat as a reusable message/card component. |
| 05a_Discussion_Q2 | coaching | active_discussion_input | classification or coaching | On Continue, call POST /user_message with { session_id, user_message }. | Use flow helper to resolve next screen from backend response. Possible outcomes: remain coaching, move to synthesis_review, move to feedback if closure occurs, or fallback to coaching. | Streamlit mapped both classification and coaching backend stages to the same visible coaching screen. Preserve that idea. |
| 05a_Discussion_A2 | coaching | coach_reply_display_variant | classification or coaching | No separate backend call. This displays the backend coach_message. | No direct transition. User action comes from the associated input screen/component. | Treat as part of the discussion screen, not as a separate app state. Useful as a reusable CoachMessage or DiscussionMessage component. |
| 06a_Problem statement | synthesis_review | review_synthesis | synthesis | User can accept or request refinement. Accept action sends yes via POST /user_message. Refinement opens 06b locally before submitting. | If user accepts, use backend response to resolve next screen, usually pathways. If user chooses refinement, stay in synthesis_review with substate refinement_open. | This is not a solution stage. It is a validation gate. Do not generate pathways locally. Backend owns the transition. |
| 06b_Problem statement_refinement | synthesis_review | refinement_open or awaiting_pathways_after_refinement | Usually synthesis; special case can be pathways + preparing. | Submit refinement text via POST /user_message. After backend applies refinement, if backend returns stage=pathways and state=preparing, keep user on synthesis review and show “continue to pathways” behaviour. | Do not jump directly to pathways after refinement submission unless the flow helper resolves it. In the special pathways/preparing case, stay on synthesis_review until user continues. | This is the most delicate transition. It must preserve the Streamlit behaviour where refined synthesis is reviewed before pathways are shown. |
| 07a_Pathways_options | pathways | cards_collapsed | pathways | User can expand a pathway, choose a pathway, type a pathway choice, or continue. Selection sends pathway_selected:<title> or pathway_selected:<typed text> via POST /user_message. Continue sends continue. | Use backend response to resolve next screen. Usually moves to feedback when backend reaches closure, otherwise may remain on pathways. | Pathways should preferably come from parsed/structured pathway data. For now, preserve compatibility with Markdown heading parsing if backend only returns coach_message. |
| 07b_Pathways_extended | pathways | expanded_pathway | pathways | No backend call merely to expand/collapse. Backend call only if user chooses the pathway or continues. | Closing the expanded card returns to pathways with cards_collapsed. Choosing pathway sends selection and then resolves next screen from backend response. | This is a substate of pathways, not pathways_review. Do not model it as a separate process stage. |
| 08a_Survey | feedback | survey | closure | Local survey interactions only unless you later add feedback submission endpoint. Close action is local for now. Optional “review pathways” action moves locally to pathways_review if supported. | Close moves to closed. Review pathways moves to pathways_review. | Streamlit feedback screen displayed closure message plus survey questions. Preserve behaviour before adding analytics or persistence. |
| 08b_Survey_dropdown | feedback | dropdown_open | closure | No backend call. Pure local UI interaction for survey multi-select/dropdown. | Closing dropdown returns to feedback / survey substate. | This is a UI substate only. Do not create a separate route or backend state for it. |
| 09_Close | closed | final | Session complete or locally closed. | No backend call unless a future explicit close-session endpoint is added. | Terminal UI state. User may leave page. | Equivalent to Streamlit closed. Keep simple. Do not reset session automatically unless explicitly designed. |
| No direct Figma equivalent yet | pathways_review | read_only_cached_pathways | Usually none; uses cached frontend pathways text. | No backend call. Uses cached pathways from previous pathways response. | Return to feedback. | Streamlit had this as a convenience screen from feedback. If Figma has no direct design, either create a simple React version later or omit deliberately. Do not confuse this with 07b_Pathways_extended. |

## Screen details

### 01_Launch

- **Figma screen:** `01_Launch`
- **App/UI state:** `launch`
- **UI mode/substate:** `splash_timer`
- **Backend stage/state:** None
- **Backend call / actions:** No backend call. Pure local UI.
- **Next screen logic:** Auto-advance to welcome, or move on via local timer/action depending on Figma behaviour.
- **Notes and risks:** New React-only state. Streamlit did not have this separate screen. Keep isolated as an onboarding screen. No session should exist yet.

### 02_Welcome

- **Figma screen:** `02_Welcome`
- **App/UI state:** `welcome`
- **UI mode/substate:** `welcome_intro`
- **Backend stage/state:** None
- **Backend call / actions:** No backend call. Pure local UI.
- **Next screen logic:** Move locally to confidentiality.
- **Notes and risks:** Equivalent to Streamlit welcome, but React may have richer visual treatment. Do not initialise backend here.

### 03_Confidentiality

- **Figma screen:** `03_Confidentiality`
- **App/UI state:** `confidentiality`
- **UI mode/substate:** `consent_required`
- **Backend stage/state:** None
- **Backend call / actions:** No backend call. User must tick/confirm consent before continuing.
- **Next screen logic:** If consent confirmed, move locally to intro.
- **Notes and risks:** Same behavioural role as Streamlit confidentiality screen. Button should remain disabled until consent is confirmed.

### 04_Information

- **Figma screen:** `04_Information`
- **App/UI state:** `intro`
- **UI mode/substate:** `pre_session_information`
- **Backend stage/state:** None before action. Session created on action.
- **Backend call / actions:** On primary action, call GET /session_initialise. Store returned session_id and initial session data.
- **Next screen logic:** If session initialisation succeeds, move to problem_input. If it fails, remain on intro and show recoverable error.
- **Notes and risks:** This is the first backend interaction. Keep loading and error state explicit. Do not let user proceed to problem input without a valid session.

### 05a_Discussion_Q1

- **Figma screen:** `05a_Discussion_Q1`
- **App/UI state:** `problem_input`
- **UI mode/substate:** `initial_problem_entry`
- **Backend stage/state:** Session exists, but no user problem has been submitted yet.
- **Backend call / actions:** On Continue, call POST /user_message with { session_id, user_message }.
- **Next screen logic:** Use the shared React flow helper to resolve next screen from backend response. Usually this will go to coaching, but do not hard-code it in the screen.
- **Notes and risks:** This is the first real conversation input. This screen should not decide whether the problem is valid. Backend owns classification.

### 05a_Discussion_A1

- **Figma screen:** `05a_Discussion_A1`
- **App/UI state:** `problem_input or coaching`
- **UI mode/substate:** `message_display_variant`
- **Backend stage/state:** Depends on surrounding conversation state.
- **Backend call / actions:** No separate backend call. This is a visual/component variant only.
- **Next screen logic:** No direct screen transition. It should be rendered as part of the discussion layout if needed.
- **Notes and risks:** Do not implement as a standalone route/page unless the Figma design truly requires it. Treat as a reusable message/card component.

### 05a_Discussion_Q2

- **Figma screen:** `05a_Discussion_Q2`
- **App/UI state:** `coaching`
- **UI mode/substate:** `active_discussion_input`
- **Backend stage/state:** classification or coaching
- **Backend call / actions:** On Continue, call POST /user_message with { session_id, user_message }.
- **Next screen logic:** Use flow helper to resolve next screen from backend response. Possible outcomes: remain coaching, move to synthesis_review, move to feedback if closure occurs, or fallback to coaching.
- **Notes and risks:** Streamlit mapped both classification and coaching backend stages to the same visible coaching screen. Preserve that idea.

### 05a_Discussion_A2

- **Figma screen:** `05a_Discussion_A2`
- **App/UI state:** `coaching`
- **UI mode/substate:** `coach_reply_display_variant`
- **Backend stage/state:** classification or coaching
- **Backend call / actions:** No separate backend call. This displays the backend coach_message.
- **Next screen logic:** No direct transition. User action comes from the associated input screen/component.
- **Notes and risks:** Treat as part of the discussion screen, not as a separate app state. Useful as a reusable CoachMessage or DiscussionMessage component.

### 06a_Problem statement

- **Figma screen:** `06a_Problem statement`
- **App/UI state:** `synthesis_review`
- **UI mode/substate:** `review_synthesis`
- **Backend stage/state:** synthesis
- **Backend call / actions:** User can accept or request refinement. Accept action sends yes via POST /user_message. Refinement opens 06b locally before submitting.
- **Next screen logic:** If user accepts, use backend response to resolve next screen, usually pathways. If user chooses refinement, stay in synthesis_review with substate refinement_open.
- **Notes and risks:** This is not a solution stage. It is a validation gate. Do not generate pathways locally. Backend owns the transition.

### 06b_Problem statement_refinement

- **Figma screen:** `06b_Problem statement_refinement`
- **App/UI state:** `synthesis_review`
- **UI mode/substate:** `refinement_open or awaiting_pathways_after_refinement`
- **Backend stage/state:** Usually synthesis; special case can be pathways + preparing.
- **Backend call / actions:** Submit refinement text via POST /user_message. After backend applies refinement, if backend returns stage=pathways and state=preparing, keep user on synthesis review and show “continue to pathways” behaviour.
- **Next screen logic:** Do not jump directly to pathways after refinement submission unless the flow helper resolves it. In the special pathways/preparing case, stay on synthesis_review until user continues.
- **Notes and risks:** This is the most delicate transition. It must preserve the Streamlit behaviour where refined synthesis is reviewed before pathways are shown.

### 07a_Pathways_options

- Figma screen: `07a_Pathways_options`
- App/UI state: `pathways`
- UI mode/substate: `cards_collapsed`
- Backend stage/state: `pathways`
- Backend call/action:
  - User presses `Continue` to move to the next stage.
  - Send `continue` via `POST /user_message`.
  - The `+` button expands a pathway locally only.
  - The download button generates a client-side PDF using `jsPDF`.
  - No backend call is required for PDF generation in the current iteration.
- Next screen logic:
  - After `continue`, apply backend response using existing session helpers.
  - Resolve next screen using `sessionFlow`.
  - PDF download does not change screen state.
- Notes/risks:
  - Do not implement pathway selection.
  - Do not send `pathway_selected:<title>`.
  - Expanding a pathway is local UI state only and must not call the backend.
  - PDF generation must be isolated under `glimpse/src/pdf/`.
  - PDF layout/composition must not live inside `PathwaysScreen`.
  - The React app must retain problem statement, synthesis, and pathways text in session/app state so the PDF can be generated without backend interaction.

### 07a_Pathways_expanded

- Figma screen: `07a_Pathways_expanded`
- App/UI state: `pathways`
- UI mode/substate: `expanded_pathway`
- Backend stage/state: `pathways`
- Backend call/action:
  - No backend call.
  - User presses `X` to close and return to `07a_Pathways_options`.
- Next screen logic:
  - Closing returns locally to `pathways` with `cards_collapsed`.
- Notes/risks:
  - This is not a separate backend stage.
  - This is not a pathway review screen.
  - This is just an expanded local reading view for one pathway.

### 08a_Survey

- **Figma screen:** `08a_Survey`
- **App/UI state:** `feedback`
- **UI mode/substate:** `survey`
- **Backend stage/state:** closure
- **Backend call / actions:** Local survey interactions only unless you later add feedback submission endpoint. Close action is local for now. Optional “review pathways” action moves locally to pathways_review if supported.
- **Next screen logic:** Close moves to closed. Review pathways moves to pathways_review.
- **Notes and risks:** Streamlit feedback screen displayed closure message plus survey questions. Preserve behaviour before adding analytics or persistence.

### 08b_Survey_dropdown

- **Figma screen:** `08b_Survey_dropdown`
- **App/UI state:** `feedback`
- **UI mode/substate:** `dropdown_open`
- **Backend stage/state:** closure
- **Backend call / actions:** No backend call. Pure local UI interaction for survey multi-select/dropdown.
- **Next screen logic:** Closing dropdown returns to feedback / survey substate.
- **Notes and risks:** This is a UI substate only. Do not create a separate route or backend state for it.

### 09_Close

- **Figma screen:** `09_Close`
- **App/UI state:** `closed`
- **UI mode/substate:** `final`
- **Backend stage/state:** Session complete or locally closed.
- **Backend call / actions:** No backend call unless a future explicit close-session endpoint is added.
- **Next screen logic:** Terminal UI state. User may leave page.
- **Notes and risks:** Equivalent to Streamlit closed. Keep simple. Do not reset session automatically unless explicitly designed.

### No direct Figma equivalent yet

- **Figma screen:** `No direct Figma equivalent yet`
- **App/UI state:** `pathways_review`
- **UI mode/substate:** `read_only_cached_pathways`
- **Backend stage/state:** Usually none; uses cached frontend pathways text.
- **Backend call / actions:** No backend call. Uses cached pathways from previous pathways response.
- **Next screen logic:** Return to feedback.
- **Notes and risks:** Streamlit had this as a convenience screen from feedback. If Figma has no direct design, either create a simple React version later or omit deliberately. Do not confuse this with 07b_Pathways_extended.

## Recommended React module boundaries

```text
glimpse/src/types/
  session.ts              backend/session response types
  screens.ts              App/UI state and UI mode types

glimpse/src/flow/
  sessionFlow.ts          backend stage/state → app screen resolution
  sessionState.ts         pure frontend state updates from backend responses

glimpse/src/api/
  coachClient.ts          GET /session_initialise, POST /user_message, GET /debug_trace/{session_id}

glimpse/src/screens/
  LaunchScreen.tsx
  WelcomeScreen.tsx
  ConfidentialityScreen.tsx
  InformationScreen.tsx
  ProblemInputScreen.tsx
  DiscussionScreen.tsx
  SynthesisReviewScreen.tsx
  PathwaysScreen.tsx
  FeedbackScreen.tsx
  ClosedScreen.tsx

glimpse/src/components/
  discussion/
  onboarding/
  synthesis/
  pathways/
  feedback/
  shared/
```

## Implementation guidance for Codex

1. Implement one screen or one flow module at a time.
2. Do not perform a full migration in one pass.
3. Keep screen components presentational where possible.
4. Keep backend calls in `coachClient.ts` only.
5. Keep backend response interpretation in `sessionFlow.ts` / `sessionState.ts` only.
6. Keep user-visible behaviour aligned with the Streamlit reference implementation.
7. Run `npm run build` and frontend tests after each React increment.
8. Do not modify backend or Streamlit files unless the task explicitly asks for it.
9. When implementing a Figma screen, use this document as the mapping reference and the Figma node as the visual reference.
10. If a Figma screen is a visual variant or substate, do not create a separate process stage for it.
