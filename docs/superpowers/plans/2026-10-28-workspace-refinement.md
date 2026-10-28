# Workspace refinement implementation plan

**Goal:** Readable themes and an acting, ordered scientific review workspace.
**Architecture:** Two isolated Streamlit entry points, one shared visual shell;
pure walkthrough state, native timer, local reference structure, optional science
workers kept outside the viewer's import graph.
**Spec:** ../specs/2026-10-28-workspace-refinement-design.md

1. Reproduce Light failures in installed React Aria widgets; write failing theme
   and workflow tests. Fix complete theme tokens and semantic tables.
2. Test and implement pure guided_tour state transitions; integrate timer and
   compact controls before widget construction, preserving prior inputs on exit.
3. Put local validation and optional sequence/coordinate files in Input. Order
   the navigation and add previous/next actions. Connect replay/chat through a
   shared shell without importing the live runner into replay.
4. Apply the same appearance to chat and the self-contained structure document;
   test no guessed selections and verify fit/rotate controls in the browser.
5. Verify official ESM3/ESMFold2/Atlas APIs and local/remote runtime readiness;
   implement bounded optional adapters with SDK-boundary tests. Do not represent
   mocked execution as real inference. Keep ranking unchanged.
6. Run focused and regression checks; inspect desktop/narrow Light/Dark and
   automatic tour behavior, update source manifest and milestone records.

Review focus: incomplete replay traces, user state restored on exit, timer/widget
ordering, dark native canvases, unmodelled A32, paid mode never armed by a tour,
and optional workers requiring pins rather than guessing SDK/model identities.
