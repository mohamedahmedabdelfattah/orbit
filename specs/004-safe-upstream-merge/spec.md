# Feature Specification: Safe Upstream Synchronization

**Feature Branch**: `main` (existing integration in progress)

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Safely merge local origin main with upstream to update the app while keeping all the local and new work intact. Origin was at version 0.8.0 when it was forked and local updates were implemented; upstream advanced to 0.12.0 and has not yet been correctly synchronized. Continue from the merge handoff."

Orbit's local fork contains substantial Windows, connection pass-through, containment, documentation, and validation work built from the upstream 0.8.0 era. Canonical upstream has independently advanced through 0.12.0 with new application behavior. The histories represent some equivalent earlier releases with different identities, and an earlier synchronization recorded upstream ancestry without actually incorporating its content. This feature produces one validated application state that contains both bodies of work, preserves their intended safety boundaries, and remains recoverable and auditable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Update the Fork Without Losing Either Line of Work (Priority: P1)

A maintainer updates the local application from its 0.8.0-era upstream base to the complete upstream 0.12.0 product while retaining every compatible local enhancement, test, specification, and document added since the fork.

**Why this priority**: The synchronization has no value if it omits upstream releases or silently removes the local work that motivated the fork.

**Independent Test**: Compare the integrated candidate with both the pre-synchronization local baseline and upstream 0.12.0. Account for every changed tracked artifact from both lines as retained, intentionally combined, or explicitly rejected with owner approval; then verify that no unapproved omission exists.

**Acceptance Scenarios**:

1. **Given** a local fork containing post-0.8.0 work and an upstream line ending at 0.12.0, **When** the integration candidate is reviewed, **Then** all compatible changes from both lines are present together.
2. **Given** equivalent historical releases represented by different revision identities, **When** the common product baseline is established, **Then** equivalent prior work is not duplicated and local differences at that baseline are not discarded.
3. **Given** both lines changed the same behavior, **When** the changes are compatible, **Then** the candidate combines their intended outcomes rather than accepting one entire side and losing the other.
4. **Given** a genuine incompatibility that cannot preserve both intended outcomes, **When** it is discovered, **Then** integration stops for an explicit owner decision and records the impact of each option.

---

### User Story 2 - Preserve Safety and Connection Invariants While Adding Upstream Features (Priority: P1)

An existing Orbit owner receives upstream's newer conversations, brain-and-hands behavior, notifications, and Claude-app entry points without weakening the fork's native-Windows containment, WSL2 fallback, provider-neutral Claude connection pass-through, or account-only Cloud Shift boundary.

**Why this priority**: A source update that appears successful but weakens containment or restores an obsolete account/provider assumption is a product and security regression.

**Independent Test**: Exercise the accepted requirements from specifications 001 through 003 together with representative upstream 0.9.0 through 0.12.0 user flows. Verify that all local invariants and all new upstream flows work in the same candidate.

**Acceptance Scenarios**:

1. **Given** ordinary local work uses a Claude-supported connection without a qualifying Claude account, **When** a chat or routine starts after synchronization, **Then** it uses that configured connection without an account-wide gate or provider-specific readiness wait.
2. **Given** native Windows is configured for MXC containment, **When** an employee performs shell-capable work, **Then** existing fail-closed containment and explicit WSL2 fallback rules remain in force.
3. **Given** Cloud Shift lacks a qualifying account, **When** local work runs, **Then** local work remains available while Cloud Shift remains separately unavailable with accurate guidance.
4. **Given** upstream 0.12.0 application flows are present, **When** the owner opens Orbit's Claude-app desk or a crew member's running conversation, **Then** those flows retain upstream's session continuity and safety controls alongside local launch policy.
5. **Given** local security specifications, plans, tests, and supporting evidence predate synchronization, **When** the candidate is inspected, **Then** those artifacts remain intact and are not misrepresented as already implemented if they were planning-only work.

---

### User Story 3 - Validate One Coherent Release Candidate (Priority: P2)

A maintainer can determine whether the integrated candidate is complete and safe using repeatable checks that cover application structure, existing behavior, new upstream behavior, supported platforms, and user-facing documentation.

**Why this priority**: Textual conflict resolution alone cannot detect an auto-merged file that is syntactically valid but semantically combines incompatible assumptions.

**Independent Test**: Run all repository validation suites and targeted integration checks against the candidate, inspect all automatically combined high-risk files, and confirm that documentation describes the behavior actually delivered.

**Acceptance Scenarios**:

1. **Given** all explicit conflicts have been resolved, **When** repository-wide structural validation runs, **Then** no unresolved path, accidental conflict marker, duplicate active definition, malformed document, or invalid source file remains.
2. **Given** the candidate includes platform and security-sensitive changes, **When** automated regression validation runs, **Then** every existing mandatory suite passes without weakening or excluding prior checks.
3. **Given** a required platform check cannot run in the maintainer's current environment, **When** readiness is assessed, **Then** the missing evidence remains visible and governed by its existing release gate rather than being counted as a pass.
4. **Given** source behavior and user documentation overlap, **When** documentation is reviewed, **Then** commands, prerequisites, versions, cost/account language, and platform claims match the candidate.

---

### User Story 4 - Recover and Publish Deliberately (Priority: P2)

A maintainer can recover the pre-synchronization state, understand the final ancestry and content, and present safe publication choices without silently rewriting the fork's remote history.

**Why this priority**: The remote fork already contains a synchronization revision whose recorded ancestry and actual content disagree. Publishing another result without review could hide the corrected work or require an unexpected destructive update.

**Independent Test**: Demonstrate recovery from the preserved checkpoint, inspect the integrated candidate's ancestry and content, and verify that no remote-changing action occurs until the owner explicitly selects a publication approach.

**Acceptance Scenarios**:

1. **Given** integration fails validation, **When** recovery is requested, **Then** the exact pre-synchronization local baseline remains available without loss.
2. **Given** the candidate passes validation, **When** its history is inspected, **Then** both the local work and canonical upstream 0.12.0 are traceable and the candidate's content reflects both.
3. **Given** the fork's remote branch contains an earlier ancestry-only synchronization, **When** publication is considered, **Then** the owner receives non-destructive and history-replacing options with consequences before any remote update.
4. **Given** no publication choice has been made, **When** local integration completes, **Then** no forced remote rewrite or destructive cleanup occurs.

### Edge Cases

- Equivalent upstream releases were replayed under different revision identities, causing an obsolete ancestor to appear as the common baseline.
- Both lines added a file at the same path with different contents.
- Upstream removed or replaced a file that local functionality still requires.
- A file is free of textual conflict markers but remains unresolved in integration metadata.
- An automatically combined file is syntactically valid but contains duplicated behavior, contradictory branches, or an obsolete fallback.
- Documentation combines two accurate paragraphs into a misleading or duplicated statement.
- A provider-neutral local launch path overlaps upstream connectivity retry behavior tied to one provider.
- Upstream interactive-session behavior overlaps local environment, settings-source, sandbox, or containment policy.
- Platform-specific validation is unavailable on the current machine, especially real-host native-Windows containment evidence.
- Validation creates temporary team or session data; cleanup must leave the owner's existing data untouched.
- File modes, line endings, generated files, or ignored files differ across Windows, WSL2, Linux, and macOS.
- Canonical upstream advances beyond 0.12.0 while this integration is underway; the target remains pinned until this candidate completes.
- Temporary reconciliation metadata could alter history interpretation if left active after completion.
- The fork's remote branch contains a prior merge revision with correct ancestry but stale application content.

## Requirements *(mandatory)*

### Functional Requirements

#### Baseline and Change Coverage

- **FR-001**: The integration MUST use the pre-synchronization local application state and canonical upstream 0.12.0 as the two authoritative content inputs.
- **FR-002**: The integration MUST establish the verified 0.8.0 product relationship between the histories while preserving any local differences already present at that point.
- **FR-003**: Every tracked local change made after the fork MUST be accounted for as retained, semantically combined, or explicitly excluded with owner approval and a recorded reason.
- **FR-004**: Every canonical upstream product change through 0.12.0 MUST be accounted for as retained, semantically combined, or explicitly excluded with owner approval and a recorded reason.
- **FR-005**: Genuine overlapping changes MUST be resolved according to intended product behavior and accepted specifications; a broad preference for one side MUST NOT be used where it would silently remove compatible work from the other.
- **FR-006**: The integrated candidate MUST retain local specifications, plans, contracts, tests, setup assets, and documentation unless an artifact is demonstrably superseded and its removal is explicitly approved.
- **FR-007**: The integrated candidate MUST identify itself as application version 0.12.0 unless the owner approves a distinct fork version after synchronization.

#### Product and Safety Preservation

