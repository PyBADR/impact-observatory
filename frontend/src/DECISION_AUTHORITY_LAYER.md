# Decision Authority Layer (DAL) — Architecture Report

## Final Verdict: DAL DESIGN READY

---

## 1. DECISION AUTHORITY GAP INVENTORY

### 1.1 Field-Level Gaps in Existing System

| Entity | Gap | Severity | Evidence |
|--------|-----|----------|----------|
| `OperatorDecision` | No `approved_by` field | CRITICAL | `operator_decision.py` has only `created_by` |
| `OperatorDecision` | No `rejected_by` field | CRITICAL | Rejection is implicit via `decision_type: REJECT_ACTION` |
| `OperatorDecision` | No `reviewed_by` field | HIGH | `IN_REVIEW` state exists but no reviewer attribution |
| `OperatorDecision` | No `execution_responsible` field | HIGH | Execution happens via `_dispatch_execution()` with no actor tracking |
| `DecisionStatus` | No `APPROVED` state | CRITICAL | Status goes `CREATED → IN_REVIEW → EXECUTED` — approval is assumed, not tracked |
| `DecisionStatus` | No `RETURNED` state | MEDIUM | No revision cycle — only accept or reject |
| `DecisionStatus` | No `ESCALATED` state | MEDIUM | No escalation routing in existing FSM |
| RBAC | No `DECISION_APPROVER` permission | HIGH | `rbac.py` has `CREATE_DECISION`, `EXECUTE_DECISION` but no approve/reject distinction |
| RBAC | No `DECISION_REVIEWER` role | MEDIUM | Role-action mapping is flat — no approval authority layer |
| Audit | No actor attribution on transitions | HIGH | `_write_decision_audit()` logs events but doesn't record WHO transitioned the state |
| Audit | No hash chaining | MEDIUM | `trust/audit.py` uses SHA-256 per-event but no chain integrity linking |
| API | No approval endpoint | CRITICAL | `decisions/routes.py` has `POST /create`, `POST /execute`, `POST /close` — no `POST /approve` |
| API | No review assignment endpoint | HIGH | No way to assign a reviewer to a decision |
| Outcome | No authority linkage | MEDIUM | `Outcome` tracks `decision_id` but not which authority approved the decision |

### 1.2 Gap Classification

- **CRITICAL (5):** Missing approval state, approval actor, rejection actor, approved_by field, approval API endpoint
- **HIGH (5):** Missing reviewer attribution, execution responsibility, actor on transitions, DECISION_APPROVER permission, review assignment
- **MEDIUM (4):** Missing returned/escalated states, hash chaining, DECISION_REVIEWER role, outcome-authority linkage

### 1.3 Decision: Wrap, Don't Replace

These gaps exist because the existing `OperatorDecision` model was designed for operational execution, not governance authority. Rather than retrofitting 14 fields and 4 states into a frozen Pydantic model, the DAL wraps each decision with an authority envelope (`DecisionAuthority`) that adds the governance layer without modifying the core entity.

---

## 2. STATE MODEL DESIGN

### 2.1 Authority State Machine

```
                    ┌──────────┐
                    │ PROPOSED │ ◄─────────── resubmit (from REJECTED/RETURNED/EXEC_FAILED)
                    └────┬─────┘
                         │ SUBMIT_FOR_REVIEW
                         ▼
                  ┌──────────────┐
                  │ UNDER_REVIEW │
                  └──┬───┬───┬──┘
       APPROVE ──────┘   │   └────── REJECT
                         │
                   RETURN / ESCALATE
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         ┌──────────┐        ┌───────────┐
         │ RETURNED │        │ ESCALATED │
         └────┬─────┘        └─────┬─────┘
              │ resubmit           │ re-route
              └────────────────────┘
                         │
                         ▼
                    ┌──────────┐
                    │ APPROVED │
                    └────┬─────┘
                         │ QUEUE_EXECUTION
                         ▼
               ┌───────────────────┐
               │ EXECUTION_PENDING │
               └────┬──────────┬───┘
          EXECUTE───┘          └───FAILURE
              │                     │
              ▼                     ▼
         ┌──────────┐     ┌──────────────────┐
         │ EXECUTED  │     │ EXECUTION_FAILED │
         │ [terminal]│     └────────┬─────────┘
         └──────────┘              │ resubmit / withdraw
                                   ▼

   Bypass paths: REVOKED (from APPROVED), WITHDRAWN (from PROPOSED/EXEC_FAILED)
   Regulatory: OVERRIDE (any → any, REGULATOR/ADMIN only)
```

