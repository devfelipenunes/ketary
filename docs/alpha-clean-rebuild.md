# Clean rebuild qualification — #110, #35

Earlier same-tree PR #498 and main cdb6600 wheel/sdist artifacts contained
identical member contents (33 and 258 members), but different compressed
hashes and all member timestamps/mtimes. Do not call that bit reproducible.

The candidate harness performs two clean builds from the exact committed Git
tree with pinned tooling, fixed SOURCE_DATE_EPOCH, PYTHONHASHSEED, UTC and C
locale. It compares raw SHA256 and member content/metadata, without rewriting
archives. Content differences fail; byte differences are retained as negative
evidence and do not close the reproducibility gate. One runner is not cross-
platform reproducibility. The existing installation and dependency checks
remain mandatory. No published artifact changes or legal approval.


## Deterministic archive creation candidate

The stock PEP 517 backend remains the baseline. In a research-only subprocess
using pinned setuptools 84.2.1, intercept the sdist release-tree archive creation
once and emit a sorted tar stream with fixed epoch, owner and gzip header. No
existing artifact is rewritten and no installed package or configured build
backend is changed. Compare both independently generated candidate sdists,
both wheels built from those sdists, and original stock member contents.
Reject symlinks and unexpected archive formats; fail on content divergence or
candidate byte divergence. This is a qualification experiment, not a release
procedure or general cross-platform reproducibility guarantee.
