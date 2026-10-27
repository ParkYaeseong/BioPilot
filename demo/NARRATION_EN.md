# Three-minute narration draft

This is a recording script, not a claim that the demo already exists. Show the described real
behavior only after implementing it. Read at a comfortable pace; leave room for the tool/result
screen. Replace the single measured-result slot with actual evidence or the supplied honest fallback.

## 0:00-0:20 | Problem

Reviewing a protein variant means more than running a model. A researcher has to check residue
numbering, protect important sites, gather evidence and keep track of computation. BioPilot Atlas
connects these steps through verifiable tools that a Meta model can use.

## 0:20-0:45 | Request

Here I am reviewing a public Lipase A reference. I ask for single-substitution candidates, with
explicit protected positions and a limited computation budget. The application checks which
sequence frame I am using. It does not silently guess how residue numbers should be converted.

## 0:45-1:20 | Actual execution

This is the actual Meta model selected for the run. It chooses an allowed BioPilot MCP tool.
The server checks the request and runs the scientific computation. These values come from ESM,
not from language-model text. Each result is linked to its model, input and saved artifact.

## 1:20-1:50 | Meaningful branch

Now I change a constraint or remove an optional capability. The server prevents unauthorized
work. The model can use the remaining permitted evidence or finish with a partial review.
This division matters: the model coordinates the work, but code enforces the rules.

## 1:50-2:25 | Output

The result is a ranked list for human review, with evidence and explicit unknowns. The ranking
uses one defined ESM score policy. Reference structures and predicted structures are labeled
separately. An ESM score is not a measured improvement in thermal stability, and preserving a
catalytic residue does not prove that the enzyme still works. The run and its evidence can be exported.

## 2:25-2:45 | Evidence

Use one verified version only:

**Measured:** 'On [N] defined tasks, we compared [METHODS] under [MATCHED CONDITIONS]. We observed
[ACTUAL RESULT], with [IMPORTANT LIMITATION]. The supporting traces are included.'

**Not yet measured:** 'This demonstration establishes tool execution and the tested constraint
checks. We have not yet established biological improvement or a general time-saving claim.'

## 2:45-3:00 | Contribution

Our contribution is a reusable, inspectable scientific workflow through MCP, with Meta making
bounded decisions over real tools. BioPilot supports the researcher's next review decision;
it does not replace experimental validation.

## Recording notes

Identify LIVE vs REPLAY vs IMPORTED SNAPSHOT on screen. Never describe a fixture as real.
Do not read placeholders aloud. If a function is missing, remove that claim and disclose the gap.
Final narration length and exported duration need actual recording verification.
