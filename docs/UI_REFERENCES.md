# UI references and implementation decisions — 2026-10-28

The user requested public co-science references and a Vercel-like visual style.
These sources were inspected read-only. They inform interaction and hierarchy;
no repository was cloned, executed or used as a copied code/asset starter.

| Primary source | Observed relevance | BioPilot decision |
|---|---|---|
| [K-Dense BYOK](https://github.com/K-Dense-AI/k-dense-byok), [basic usage](https://github.com/K-Dense-AI/k-dense-byok/blob/main/docs/basic-usage.md), [provenance](https://github.com/K-Dense-AI/k-dense-byok/blob/main/docs/provenance.md) | Research task workspace, file/artifact inspection and recorded execution provenance | Separate task context, recorded tool decisions, numerical candidate results and original evidence |
| [Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills) | Procedural scientific skills, formerly Claude Scientific Skills; not an application UI starter | Keep explicit input/output/verification contracts; do not import broad scientific tool access |
| [Geist introduction](https://vercel.com/geist/introduction), [typography](https://vercel.com/geist/typography), [tabs](https://vercel.com/geist/tabs) | Restrained visual hierarchy, sibling views, compact status and progressive disclosure | Original local monochrome CSS, readable candidate rows and labeled controls, small semantic state accents |
| [Geist Font](https://github.com/vercel/geist-font) | Sans/mono hierarchy | Use local system fonts; no new font dependency or remote font request |

K-Dense BYOK's [MIT license](https://github.com/K-Dense-AI/k-dense-byok/blob/main/LICENSE)
and the skills repository's [MIT license](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/LICENSE.md)
were inspected; individual skills may have separate terms. Geist Font records
[SIL OFL 1.1](https://github.com/vercel/geist-font/blob/main/LICENSE.txt).
Those licenses are source observations, not a blanket rights clearance for this
project. No third-party visual asset or implementation is redistributed by this change.

## Scope and authenticity

The product runtime stays the existing controlled Meta/MCP path. Referencing a
Claude-related project does not introduce Claude as a product model or a fallback.
There are no new shell/file/URL tools or cloud services. The viewer presents saved
run evidence and isolated real local input checks; it never invents a new Meta
decision, scientific computation, provider bill or measured research gain.

The retained score family is `esm150_masked_v1` in `full_212`; selection and CSV
are views of that saved rank, not new scoring/ranking methods. Current playback
and original computation modes remain explicit. Unknown original goal/additional
constraints are not reconstructed from defaults.

## Subsequent refinement

On2026-10-28 inspected [Geist introduction](https://vercel.com/geist/introduction)
and [Linear's official product overview](https://linear.app/features) for restrained
hierarchy, consistent controls and ordered work. Applied original local CSS and
system fonts; no vendor assets or application code copied. Replaced the long
explanation card with an acting offline walkthrough and moved uploads to Input.