- **FR-008**: The integrated candidate MUST continue satisfying the accepted behavior and safety boundaries defined by `specs/001-windows-mxc-sandbox`, `specs/002-claude-connection-pass-through`, and `specs/003-close-containment-gaps`; synchronization MUST NOT weaken those requirements.
- **FR-009**: Ordinary local model-backed work MUST continue using Claude's effective configured connection without requiring a Claude-account login or a successful provider-specific connectivity preflight.
- **FR-010**: Native-Windows MXC mode, explicit WSL2 fallback, platform-specific tool surfaces, and fail-closed behavior MUST remain available and MUST NOT silently fall back to uncontained host execution.
- **FR-011**: Cloud Shift MUST remain an optional account-only capability whose eligibility and failure do not block ordinary local work.
- **FR-012**: Upstream's 0.9.0 through 0.12.0 user-visible behavior—including brain-and-hands model roles, one running crew-member conversation, report delivery and unread state, terminal/app chat continuity, and Orbit's Claude-app desk—MUST remain present unless an explicit conflict decision says otherwise.
- **FR-013**: Interactive and unattended crew work MUST apply the same effective local safety boundaries while retaining the interaction differences required by each mode.
- **FR-014**: Existing owner team data, employee workspaces, sessions, roles, routines, abilities, grants, and secrets MUST require no destructive migration as a result of source synchronization.
- **FR-015**: Planning-only local security work MUST remain clearly identified as planning or pending work; synchronization MUST NOT claim that preservation of an artifact proves its requirements are implemented.

#### Conflict and Documentation Quality

- **FR-016**: The final candidate MUST contain no unresolved integration paths or accidental conflict syntax in product source, tests, setup assets, or user documentation. Deliberate conflict strings used as test data MUST be clearly isolated as fixtures.
- **FR-017**: Every manually resolved overlap MUST have a reviewable rationale tied to a user scenario, accepted requirement, regression test, or authoritative upstream behavior.
- **FR-018**: Automatically combined high-risk files MUST receive semantic review even when the source-control system reports no textual conflict.
- **FR-019**: The candidate MUST contain one active definition for each runtime behavior unless multiple definitions are intentional, separately reachable, and covered by tests.
- **FR-020**: User documentation MUST describe the integrated behavior consistently, including supported platforms, Claude connection expectations, Cloud Shift eligibility, new conversation/desk flows, usage language, and the 0.12.0 version.
- **FR-021**: Documentation MUST NOT duplicate contradictory cost, account, setup, or safety guidance from the two input lines.

#### Validation and Readiness

- **FR-022**: All mandatory automated validation suites that passed on either input baseline MUST remain enabled and pass on the integrated candidate.
- **FR-023**: Targeted validation MUST cover every manually resolved runtime overlap and every local safety boundary affected by an upstream change.
- **FR-024**: Validation MUST separately prove representative upstream 0.9.0 through 0.12.0 flows and representative local native-Windows, connection pass-through, and containment flows.
- **FR-025**: Validation MUST preserve existing cleanup guarantees so test runs do not alter or delete an owner's real team data, sessions, or credentials.
- **FR-026**: A platform-specific check that cannot run in the current environment MUST be recorded as pending evidence, not reported as successful or silently removed from release criteria.
- **FR-027**: Existing P0 release gates for native-Windows containment MUST remain authoritative after synchronization, including any real-host evidence that cannot be produced by ordinary hosted validation.
- **FR-028**: Any failed check MUST block completion until it is corrected or the owner explicitly accepts a documented exception with its user and safety impact.

#### Recovery, History, and Publication

- **FR-029**: A stable recovery point for the complete pre-synchronization local state MUST remain available until the integrated candidate is validated and the owner approves cleanup.
- **FR-030**: The completed local history MUST make both the local baseline and canonical upstream 0.12.0 ancestry traceable while the resulting application content contains the approved semantic integration.
- **FR-031**: Temporary metadata used only to reconcile rewritten history MUST be removed after the integrated revision is safely recorded, and its removal MUST NOT change the candidate's content.
- **FR-032**: The integration process MUST NOT reset, overwrite, or discard unreviewed local work.
- **FR-033**: The integration process MUST NOT force-update, rewrite, or otherwise destructively change the fork's remote branch without explicit owner authorization after validation.
- **FR-034**: Before publication, the owner MUST receive the detected remote-history condition, available reconciliation choices, and the consequence of each choice for collaborators and future updates.
- **FR-035**: Completion evidence MUST include the target versions, retained local capability set, conflict-resolution summary, validation results, pending platform evidence, final content identity, and recovery-point status.

### Scope Boundaries

**In scope**:

- Integrating canonical upstream changes from the verified 0.8.0 relationship through 0.12.0.
- Preserving all compatible local product, platform, security, specification, documentation, and test work.
- Semantically resolving genuine overlaps and auditing automatically combined high-risk files.
- Validating the integrated candidate and documenting any evidence that requires another platform.
- Recording a safe local integrated revision and presenting publication choices for the fork remote.

