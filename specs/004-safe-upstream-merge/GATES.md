# Gates: Safe upstream v0.12.0 integration

OWNS: **

Scope: Preserve both reviewed lines of work, validate one exact candidate, record a genuine local two-parent merge, remove only the temporary replacement, and leave remote publication on hold.

- [x] G1: The intended candidate has complete path accounting, no unresolved index entries or accidental conflict markers, parses cleanly, and reports version 0.12.0.
  CHECK: python verify_candidate.py structural
  EXPECT: SAFE_MERGE_STRUCTURAL_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=4833e10b08c366191d502fd13b6aefa7cf72ee85ded59a7fc81a22335fcd8ffe; exit=0; EXPECT=matched; output-sha256=6e2dd823d06e84a87536e85d15d7eadfabc8db1c0da3460035fbc5541bbf3f59; output-bytes=26; shell=C:\Windows\system32\cmd.exe; cwd=D:\Programming\Projects\AI\Orbit\specs\004-safe-upstream-merge; path=4056517a37ee/42 entries

- [x] G2: All six Python test modules run in separate child processes, every host-applicable case passes, unavailable dependencies/platforms remain explicit skips, and registered disposable test data is removed.
  CHECK: python verify_candidate.py tests
  EXPECT: SAFE_MERGE_TESTS_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=b406cda572f3110a9f4562b640ccfaf1c044ad2d2c9f4c05fbceecec9e0a398d; exit=0; EXPECT=matched; output-sha256=94a1fcea6d750715c634f5a35290b7a2e7cb7dc0575936e44eeed9a76a37b09f; output-bytes=109; shell=C:\Windows\system32\cmd.exe; cwd=D:\Programming\Projects\AI\Orbit\specs\004-safe-upstream-merge; path=4056517a37ee/42 entries

- [x] G3: The integration ledger and validation records account for every regenerated input path and satisfy their schema, overlap, invariant, and candidate-tree constraints.
  CHECK: python verify_candidate.py evidence
  EXPECT: SAFE_MERGE_EVIDENCE_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=bd00d48059a1834592c0846b887892e0504a8875c72a034a357f7e5577040f20; exit=0; EXPECT=matched; output-sha256=3acdf405c1198ccb6de1c683561faa1917aecc993757db0c7c74c79ece1e786c; output-bytes=24; shell=C:\Windows\system32\cmd.exe; cwd=D:\Programming\Projects\AI\Orbit\specs\004-safe-upstream-merge; path=4056517a37ee/42 entries

- [x] G4: The locally recorded merge has exactly the reviewed local and upstream parents, keeps the validated tree after replacement removal, preserves recovery, and leaves no replacement ref.
  CHECK: python verify_candidate.py history
  EXPECT: SAFE_MERGE_HISTORY_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=6efbe8823a28bbdec0db3f9b7eed3966ce624eb0f2446e2be201b1c6cf60a06e; exit=0; EXPECT=matched; output-sha256=c5238c9b46f83ad290f41fc21d644a268cb3642c33e8e0669c80ecef63d3ab36; output-bytes=23; shell=C:\Windows\system32\cmd.exe; cwd=D:\Programming\Projects\AI\Orbit\specs\004-safe-upstream-merge; path=4056517a37ee/42 entries

- [x] G5: Publication remains `hold_local`; no remote ref is changed without a later explicit owner decision.
  EVIDENCE: manual-evidence=v1; judged from the repository and session record on 2026-11-11 — `git ls-remote origin refs/heads/main` still advertises `da644db1159d076b8119ad621ba421f2da8ecbe0` (read-only refresh, no fetch), no push or remote write was executed in any session step, `publication-options.md` records the decision as `hold_local` / approval "no positive remote-write approval has been given" / status `pending`, and `C:\Users\Mohamed\AppData\Local\Temp\opencode\orbit-upstream-merge-publication-handoff.md` requires a fresh owner decision plus a re-observed remote tip before any remote action. Reader caveat: manual statement, not machine-checked.
