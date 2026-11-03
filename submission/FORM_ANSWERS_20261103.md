# Final submission answers — BioPilot Bench

These final copy-ready answers follow the actual field names supplied by the owner. Objective project
claims are supported by the repository. Survey selections are suggestions for the
owner to accept or change, not measured facts or recorded personal opinions.
No form has been submitted by this document.

## Team Name

BioPilot Bench

## Team Members

Keep the owner's existing participant account. Solo entrant: Yaeseong Park.
Codex and Claude are development tools, not human team members.

## Which track are you submitting to?

Indie Developer

## Which problem statement did you build towards?

Push the Frontier

## Most Viral Track — X post link

Leave blank unless entering that award with an actual published X post.

## Project Description

BioPilot Bench turns a protein-variant request into an inspectable scientific review.
Researchers upload a registered public Lipase A FASTA, describe a variant, validate
the input, explicitly approve a bounded run, and inspect candidates, structure,
tool calls and evidence in one local workbench. Meta selects permitted MCP tools
and explains the result; code enforces residue numbering, protected catalytic
sites, execution limits and a common ranking policy. Local ESM-2 scores all 19
non-WT alternatives at an approved position. Researchers can also inspect a public
experimental reference, real stored ESMFold2 WT and ESM3 A32V predictions from
separate L40S GPU runs, and an exact-reference Atlas database snapshot. These
optional evidence views preserve the scoring policy and identify their sources.
The event contribution is this guarded workflow and review interface, not the
underlying public models or reference data. Sequence preferences and predicted
structures support hypothesis review, not measured enzyme performance.

## Public GitHub Repository

https://github.com/ParkYaeseong/BioPilot

## 3-Minute Demo Video

https://www.youtube.com/watch?v=V7jWi7q1ggU

## Describe your use of Meta products to build the submitted project

The submitted product uses the Meta Model API with muse-spark-1.3 as its runtime
agent. Meta requests MCP target validation and position scoring, then produces a
bounded explanation of the recorded evidence. The demonstrated run completed with
3 Meta requests, 2 MCP calls and 19 scored candidates. The MCP server and Python
host enforce reference identity, scientific guards, approval and call limits; local
ESM-2 performs the numerical scoring. Codex and Claude assisted development and are
disclosed separately. We do not present them as the product's Meta runtime or claim
that Muse Code was used.

The structure review additionally displays separately acquired ESMFold2 and ESM3
GPU predictions and a Biohub ESM Atlas exact-reference snapshot. These are optional
scientific evidence sources, not additional Meta Model API calls or tool calls
retroactively attributed to the demonstrated Meta trace.

## Why are Meta's models important to your solution?

Meta provides the natural-language-to-tool coordination layer. It turns a research
request into permitted scientific tool calls and explains the returned evidence,
while deterministic code remains responsible for safety checks, computation and
ranking. This makes BioPilot an interactive review workflow rather than only a
scoring script. We preserve the actual model identity and tool trace so researchers
can inspect what Meta requested and what the scientific code computed.

## Provide feedback from your experience using partner technologies

Fireworks, Modal and Baseten were not used to serve the submitted runtime. We ran
ESM-2 locally and used a separately authorized L40S server for optional scientific
predictions, so I cannot provide a meaningful deployment comparison of those partners.

## Survey selections — owner opinion required

- How likely are you to build with Meta Model API? Suggested: **Likely**.
- Overall opinion of Meta Model API? Suggested: **Positive**.
- Recommend Meta Model API? Suggested: **8/10**, only if it matches the owner's opinion.
- Recommend Muse Code? **Not used / N/A**. Do not invent a usage-based score; if the field requires a number, the owner must decide how to answer.

## Publicity permission

The owner must read and choose whether to grant Meta/Cerebral Valley permission to
use, publish, share and promote submitted materials. No acceptance is presumed here.

## What was the biggest obstacle your team hit while building this project?

Keeping sequence numbering, structure numbering and execution state consistent.
The full 212-residue reference and the public structure use different numbering,
and some residues have no observed atoms. We built explicit correspondence checks
and missing-coordinate handling instead of guessing locations. We also added
durable execution records so page refreshes and result navigation cannot silently
dispatch another paid review.

## Compared with other AI models your team has used for the same kind of work, how did Meta's models perform on this project?

We did not run a controlled same-task benchmark against other models, so we cannot
claim a performance advantage. Muse Spark successfully completed the demonstrated
bounded validation-and-scoring workflow and produced an evidence explanation.
Codex and Claude were used for development assistance, which is a different task
from the submitted runtime agent and is not a fair head-to-head comparison.

## When your team chooses an AI model or coding tool, what matters most?

Reliable structured tool calls, adherence to constraints, inspectable outputs,
predictable latency and cost, clear data-use terms, and integration with an existing
Python/MCP workflow. For scientific work, reproducibility and failure handling
matter more than fluent but unsupported explanations.

## What makes it hardest for your team to switch to a different AI model or coding tool?

Revalidating tool schemas, prompt behavior, provider-specific response handling,
usage accounting and failure cases. A replacement must preserve the same scientific
guards and provenance, so migration requires regression testing rather than only
changing a model name.

## If your team took this project to production, what would most likely stop you from using Meta's models?

Insufficiently predictable pricing, rate limits or availability for the intended
workload, or data-handling terms that do not meet future private-research requirements.
Production adoption would require workload-specific reliability and cost evaluation;
our hackathon runs do not establish production readiness.