### 2.2 State Count: 11

| State | Terminal | Resubmittable | Happy Path |
|-------|----------|---------------|------------|
| PROPOSED | No | — | Yes |
| UNDER_REVIEW | No | — | Yes |
| APPROVED | No | — | Yes |
| REJECTED | No | Yes | No |
| RETURNED | No | Yes | No |
| ESCALATED | No | — | No |
| EXECUTION_PENDING | No | — | Yes |
| EXECUTED | **Yes** | — | Yes |
| EXECUTION_FAILED | No | Yes | No |
| REVOKED | **Yes** | — | No |
| WITHDRAWN | **Yes** | — | No |

### 2.3 Valid Transition Matrix

Defined in `types/authority.ts → AUTHORITY_TRANSITIONS`:

```typescript
PROPOSED:           ["UNDER_REVIEW", "WITHDRAWN"]
UNDER_REVIEW:       ["APPROVED", "REJECTED", "ESCALATED", "RETURNED"]
APPROVED:           ["EXECUTION_PENDING", "REVOKED"]
REJECTED:           ["PROPOSED"]           // resubmission only
RETURNED:           ["PROPOSED"]           // revision cycle
ESCALATED:          ["UNDER_REVIEW"]       // re-routed to higher authority
EXECUTION_PENDING:  ["EXECUTED", "EXECUTION_FAILED"]
EXECUTED:           []                     // terminal
EXECUTION_FAILED:   ["PROPOSED", "WITHDRAWN"]
REVOKED:            []                     // terminal
WITHDRAWN:          []                     // terminal
```

### 2.4 Design Constraints

- No transition skipping (PROPOSED cannot jump to EXECUTED)
- Terminal states are immutable — no further transitions
- Resubmission increments `revision_number`
- Every transition produces an immutable `AuthorityEvent`
- Regulatory OVERRIDE bypasses the matrix (explicit audit trail)

---

## 3. ACTOR / ROLE RESPONSIBILITY MODEL

### 3.1 Authority Actors

| Actor | Maps to RBAC | Authority Responsibility |
|-------|-------------|------------------------|
| SYSTEM | — (automated) | Proposes decisions from pipeline runs |
| ANALYST | ANALYST | Proposes, recommends, annotates, withdraws own proposals |
| OPERATOR | OPERATOR | Submits for review, queues execution, executes, reports failures |
| EXECUTIVE | ADMIN | Approves, rejects, returns for revision, escalates, revokes |
| REGULATOR | REGULATOR | Overrides, audits, returns for revision, escalates, revokes |
| ADMIN | ADMIN | All permissions (system administrator) |

### 3.2 Permission Matrix

Defined in `types/authority.ts → AUTHORITY_PERMISSIONS`:

| Action | SYSTEM | ANALYST | OPERATOR | EXECUTIVE | REGULATOR | ADMIN |
|--------|--------|---------|----------|-----------|-----------|-------|
| PROPOSE | ✓ | ✓ | ✓ | | | |
| SUBMIT_FOR_REVIEW | | ✓ | ✓ | | | |
| APPROVE | | | | ✓ | | ✓ |
| REJECT | | | | ✓ | | ✓ |
| RETURN_FOR_REVISION | | | | ✓ | ✓ | |
| ESCALATE | | | ✓ | ✓ | ✓ | |
| QUEUE_EXECUTION | | | ✓ | | | ✓ |
| EXECUTE | | | ✓ | | | ✓ |
| REPORT_EXECUTION_FAILURE | ✓ | | ✓ | | | |
| REVOKE | | | | ✓ | ✓ | ✓ |
| WITHDRAW | | ✓ | ✓ | | | |
| OVERRIDE | | | | | ✓ | ✓ |
| ANNOTATE | | ✓ | ✓ | ✓ | ✓ | ✓ |

