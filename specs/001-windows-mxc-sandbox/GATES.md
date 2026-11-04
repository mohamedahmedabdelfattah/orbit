# Gates: Windows MXC feature (001-windows-mxc-sandbox)

OWNS: core/mxc.py, core/osinfo.py, core/engine.py, core/calls.py, orbit, install.sh, setup-windows.ps1, tests/test_mxc.py, tests/test_platforms.py, tests/test_calls.py, .github/workflows/tests.yml, README.md, SETUP.md, CLAUDE.md, PRODUCT.md, VERSION, specs/001-windows-mxc-sandbox/**

Scope: implement native-Windows MXC sandboxing (per-command containment via the PreToolUse hook, WSL2 fallback, service/doctor/installer/peripherals, CI) exactly to spec.md, tasks.md, and contracts/, with zero mac/Linux/WSL2 regressions and no manual release gate (owner decision 2026-11-04).

- [x] G1: the planning artifacts are internally consistent — no stale cross-references (SE-1, old CI section title, T042→T034, per-run containment wording), every referenced task id is defined, and quickstart Scenarios A–F all exist
  CHECK: python verify_gates.py planning
  EXPECT: planning verification passed
  EVIDENCE: automatic-evidence=v1; definition-sha256=e3805c5e235634324f6e0865bbe00a0ce75650797fa3b503acffbae86942fdb6; exit=0; EXPECT=matched; output-sha256=aed58dfe98e19b6e157165d6576a7ee95c218bd6c22c44d1bbcaed0392aa67af; output-bytes=30; shell=C:\Windows\system32\cmd.exe; cwd=D:\Programming\Projects\AI\Orbit\specs\001-windows-mxc-sandbox; path=0ea21c6dbd38/41 entries

- [ ] G2: Phase 1–2 lands — native Windows is a first-class platform kind with Windows metadata/secret paths/peripheral branches, and sandbox-mode storage helpers validate owner-vs-unavailable decisions (T001–T015)
  CHECK: python verify_gates.py phase2
  EXPECT: phase2 verification passed
  EVIDENCE: pending

- [ ] G3: Phase 4 lands — per-command policy translation satisfies the mxc-request contract invariants and the hook decision matrix behaves per the cc-hook contract (allow+rewrite pairing, excluded pass-through, deny-on-failure, no widening) with mac/WSL settings byte-identical (T030–T035)
  CHECK: python verify_gates.py phase4
  EXPECT: phase4 verification passed
  EVIDENCE: pending

- [ ] G4: Phase 5 lands — the probe produces usable/unusable-with-reason verdicts from the positive/negative matrix and refuses unsandboxed work when unusable (T040–T043)
  CHECK: python verify_gates.py phase5
  EXPECT: phase5 verification passed
  EVIDENCE: pending

- [ ] G5: Phases 6–7 land — WSL2 fallback triggers only on MXC unavailability or explicit owner bypass, the doctor surfaces both fix paths verbatim, and no path switches modes per-run (T050–T061)
  CHECK: python verify_gates.py phase57
  EXPECT: phase57 verification passed
  EVIDENCE: pending

- [ ] G6: Phases 3 and 9 land — native installer/scheduled-task service/doctor/peripheral checks work with unit coverage, with no WSL-mentioning failure messaging (T020–T025, T080–T082)
  CHECK: python verify_gates.py phase39
  EXPECT: phase39 verification passed
  EVIDENCE: pending

- [ ] G7: the CI workflow gains the windows-latest unit job carrying the owner-mandated hint that MXC containment itself is not part of automated testing, pointing to quickstart.md as an on-demand guide — and no release checklist exists anywhere (T090, T092)
  CHECK: python verify_gates.py ci
  EXPECT: ci verification passed
  EVIDENCE: pending

- [ ] G8: the full suite — all existing modules plus test_mxc — is green with zero mac/Linux/WSL2 behavioral diffs, on the fake executor only (T091, T093)
  CHECK: python verify_gates.py full
  EXPECT: full-suite verification passed
  EVIDENCE: pending
