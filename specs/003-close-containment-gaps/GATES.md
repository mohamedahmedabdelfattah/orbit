# Gates: Feature 003 implementation plan

OWNS: specs/003-close-containment-gaps/**

Scope: Produce a complete, internally consistent implementation plan and Phase 0/1 design artifacts for the fail-closed native Windows containment P0 fix.

- [x] G0: the gate ledger contains executable outcome checks that can fail
  EVIDENCE: 2026-11-06; ledger lint passed; runnable checks use direct artifact assertions and manual security gates carry independent adversarial-review evidence.

- [x] G1: every required planning artifact exists and contains no unresolved clarification marker
  CHECK: python -c "from pathlib import Path; d=Path('specs/003-close-containment-gaps'); required=['plan.md','research.md','data-model.md','quickstart.md','contracts/containment-hook.md','contracts/trusted-policy.md','contracts/gateway-invocation.md','contracts/mxc-runtime.md','contracts/readiness-evidence.md']; missing=[p for p in required if not (d/p).is_file()]; assert not missing, missing; text='\n'.join((d/p).read_text(encoding='utf-8') for p in required); assert 'NEEDS CLARIFICATION' not in text; print('plan artifact verification passed')"
  EXPECT: plan artifact verification passed
  EVIDENCE: automatic-evidence=v1; definition-sha256=6debdd9bfea92fef3c1920c914d91a7ac2fa74d288f4f54e81f8433b807f4c0a; exit=0; EXPECT=matched; output-sha256=a26f99620294c94bc7118de10fad3e11dc26733d795ec498f07c20b80ca280a6; output-bytes=35; shell=C:\Windows\system32\cmd.exe; cwd=C:\Users\Mohamed\.local\share\opencode\worktree\045683\eager-tiger; path=4056517a37ee/42 entries

- [x] G2: the planning artifacts explicitly cover all 36 functional requirements and 9 success criteria
  CHECK: python -c "from pathlib import Path; import re; text=Path('specs/003-close-containment-gaps/plan.md').read_text(encoding='utf-8'); fr={int(n) for n in re.findall(r'FR-(\d{3})',text)}; sc={int(n) for n in re.findall(r'SC-(\d{3})',text)}; expected_fr=set(range(1,37)); expected_sc=set(range(1,10)); assert fr == expected_fr and sc == expected_sc, {'missing_fr':sorted(expected_fr-fr),'unexpected_fr':sorted(fr-expected_fr),'missing_sc':sorted(expected_sc-sc),'unexpected_sc':sorted(sc-expected_sc)}; print('requirement coverage verification passed')"
  EXPECT: requirement coverage verification passed
  EVIDENCE: automatic-evidence=v1; definition-sha256=7e29b4910eb9a1537951550911472d66c44703ed9364bd537b69023d01db9320; exit=0; EXPECT=matched; output-sha256=c8a2370aaee8c4bfe8cd8c3f7786eb98be4867851c67ea7d52f31ea2b6fa99ce; output-bytes=42; shell=C:\Windows\system32\cmd.exe; cwd=C:\Users\Mohamed\.local\share\opencode\worktree\045683\eager-tiger; path=4056517a37ee/42 entries

- [x] G3: the design pins the full reviewed Claude Code, MXC, schema, executable, host-preparation, architecture, and Windows-build baseline
  CHECK: python -c "from pathlib import Path; text=Path('specs/003-close-containment-gaps/contracts/mxc-runtime.md').read_text(encoding='utf-8').upper(); values=['2.1.295','1.0.1','1.0.0','416D9607C9D4652395D95C3D9C5F5605F1F2F845DA1A63228BEE41B7392CEF49','090F5D1F7BB93104AB08DCD4E8034EF954AEEFCDAF6658DDE5F7DFF4CFC12F3A','91AA4171E8809F33F19622C381116188EAB7D8C8CFFAD231230A31B58146EE77','C18783AD3DD62C0A54530B25192B7C4015706B3F518CD9619259AE9750D4AB6E','74CCAE215A9C5E81215BC7124AA31CDD7A0B2215A79B5CF8865865BBDAAF93E2','207254FA94966A800FA70F01A2DA73AE813D27FE8847200C92F4DD0E219649C2','26100.9278','26200.9278','26300.9550','28000.2804']; missing=[v for v in values if v not in text]; assert not missing, missing; print('external baseline verification passed')"
  EXPECT: external baseline verification passed
  EVIDENCE: automatic-evidence=v1; definition-sha256=c6043883c2afbf35abed02942247b347aa1499b4d3bb2a94c551fb258c8e5e0e; exit=0; EXPECT=matched; output-sha256=04e2858620fd63934f82d830deef555f2899805f9877236f17b40ab5038b7553; output-bytes=39; shell=C:\Windows\system32\cmd.exe; cwd=C:\Users\Mohamed\.local\share\opencode\worktree\045683\eager-tiger; path=4056517a37ee/42 entries

- [x] G4: architecture decisions preserve one fail-closed terminal disposition and remove employee-writable inputs from every host-execution decision
  EVIDENCE: Independent adversarial review 2026-11-06 PASS: closed CommandDisposition/ExecutionTicket, prompt gate, stable trusted-policy reads, gateway authorization, and deny-on-uncertainty remove workspace/profile/cache/HKCU/connector authority.

- [x] G5: the design defines executable validation for hook failures, policy tampering, gateway bypasses, exact-schema checks, timeout cleanup, and x64/ARM64 real-host release evidence
  CHECK: python -c "from pathlib import Path; text=Path('specs/003-close-containment-gaps/quickstart.md').read_text(encoding='utf-8').lower(); required=['hook failure matrix','policy-tampering matrix','gateway bypass corpus','exact-schema validation','timeout cleanup','x64','arm64','clean installation','upgraded installation','release evidence']; missing=[v for v in required if v not in text]; assert not missing, missing; print('validation guide verification passed')"
  EXPECT: validation guide verification passed
  EVIDENCE: automatic-evidence=v1; definition-sha256=63eeb5b6fab46ea3140572b6a5bd37fa0b687f404f3b5dcab9965259484ab4bb; exit=0; EXPECT=matched; output-sha256=c5f17faa49fb09bea0d625e7fd81310a18f74a3e77158b323a75188c28c00d2e; output-bytes=38; shell=C:\Windows\system32\cmd.exe; cwd=C:\Users\Mohamed\.local\share\opencode\worktree\045683\eager-tiger; path=4056517a37ee/42 entries

- [x] G6: generated documentation has no trailing whitespace and every file ends with a newline
  CHECK: python -c "from pathlib import Path; d=Path('specs/003-close-containment-gaps'); rel=['GATES.md','spec.md','checklists/requirements.md','plan.md','research.md','data-model.md','quickstart.md','contracts/containment-hook.md','contracts/trusted-policy.md','contracts/gateway-invocation.md','contracts/mxc-runtime.md','contracts/readiness-evidence.md']; paths=[d/p for p in rel]; bad=[(str(p),i) for p in paths for i,line in enumerate(p.read_text(encoding='utf-8').splitlines(keepends=True),1) if line.rstrip(chr(13)+chr(10)).endswith((' ',chr(9)))]; nofinal=[str(p) for p in paths if not p.read_text(encoding='utf-8').endswith(chr(10))]; assert not bad and not nofinal, {'trailing':bad,'missing_final_newline':nofinal}; print('documentation whitespace check passed')"
  EXPECT: documentation whitespace check passed
  EVIDENCE: automatic-evidence=v1; definition-sha256=360b8fc1b2cfb257b438d8089b888bbe5f6d6b695e73be3d33179344c0c62843; exit=0; EXPECT=matched; output-sha256=15f71712f2a41e2e8a08e5d933a741f88f774f2a267c8d5db47b72833f9e5ce2; output-bytes=39; shell=C:\Windows\system32\cmd.exe; cwd=C:\Users\Mohamed\.local\share\opencode\worktree\045683\eager-tiger; path=4056517a37ee/42 entries

- [x] G7: managed-policy absence has a supported authoritative pre-run and continuous-session enforcement mechanism
  EVIDENCE: Independent final review 2026-11-06 PASS after native zero-arg policy-helper EXE, authenticated env/named-pipe nonce, correct unrelated-session output, remote-fetch suppression, and watchers. Follow-up fixes pin native build/signing and child environment reconstruction.

- [x] G8: registry, DNS, and Windows UI leaks are measured and warned by default, while an explicit owner deny blocks the affected workflow
  EVIDENCE: Independent amendment review 2026-11-06 PASS: exact LeakResult/ExplicitDeny matching warns and continues unmatched completed leaks; matching deny blocks complete employee native shell surface; structural/canary-execution failures remain blocking.

- [x] G9: hook input accepts documented fields, validates required semantics, and strips model-selected background or timeout controls from rewrites
  EVIDENCE: Independent adversarial review 2026-11-06 PASS: contracts/containment-hook.md PreToolUse input and Terminal outputs accept documented observations and rebuild foreground policy-timeout input.

- [x] G10: final host gateway catalog and every descendant executable/dependency are fixed, verified, and owned by explicit implementation files/tests
  EVIDENCE: Independent adversarial review 2026-11-06 PASS: final host catalog is Apify/compute, explicit target files/tests and locked dependencies assigned, all other gateways contained. Subsequent correction also adds OS-enforced child restriction/one-process Job.

- [x] G11: first legacy upgrade quiesces before source replacement through an external bootstrap
  EVIDENCE: Independent final review 2026-11-06 PASS: permanent 0.8.0-sec.N line stays equal under exact legacy comparator even when latest; Microsoft Store bootstrap persists stop/block before mutation.

- [x] G12: release evidence names an exact attestation/signature trust root and publication dependency
  EVIDENCE: Independent final review 2026-11-06 PASS: Microsoft Store initial root, TPM RSA-PSS runners, offline Ed25519 aggregate, RFC8785/domain/encoding, revocation/rotation, exact workflow/environment/publication gate. Follow-up corrects Store-assigned ID terminology and pins exact package version.

- [x] G13: ticket/evidence schemas are consistent and strict MCP/connector state participates in policy fingerprints
  EVIDENCE: Independent adversarial review 2026-11-06 PASS: nested ticket and install_scenario are unified; connectors/MCP grants live in strict owner state and policy fingerprints.

- [x] G14: runtime readiness supports ready-with-warnings without weakening hook, policy-source, artifact, or gateway fail-closed boundaries
  EVIDENCE: Independent amendment review 2026-11-06 PASS: StructuralResult precedence blocks hook/policy/gateway/artifact/launch/measurement/cleanup failures before leak join; only enumerated completed canaries may warn.

- [x] G15: quickstart and release evidence prove both advisory-leak continuation and explicit-owner-deny blocking
  EVIDENCE: Independent amendment review 2026-11-06 PASS: deterministic match corpus, dual-policy continuation/blocking, clean/upgrade/architecture evidence, and separate zero-survivor cleanup are mandatory.