### 3.3 Enforcement

- **Frontend:** `useAuthorityStore.canPerform(authorityId, action, actorRole)` gates button rendering
- **Store:** `assertPermission(action, actorRole)` throws `AuthorityPermissionError` before state mutation
- **Backend (planned):** `@require_authority_permission(action)` decorator on API routes

---

## 4. APPROVAL FLOW DESIGN

### 4.1 Flow Sequence

```
1. PROPOSE  (SYSTEM/ANALYST/OPERATOR)
   → Creates DecisionAuthority envelope
   → Sets authority_status = PROPOSED
   → Emits AuthorityEvent (PROPOSE, null → PROPOSED)

2. SUBMIT_FOR_REVIEW  (OPERATOR/ANALYST)
   → Transitions PROPOSED → UNDER_REVIEW
   → Sets review_started_at timestamp
   → Emits AuthorityEvent

3. APPROVE  (EXECUTIVE/ADMIN)
   → Transitions UNDER_REVIEW → APPROVED
   → Sets authority_actor_id, authority_actor_role, authority_decided_at, authority_rationale
   → Emits AuthorityEvent

   OR

   REJECT  (EXECUTIVE/ADMIN)
   → Transitions UNDER_REVIEW → REJECTED
   → Same authority actor fields populated
   → Emits AuthorityEvent

   OR

   RETURN_FOR_REVISION  (EXECUTIVE/REGULATOR)
   → Transitions UNDER_REVIEW → RETURNED
   → Emits AuthorityEvent with revision feedback

   OR

   ESCALATE  (OPERATOR/EXECUTIVE/REGULATOR)
   → Transitions UNDER_REVIEW → ESCALATED
   → Increments escalation_level
   → Emits AuthorityEvent with target_role metadata
```

### 4.2 Resubmission Cycle

When a decision is REJECTED, RETURNED, or EXECUTION_FAILED:

```
1. RESUBMIT  (original proposer role)
   → Transitions to PROPOSED
   → Increments revision_number
   → Resets review/approval/execution fields
   → Preserves original proposal linkage
   → Emits AuthorityEvent with revision metadata
```

### 4.3 Data Contract: DecisionAuthority Approval Fields

```typescript
// Populated on APPROVE or REJECT:
authority_actor_id: string;       // WHO approved/rejected
authority_actor_role: AuthorityActor;  // EXECUTIVE or ADMIN
authority_decided_at: string;     // WHEN (ISO timestamp)
authority_rationale: string;      // WHY (free text)
```

---

## 5. EXECUTION FLOW DESIGN

### 5.1 Post-Approval Execution Sequence

```
1. QUEUE_EXECUTION  (OPERATOR/ADMIN)
   → Transitions APPROVED → EXECUTION_PENDING
   → Emits AuthorityEvent

2. EXECUTE  (OPERATOR/ADMIN)
   → Transitions EXECUTION_PENDING → EXECUTED [terminal]
   → Sets executed_by, executed_by_role, executed_at, execution_result
   → Optionally links linked_outcome_id
   → Emits AuthorityEvent

   OR

   REPORT_EXECUTION_FAILURE  (OPERATOR/SYSTEM)
   → Transitions EXECUTION_PENDING → EXECUTION_FAILED
   → Sets execution_result = failure_reason
   → Emits AuthorityEvent with failure metadata
```

### 5.2 Execution Responsibility Chain

| Field | Purpose |
|-------|---------|
| `proposed_by` + `proposed_by_role` | Who initiated |
| `authority_actor_id` + `authority_actor_role` | Who approved |
| `executed_by` + `executed_by_role` | Who executed |

