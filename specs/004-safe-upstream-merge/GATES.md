# Gates: Safe upstream v0.12.0 integration

OWNS: **

Scope: Preserve both reviewed lines of work, validate one exact candidate, record a genuine local two-parent merge, remove only the temporary replacement, and leave remote publication on hold.

- [ ] G1: The intended candidate has complete path accounting, no unresolved index entries or accidental conflict markers, parses cleanly, and reports version 0.12.0.
  CHECK: python specs/004-safe-upstream-merge/verify_candidate.py structural
  EXPECT: SAFE_MERGE_STRUCTURAL_OK
  EVIDENCE: pending

- [ ] G2: All six Python test modules run in separate child processes, every host-applicable case passes, unavailable dependencies/platforms remain explicit skips, and registered disposable test data is removed.
  CHECK: python specs/004-safe-upstream-merge/verify_candidate.py tests
  EXPECT: SAFE_MERGE_TESTS_OK
  EVIDENCE: pending

- [ ] G3: The integration ledger and validation records account for every regenerated input path and satisfy their schema, overlap, invariant, and candidate-tree constraints.
  CHECK: python specs/004-safe-upstream-merge/verify_candidate.py evidence
  EXPECT: SAFE_MERGE_EVIDENCE_OK
  EVIDENCE: pending

- [ ] G4: The locally recorded merge has exactly the reviewed local and upstream parents, keeps the validated tree after replacement removal, preserves recovery, and leaves no replacement ref.
  CHECK: python specs/004-safe-upstream-merge/verify_candidate.py history
  EXPECT: SAFE_MERGE_HISTORY_OK
  EVIDENCE: pending

- [ ] G5: Publication remains `hold_local`; no remote ref is changed without a later explicit owner decision.
  EVIDENCE: pending
