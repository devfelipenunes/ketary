# RF refinement and code review cycle

Baseline 452a2f5 (research atlas, 32 tasks). New RF issues #169–#198
are child tasks of #106/#166, not a replacement for TC/QA/ABS.
#199 integrated at 2af669c: public aligned angles in seven existing
pair rotation methods, 986 passed / 12 skipped / 95% branch coverage.
#200 integrated at c85ee4d: executable 13-task source rewrite ladder;
all three rewrite jobs and six SDK jobs passed.

## Observed first rewrite experiment

Run 45770886424, three runners, same source metrics in all three.
13 tasks, four versions, strict phase and arbitrary complex inputs.
Totals: scalar/fluent/intent/Qiskit tokens 604/500/306/531,
AST nodes 698/542/340/609, statements 60/24/17/51, loops 19/12/5/9,
calls 69/65/39/74, numeric literals 41/29/14/39. All four have
195 u,cx basis gates and summed depth 128. Retrospective shortest
Ketary per task 282 tokens (not an automatic source optimizer).
Maximum operator/state/basis residual <=2.223e-15.
Retain negative evidence: QFT middle rewrite 103 vs scalar 78,
conjugation intent 51 vs fluent 27, QPE middle 83 vs scalar 71.
Qiskit QFT factory and opaque execution can be faster than Ketary's
expanded circuit; equal common-basis counts do not mean equal run time.
These are authored tasks, not independent human readability data.

## Decisions and next checks

| Issues | Direction |
|---|---|
| #169 #172–174 #192 #194 | Executable ladder, matched references, complete source and metrics; extend held-out cases separately |
| #170–171 #191 #195 | Aligned pair API accepted, exact-order and rollback; scale diagnostic in this PR |
| #175–177 | Separate #201 candidate exact commuting evolution, no silent approximation |
| #178–181 | QAOA, QFT, QPE, VQE: keep useful algorithm loops and existing factories; avoid generic wrappers that lose |
| #182–186 | Research product/basis, oracles, arithmetic, graph states and reflection; compare native factories and distinct semantics before public promotion |
| #187–189 | Current conjugation/repeat remain canonical; explicit approximation and controlled synthesis research only |
| #190 | Avoid separate generic IR/DSL; extract only proven code duplication |
| #193 | Paired construction/runtime costs; dedicated host/RSS still pending |
| #196 | Approve selected narrow additions only; reject redundant layer/power/topology aliases until evidence |
| #197 | Held-out task protocol; no independent participants or agent trials |
| #198 | Exact-head full CI and integrated verification; no publication |

### Recursive review method

1. Start from a correct scalar circuit, with exact task and inputs.
2. Reread for repeated placement, parameter alignment and reusable blocks.
3. Rewrite using current canonical Ketary. Keep algorithmic control flow.
4. Compare with mathematical intent and the strongest matching Qiskit idiom.
5. Strict full operator, arbitrary complex state, common-basis gate/depth,
   source metrics, paired raw timing and negative resource/ownership tests.
6. Preserve the losing versions and their reason. Do not equate token count
   with readability; no claim of independent review or dedicated performance.
7. Promote only a narrow compatible change; repeat on new held-out cases.

The scaling harness measures 2 gates x 5 sizes x 2 input modes; native
scalar broadcast is compared only when all angles are equal. Every
variant must produce the same ordered native instructions; full operator
up to 100 pairs. Python tracemalloc is reported separately, never as RSS
or native-memory evidence. No timing thresholds in CI.