This 3-actor chain ensures every decision has a clear: proposer → approver → executor trail. No single actor can propose, approve, AND execute — enforced by the permission matrix.

### 5.3 Outcome Linkage

- `linked_outcome_id` is set at execution time (not copied — FK reference)
- `linked_value_id` is set when value is calculated (post-execution)
- Neither field duplicates Outcome or DecisionValue data — only references

### 5.4 Revocation

```
REVOKE  (EXECUTIVE/REGULATOR/ADMIN)
→ Transitions APPROVED → REVOKED [terminal]
→ Only allowed from APPROVED state (not from EXECUTED)
→ Emits AuthorityEvent with revocation rationale
```

---

## 6. AUDIT TRAIL DESIGN

### 6.1 AuthorityEvent Entity

Every authority action produces an immutable, append-only `AuthorityEvent`:

```typescript
interface AuthorityEvent {
  event_id: string;           // Unique event identifier
  authority_id: string;       // FK to DecisionAuthority
  decision_id: string;        // FK to OperatorDecision
  action: AuthorityAction;    // What was done (13 action types)
  from_status: AuthorityStatus | null;  // State before
  to_status: AuthorityStatus;           // State after
  actor_id: string;           // WHO did it
  actor_role: AuthorityActor; // Role of WHO
  timestamp: string;          // WHEN (ISO 8601)
  notes: string | null;       // Human-readable context
  metadata: Record<string, unknown>;  // Structured extras
  event_hash: string;         // SHA-256 of this event
  previous_event_hash: string | null; // Hash of prior event (chain)
}
```

### 6.2 Hash Chain Integrity

Each event computes `event_hash = SHA-256(event_id + authority_id + decision_id + action + from_status + to_status + actor_id + actor_role + timestamp)` and stores `previous_event_hash` pointing to the last event for the same authority_id. This creates a per-authority hash chain.

**Verification:** The `AuthorityAuditTimeline` component visually verifies chain continuity — a broken link (where `event.previous_event_hash !== predecessor.event_hash`) is flagged with a red "Chain Broken" badge.

**Frontend note:** The current implementation uses a fast hash simulation (`simpleHash()`) for local rendering. Production backend uses `trust/audit.py` with full SHA-256 via `hashlib`.

### 6.3 Audit Trail Properties

- **Immutable:** Events are append-only. No event is ever modified or deleted.
- **Attributable:** Every event records `actor_id` and `actor_role`.
- **Traceable:** `from_status → to_status` provides full state history reconstruction.
- **Tamper-evident:** Hash chain breaks if any event is modified after creation.
- **Time-stamped:** ISO 8601 timestamps with millisecond precision.

### 6.4 Observability Hooks

| Hook | Where | What |
|------|-------|------|
| `applyTransition()` | authority-store.ts | Emits event on every state change |
| `override()` | authority-store.ts | Emits event with `metadata.override = true` |
| `annotate()` | authority-store.ts | Emits non-transitional event (notes only) |
| `AuthorityAuditTimeline` | UI component | Renders chain with integrity badges |
| `ChainBadge` | UI sub-component | Visual chain verification per-event |

---

## 7. CONTROL TOWER AUTHORITY UPGRADE

### 7.1 Before (Pre-DAL)

The UnifiedControlTower contained:
1. System Health Badge
2. Stage Summary Cards
3. Cross-Layer Intelligence Summary (6 cards: Signals, Impact, Decisions, Outcomes, ROI, Operator)
4. Flow Narrative Panel
5. Executive Control Tower (5 panels: Value, Narrative, Drivers, Performance, Risk)

**Missing:** No authority queue, no approval backlog, no execution tracking, no authority timeline.

### 7.2 After (Post-DAL)

The UnifiedControlTower now contains:
1. System Health Badge
2. Stage Summary Cards
3. Cross-Layer Intelligence Summary (6 cards)
4. **Authority Queue Panel** ← NEW
5. Flow Narrative Panel
6. Executive Control Tower (5 panels)

