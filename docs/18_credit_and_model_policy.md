# 18. Credit and model policy

This file distinguishes captured event offers from verified account balances. No credit receipt,
card authorization, subscription purchase or account change was performed in this revision.

| Service | Captured offer | What not to assume |
|---|---|---|
| Meta Model API | $150 per accepted participant, own account, one claim | Not cash, not automatically credited, not all other services |
| Modal | $100, first 1,000 per guide, partner discretion | Not Meta API credit; confirm ESM workload eligibility |
| Baseten | $100, up to 2,000 selected individuals, use-case review | Not a transferable GPU budget |
| Fireworks | $25 for selected teams | Not guaranteed to every participant |

The claim form supplied by the user states distribution within two business days. The guide says
batch distribution and valid payment method for API use. A submitted form is not a balance receipt.
A failed card authorization is a separate issue. The billing page's Spend Limit wording is an email
notification, not an automatic stop; do not equate a $150 alert with a zero-overspend guarantee [S21,S24].

Separate ledgers: hosted Meta API, Muse Code subscription/allowance, ESM GPU, partner inference,
storage and third-party coding tools. Confirm current prices and account-specific credit eligibility.
Do not auto-purchase, retry failed payment, change card settings or move funds.

Default app ceiling is a proposal, not permission: 2 USD per run, 12 Meta requests, 900 GPU seconds,
one concurrent job, zero new folds. Provider billing can lag and in-flight charges can exceed a
local estimate; account controls plus bounded jobs are still needed. Use actual/estimated/unknown
cost labels. Stop new calls before exhausted approved funds; do not silently switch providers.

Develop with fixtures and stored real responses where appropriate, but final integration evidence
must include actual Meta calls. Codex/Claude Code can help build under their own terms and budgets;
confirm event allowance when ambiguous. Their use does not replace meaningful Meta runtime use.

ESM runs outside the Meta API catalog, with separate compute costs. Atlas/PDB are separate evidence
sources with their own terms. The guide's open-weight bonus specifically names Muse Glimmer or
Muse Spark Open; ESM alone is not a confirmed qualifier. An alternative eligible runtime is P1,
not a reason to expand scope or charge an account without approval.
