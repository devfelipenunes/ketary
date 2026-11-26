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