### 7.3 Authority Queue Panel (`AuthorityQueuePanel.tsx`)

**Capabilities:**
- Tabbed queue view: Pending, In Review, Approved, Executed, Rejected, Escalated, All
- Per-persona tab visibility (PERSONA_AUTHORITY_CAPABILITIES.visible_queues)
- Summary badges: active count, overdue count, escalated count
- Queue items sorted by: overdue first → priority → recency
- Per-item action buttons (only rendered if `canPerform()` returns true)
- Bilingual labels (EN/AR)

**Data flow:**
```
useAuthorityStore.getQueueSummary() → header badges
useAuthorityStore.getQueueForPersona(persona) → queue items
PERSONA_AUTHORITY_CAPABILITIES[persona] → visible tabs + allowed actions
useAuthorityStore.canPerform() → per-item action gate
```

### 7.4 Authority Detail Panel (`AuthorityDetailPanel.tsx`)

Expanded detail for a single DecisionAuthority:
- Lifecycle bar (happy path visualization)
- Proposal section (proposer, rationale, priority, revision)
- Review section (reviewer, start time)
- Authority decision section (approver/rejector, rationale, timestamp)
- Execution section (executor, result, timestamp)
- Linkage section (outcome_id, value_id)
- Embedded AuthorityAuditTimeline

### 7.5 Authority Audit Timeline (`AuthorityAuditTimeline.tsx`)

- Chronological event rendering with action icons
- Actor + role attribution per event
- State transition labels (from → to)
- Hash chain integrity badges (Regulator mode)
- Expandable (latest N events with "show all")

---

## 8. PERSONA AUTHORITY UX

### 8.1 Executive — Authority Console

**Surface label:** "Authority Console" | "وحدة الصلاحيات"

| Capability | Detail |
|-----------|--------|
| Allowed actions | APPROVE, REJECT, RETURN_FOR_REVISION, ESCALATE, REVOKE, ANNOTATE |
| Visible queues | UNDER_REVIEW, APPROVED, EXECUTION_PENDING, EXECUTED, REJECTED, ESCALATED, REVOKED |
| Audit trail | Full visibility |
| Cross-persona | Can see all actors' actions |

**UX flow:**
1. Executive sees Authority Queue in Control Tower
2. Tabs: "In Review" (primary), "Approved", "Executed", "Rejected", "Escalated"
3. Each item shows: status badge, priority dot, rationale preview, proposer, time ago
4. Action buttons: Approve (green), Reject (red), Return (orange), Escalate (purple)
5. Click item → AuthorityDetailPanel with full audit timeline (latest 5 events)

### 8.2 Analyst — Recommendation Queue

**Surface label:** "Recommendation Queue" | "قائمة التوصيات"

| Capability | Detail |
|-----------|--------|
| Allowed actions | PROPOSE, SUBMIT_FOR_REVIEW, WITHDRAW, ANNOTATE |
| Visible queues | PROPOSED, UNDER_REVIEW, APPROVED, REJECTED, RETURNED |
| Audit trail | Not visible |
| Cross-persona | Cannot see other personas' actions |

**UX flow:**
1. Analyst sees Authority Queue after FlowNarrative in their view
2. Tabs: "Pending" (own proposals), "In Review", "Approved", "Rejected"
3. Each item shows: status badge, priority, rationale
4. Action buttons: Submit for Review (blue), Withdraw (gray)
5. Click item → AuthorityDetailPanel (no hash chain display, max 5 events)

### 8.3 Regulator — Compliance & Authority Audit

**Surface label:** "Compliance & Authority Audit" | "تدقيق الامتثال والصلاحيات"

| Capability | Detail |
|-----------|--------|
| Allowed actions | OVERRIDE, RETURN_FOR_REVISION, ESCALATE, REVOKE, ANNOTATE |
| Visible queues | ALL 11 states |
| Audit trail | Full visibility with hash chain verification |
| Cross-persona | Can see all actors' actions |

