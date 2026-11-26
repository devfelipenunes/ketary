# Security policy

Ketary is an experimental unreleased SDK. Report suspected security issues
privately through GitHub's private vulnerability reporting if enabled, or
request a private channel from the repository maintainer without posting
exploit details publicly.

JSON replay accepts only a bounded allowlist and never executes code.
Native Python objects and in-process callers are trusted; Ketary is not
a sandbox. Payload guards do not guarantee total memory or CPU bounds.

CI uses read-only contents permissions and disables persisted checkout
credentials. Dependency audit is a snapshot of known advisories. Before
release, review action commit pinning, build tool constraints, provenance
and artifact signing. Do not add publication credentials to PR workflows.