**Out of scope**:

- Adding upstream changes newer than 0.12.0 during this synchronization.
- Implementing requirements that exist only as unimplemented work in local planning artifacts.
- Redesigning native-Windows containment, Claude connection pass-through, Cloud Shift, or upstream conversation features beyond what compatibility requires.
- Migrating or modifying live owner team data.
- Automatically force-updating or rewriting the fork remote.
- Removing historical specifications or safety evidence merely because upstream does not contain them.

### Key Entities *(include if feature involves data)*

- **Local Baseline**: The complete pre-synchronization fork state, including application code, tests, specifications, documents, and a stable recovery identity.
- **Upstream Release Baseline**: Canonical upstream 0.12.0 and its product changes since the corresponding 0.8.0 state.
- **Change Coverage Record**: An accounting of local and upstream changes showing whether each was retained, combined, or explicitly excluded.
- **Integration Candidate**: The proposed single application state containing the approved content from both baselines.
- **Behavioral Invariant**: A local or upstream outcome that must remain true after synchronization, especially security, platform, connection, session, and account boundaries.
- **Validation Evidence**: Results from structural checks, automated suites, targeted regressions, documentation review, and any pending platform-specific proof.
- **Recovery Point**: The preserved identity from which the complete local pre-synchronization state can be restored.
- **Publication Decision**: The owner's explicit choice for reconciling the validated local candidate with the fork's existing remote history.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The change coverage record accounts for 100% of tracked local changes since the fork and 100% of canonical upstream changes through 0.12.0, with zero unapproved omissions.
- **SC-002**: Comparison against both authoritative inputs finds zero lost local artifacts and zero missing upstream 0.12.0 product artifacts, except items explicitly excluded with owner approval.
- **SC-003**: The final candidate has zero unresolved integration paths, zero accidental conflict markers, zero source parsing failures, and zero unintended duplicate active definitions.
- **SC-004**: 100% of mandatory automated validation suites pass on the integrated candidate with no pre-existing test silently disabled, weakened, or skipped.
- **SC-005**: Targeted regression checks pass for 100% of manually resolved runtime overlaps and for the native-Windows, WSL2 fallback, provider-neutral connection, Cloud Shift, containment, conversation, notification, and Claude-app desk boundaries affected by synchronization.
- **SC-006**: The integrated candidate reports version 0.12.0 and completes at least one successful representative flow for setup/status, ordinary crew work, a running conversation, report delivery, and Orbit's Claude-app desk without loss of existing owner data.
- **SC-007**: Documentation review finds zero commands, prerequisites, account claims, platform claims, or version statements that contradict the integrated candidate.
- **SC-008**: Existing owner team data requires zero destructive migration, and validation leaves zero unintended changes in real owner data or credentials.
- **SC-009**: Every manually resolved overlap and every pending platform-specific check is traceable to a requirement and a recorded validation result; no unavailable check is counted as passed.
- **SC-010**: A maintainer can identify and restore the complete pre-synchronization local baseline within 5 minutes using the preserved recovery point.
- **SC-011**: Independent review confirms that the final content includes both approved lines of work and that ancestry-only history cannot be mistaken for content integration.
- **SC-012**: Zero destructive remote operations occur without an explicit owner publication decision made after validation results are available.

## Assumptions

- Canonical upstream 0.12.0 is the fixed target for this synchronization; later upstream releases will be handled separately.
- The local pre-synchronization baseline and a dedicated recovery reference remain available throughout the work.
- The local and upstream 0.8.0-era revisions represent the same product milestone even though their revision identities and a small set of local contents differ.
- Specifications 001, 002, and 003 are the authoritative descriptions of local native-Windows, Claude connection pass-through, and containment requirements; preservation does not imply every planned requirement is already implemented.
- Live owner team data is outside the repository integration surface and must not be used as disposable test data.
- The existing fork remote contains an earlier synchronization revision that records upstream ancestry but retains stale pre-synchronization content.
- A content-preserving local integration can be completed before deciding how the fork remote should be reconciled.

### Dependencies

- Read access to the complete local baseline, canonical upstream 0.12.0, their corresponding 0.8.0-era states, and the preserved recovery reference.
- The repository's existing automated tests, fixtures, cleanup support, and continuous-validation definitions.
- Supported macOS, Linux, WSL2, and native-Windows environments for the evidence each platform requires.
- Existing specifications, plans, contracts, and release gates for local safety-sensitive features.
- An explicit owner decision before any publication approach that would rewrite the fork's remote history.