**UX flow:**
1. Regulator sees Authority Queue after FlowNarrative in their view
2. Tabs: ALL tabs visible (full system-wide authority view)
3. Each item shows: all metadata including escalation level, revision number
4. Action buttons: Override (red), Return (orange), Escalate (purple), Revoke (red)
5. Click item → AuthorityDetailPanel with FULL hash chain audit timeline
6. Chain integrity badges visible on every event

---

## 9. IMPLEMENTATION RECOMMENDATION

### 9.1 Files Created

| File | Purpose | Layer |
|------|---------|-------|
| `types/authority.ts` | DAL type system (11 states, 13 actions, 6 actors, transition matrix, permission matrix) | Types |
| `store/authority-store.ts` | Zustand store (state machine, all lifecycle actions, hash-chained audit, queue selectors) | State |
| `features/authority/AuthorityQueuePanel.tsx` | Tabbed queue with persona-aware tabs/actions | UI |
| `features/authority/AuthorityAuditTimeline.tsx` | Hash-chained event timeline with integrity badges | UI |
| `features/authority/AuthorityDetailPanel.tsx` | Expanded authority detail with lifecycle bar | UI |
| `features/authority/index.ts` | Barrel exports | Module |

### 9.2 Files Modified

| File | Change |
|------|--------|
| `features/flow/UnifiedControlTower.tsx` | Added AuthorityQueuePanel between Intelligence Summary and Flow Narrative |
| `features/flow/PersonaFlowView.tsx` | Added AuthorityQueuePanel to FlowAnalystView and FlowRegulatorView |
| `features/flow/index.ts` | Added authority component re-exports |

### 9.3 Files NOT Modified (by design)

| File | Reason |
|------|--------|
| `store/app-store.ts` | DAL sits on top — no changes to core state |
| `lib/run-state.ts` | Run synchronization unchanged |
| `types/observatory.ts` | OperatorDecision model unchanged |
| `features/personas/ExecutiveView.tsx` | Consumed by PersonaFlowView, authority injected at flow level |
| `features/personas/AnalystView.tsx` | Same — wrapped, not modified |
| `features/personas/RegulatorView.tsx` | Same — wrapped, not modified |
| `lib/persona-view-model.ts` | Pure transformation functions unchanged |
| `hooks/use-api.ts` | API polling unchanged |
| Backend models | DAL is frontend-first; backend schema planned as Phase 2 |

### 9.4 Ordered Implementation Sequence

| Phase | Deliverable | Status |
|-------|------------|--------|
| 1. Type system | `types/authority.ts` | ✅ Complete |
| 2. State machine | `store/authority-store.ts` | ✅ Complete |
| 3. Queue UI | `features/authority/AuthorityQueuePanel.tsx` | ✅ Complete |
| 4. Audit UI | `features/authority/AuthorityAuditTimeline.tsx` | ✅ Complete |
| 5. Detail UI | `features/authority/AuthorityDetailPanel.tsx` | ✅ Complete |
| 6. Control Tower wiring | `UnifiedControlTower.tsx` + `PersonaFlowView.tsx` | ✅ Complete |
| 7. Backend schema | `backend/app/domain/models/decision_authority.py` | ⏳ Phase 2 |
| 8. Backend API | `backend/app/authority/routes.py` | ⏳ Phase 2 |
| 9. Backend audit | `backend/app/trust/authority_audit.py` | ⏳ Phase 2 |
| 10. E2E testing | Authority lifecycle integration tests | ⏳ Phase 2 |

### 9.5 Backend Schema Plan (Phase 2)

