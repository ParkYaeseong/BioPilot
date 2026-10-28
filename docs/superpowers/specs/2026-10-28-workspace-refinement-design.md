# Workspace refinement

User request: repair Light theme after the latest Claude changes, replace the
explanatory tour with an acting walkthrough, improve layout, order file input
before inspection, connect replay and live chat, and implement the previously
planned optional science integrations where the verified runtime permits.

## Chosen approach

Retain Streamlit and the existing isolated entry points. A shared shell links
Saved review (8520) and Live session (8521), retaining appearance in navigation.
This gives one workspace experience while the saved viewer's import graph still
has no dispatch capability. A single process with paid capabilities would weaken
that property; a framework rewrite is outside the project's local viewer scope.
The user has delegated routine design choices and requested implementation.

Use a compact header and ordered Input, Candidates, Structure, Meta trace,
Evidence steps. Uploads are optional diagnostics inside Input; they do not
replace the registered target or silently change the saved run. Reveal raw
technical details on demand. Use restrained neutral surfaces, consistent type,
one semantic accent and actual theme tokens for every native widget and iframe.
References: Vercel Geist and Linear official product pages; original local code,
no copied assets. Use semantic tables so the native dark canvas cannot survive
an application Light selection.

The tour changes actual local checks, shortlist, structure focus and recorded
trace state. It supports timed play, pause, back, next, restart and exit/restore.
It is explicitly an offline REPLAY walkthrough. No live flags, run arming,
provider requests, fabricated computation or fabricated progress.

Structure remains the actual 1ISP reference. Full 32 is unmodelled and must never
highlight author 32. Theme, fit and rotate controls affect presentation only.
Optional ESM3/ESMFold2/Atlas evidence stays separate from the shared ESM2 rank.
Adapters require verified model/runtime/source pins; unavailable configurations
remain unavailable. BOP connection is inspected only after the user supplied it.
No credentials, server address or private runtime state enters public package.

## Verification

Failing behavior tests before implementation, focused AppTests, actual Light/Dark
browser inspection of controls, chat and iframe, timed tour observation, full
regression and package checks. Preserve existing changes, evidence and recordings.
Update STATUS and DECISIONS with what ran and what remains unverified.
