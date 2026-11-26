# Four bounded QML workflows

Ref #295. Independent analytic oracle and native Qiskit programs:
angle encoding with a fixed synthetic regression target and threshold
classification (score Z); parity of rotated product bits, predicted
by Z on the CNOT target; overlap kernel from inverse feature map;
shared-parameter nonlinear regression with occurrence-specific gradient.
Fixed TRAIN/HELD split and fixed pair fixtures; no claim of independent
usability, generalization, ML superiority or quantum advantage. Angle
training records eight steps of loss, derivative and parameter; held
outputs are not used for fitting. Regression records predictions,
gradient and training loss/gradient; no hidden optimizer.

The runnable script provides both SDK and native builder sources and
token/line counts for those builders only, representative full operator
checks and instruction counts, state payload bytes (not RSS), matched
full-workload timings with raw p50/p95. Native angle objective uses
separate Statevector execution per shift; shared regression native route
uses explicit per-occurrence shifts. Differences in orchestration are
reported, not attributed to simulator superiority. The fixtures are
small and deliberately transparent, not production datasets.

Classification decisions are now explicit: angle score >=0.8, targets
cos(x+0.41)>=0.8 on the disjoint held-out points; parity score >=0.5
on fixed evaluation pairs, no fitted parity classifier. Accuracy and
predicted/target binary labels are recorded alongside continuous scores.
Both target classes occur in the fixed evaluation fixtures. This is a
synthetic task, not evidence of real-world generalization. The angle
optimizer still minimizes a continuous surrogate, not classification
cross-entropy. Builder-only token counts exclude shared orchestration.