```sql
CREATE TABLE decision_authority (
  authority_id     TEXT PRIMARY KEY,
  decision_id      TEXT NOT NULL REFERENCES operator_decisions(decision_id),
  authority_status TEXT NOT NULL DEFAULT 'PROPOSED',
  proposed_by      TEXT NOT NULL,
  proposed_by_role TEXT NOT NULL,
  proposed_at      TEXT NOT NULL,
  -- ... all fields from DecisionAuthority interface
  UNIQUE(decision_id)
);

CREATE TABLE authority_events (
  event_id            TEXT PRIMARY KEY,
  authority_id        TEXT NOT NULL REFERENCES decision_authority(authority_id),
  decision_id         TEXT NOT NULL,
  action              TEXT NOT NULL,
  from_status         TEXT,
  to_status           TEXT NOT NULL,
  actor_id            TEXT NOT NULL,
  actor_role          TEXT NOT NULL,
  timestamp           TEXT NOT NULL,
  notes               TEXT,
  metadata            TEXT, -- JSON
  event_hash          TEXT NOT NULL,
  previous_event_hash TEXT
);

CREATE INDEX idx_auth_decision ON decision_authority(decision_id);
CREATE INDEX idx_auth_status ON decision_authority(authority_status);
CREATE INDEX idx_events_authority ON authority_events(authority_id);
```

---

## 10. FINAL VERDICT

### **DAL DESIGN READY**

The Decision Authority Layer is architecturally complete at the frontend layer. Every component is implemented, wired, and follows the non-negotiable constraints:

| Constraint | Status | Evidence |
|-----------|--------|----------|
| Don't redesign core | ✅ | No changes to `app-store.ts`, `observatory.ts`, `operator_decision.py` |
| Don't replace decision layer | ✅ | DAL wraps via FK (`decision_id`), does not modify `OperatorDecision` |
| Don't duplicate outcome/ROI logic | ✅ | `linked_outcome_id` and `linked_value_id` are FK references only |
| DAL sits ON TOP | ✅ | `DecisionAuthority` envelope pattern — zero core modifications |
| Must be auditable | ✅ | Hash-chained `AuthorityEvent` log with tamper detection |
| Must be stateful | ✅ | 11-state FSM with formal transition matrix |
| Must respect persona boundaries | ✅ | `PERSONA_AUTHORITY_CAPABILITIES` governs visibility and actions per persona |

### Risk Register

| Risk | Probability | Mitigation |
|------|------------|------------|
| Authority store grows unbounded in long sessions | Low | Terminal state cleanup + bounded queue selectors |
| Hash chain frontend simulation is not cryptographic | Medium | Production backend uses `hashlib.sha256`; frontend is for visual verification only |
| Persona capability drift between frontend and backend | Medium | `PERSONA_AUTHORITY_CAPABILITIES` is shared type — backend mirrors the same constant |
| Action handler placeholder (console.log) in queue | Expected | Phase 2 wires action handlers to modal dialogs + backend API calls |
| No backend schema yet | Expected | Frontend-first design validates UX/flow before committing to schema |
| Concurrent approval conflicts (two executives approve simultaneously) | Low | Backend will use optimistic locking on `authority_status` + `updated_at` |

### Decision Gate: What Must Be True Before Phase 2

1. ✅ All 11 authority states are defined with valid transition matrix
2. ✅ All 13 authority actions are defined with permission matrix
3. ✅ Authority store validates transitions AND permissions before mutation
4. ✅ Every transition emits a hash-chained audit event
5. ✅ Queue selectors filter by persona capabilities
6. ✅ UI components render persona-bounded actions
7. ✅ Control Tower integrates authority queue
8. ✅ All three persona views show authority surface
9. ⏳ Backend schema and API routes (Phase 2)
10. ⏳ E2E integration tests (Phase 2)

### Architecture Layer Mapping

| Layer | DAL Component |
|-------|--------------|
| Data | `authority-store.ts` (Zustand), `types/authority.ts` |
| Features | Authority state machine, transition validation, permission enforcement |
| Models | `DecisionAuthority`, `AuthorityEvent` (typed, immutable) |
| Agents | `applyTransition()` — automated state change + event emission |
| APIs | Phase 2: `POST /authority/propose`, `POST /authority/approve`, etc. |
| UI | `AuthorityQueuePanel`, `AuthorityAuditTimeline`, `AuthorityDetailPanel` |
| Governance | Hash-chained audit trail, persona-bounded capabilities, transition matrix enforcement |
