/**
 * Impact Observatory | مرصد الأثر — Decision Authority Layer (DAL) Types
 *
 * The authority model that governs WHO can do WHAT to decisions, and WHEN.
 *
 * This layer sits ON TOP of existing OperatorDecision entities.
 * It does NOT replace them. It wraps them with:
 *   - Formal authority lifecycle (PROPOSED → APPROVED → EXECUTED)
 *   - Actor-attributed state transitions
 *   - Approval/rejection metadata
 *   - Execution responsibility tracking
 *   - Full audit trail
 *
 * Design constraints:
 *   - Single source of truth: OperatorDecision.decision_id is the foreign key
 *   - No duplication of outcome or ROI logic
 *   - Persona-bounded authority (Executive approves, Analyst recommends, Regulator audits)
 *   - Every transition produces an immutable AuthorityEvent
 */

// ─── Authority Lifecycle States ─────────────────────────────────────────────

/**
 * The formal authority lifecycle for a decision.
 *
 * This is NOT the same as OperatorDecision.decision_status (CREATED/IN_REVIEW/EXECUTED/FAILED/CLOSED).
 * AuthorityStatus governs the GOVERNANCE envelope around decisions.
 *
 * Transition matrix:
 *   PROPOSED       → UNDER_REVIEW, WITHDRAWN
 *   UNDER_REVIEW   → APPROVED, REJECTED, ESCALATED, RETURNED
 *   APPROVED       → EXECUTION_PENDING, REVOKED
 *   REJECTED       → PROPOSED (resubmission only), [terminal]
 *   RETURNED       → PROPOSED (revision cycle)
 *   ESCALATED      → UNDER_REVIEW (re-routed to higher authority)
 *   EXECUTION_PENDING → EXECUTED, EXECUTION_FAILED
 *   EXECUTED       → [terminal — outcome layer takes over]
 *   EXECUTION_FAILED → PROPOSED (retry), WITHDRAWN
 *   REVOKED        → [terminal]
 *   WITHDRAWN      → [terminal]
 */
export type AuthorityStatus =
  | "PROPOSED"            // System or analyst submitted a decision for authority review
  | "UNDER_REVIEW"        // Active review by an authorized reviewer
  | "APPROVED"            // Authority granted — execution permitted
  | "REJECTED"            // Authority denied — cannot execute without resubmission
  | "RETURNED"            // Sent back for revision — not rejected, needs rework
  | "ESCALATED"           // Routed to higher authority (e.g., Regulator override)
  | "EXECUTION_PENDING"   // Approved and queued for execution
  | "EXECUTED"            // Terminal — authority lifecycle complete, outcome layer takes over
  | "EXECUTION_FAILED"    // Execution attempted but failed
  | "REVOKED"             // Previously approved, now revoked before execution
  | "WITHDRAWN";          // Proposer withdrew the decision

/** Terminal states — no further transitions allowed */
export const TERMINAL_AUTHORITY_STATES: AuthorityStatus[] = [
  "EXECUTED", "REVOKED", "WITHDRAWN",
];

/** States that allow resubmission to PROPOSED */
export const RESUBMITTABLE_STATES: AuthorityStatus[] = [
  "REJECTED", "RETURNED", "EXECUTION_FAILED",
];

// ─── Valid Transition Matrix ────────────────────────────────────────────────

export const AUTHORITY_TRANSITIONS: Record<AuthorityStatus, AuthorityStatus[]> = {
  PROPOSED:           ["UNDER_REVIEW", "WITHDRAWN"],
  UNDER_REVIEW:       ["APPROVED", "REJECTED", "ESCALATED", "RETURNED"],
  APPROVED:           ["EXECUTION_PENDING", "REVOKED"],
  REJECTED:           ["PROPOSED"],  // resubmission only
  RETURNED:           ["PROPOSED"],  // revision cycle
  ESCALATED:          ["UNDER_REVIEW"],  // re-routed to higher authority
  EXECUTION_PENDING:  ["EXECUTED", "EXECUTION_FAILED"],
  EXECUTED:           [],  // terminal
  EXECUTION_FAILED:   ["PROPOSED", "WITHDRAWN"],  // retry or abandon
  REVOKED:            [],  // terminal
  WITHDRAWN:          [],  // terminal
};

// ─── Authority Actors ───────────────────────────────────────────────────────

/**
 * Who is acting. Maps to backend RBAC roles but is explicit in the DAL.
 *
 * SYSTEM:     Automated pipeline (proposes decisions from run results)
 * ANALYST:    Human analyst (proposes, recommends, annotates)
 * OPERATOR:   Operational staff (submits for review, executes after approval)
 * EXECUTIVE:  Decision authority (approves, rejects, revokes)
 * REGULATOR:  Compliance authority (audits, overrides, escalation target)
 * ADMIN:      System administrator (all permissions)
 */
export type AuthorityActor =
  | "SYSTEM"
  | "ANALYST"
  | "OPERATOR"
  | "EXECUTIVE"
  | "REGULATOR"
  | "ADMIN";

// ─── Authority Action Types ─────────────────────────────────────────────────

/**
 * Every authority action that produces an audit event.
 */
export type AuthorityAction =
  | "PROPOSE"                // Submit decision for authority review
  | "SUBMIT_FOR_REVIEW"      // Move from PROPOSED to UNDER_REVIEW
  | "APPROVE"                // Grant execution authority
  | "REJECT"                 // Deny execution authority
  | "RETURN_FOR_REVISION"    // Send back with feedback
  | "ESCALATE"               // Route to higher authority
  | "QUEUE_EXECUTION"        // Move approved decision to execution queue
  | "EXECUTE"                // Perform the authorized action
  | "REPORT_EXECUTION_FAILURE" // Execution failed
  | "REVOKE"                 // Revoke previously granted authority
  | "WITHDRAW"               // Proposer withdraws decision
  | "OVERRIDE"               // Regulator override (bypasses normal flow)
  | "ANNOTATE";              // Add note without state change

// ─── Who Can Do What ────────────────────────────────────────────────────────

/**
 * Permission matrix: which actors can perform which authority actions.
 *
 * This is the HEART of the DAL. If an actor is not listed for an action,
 * the UI must not render the button and the backend must reject the request.
 */
export const AUTHORITY_PERMISSIONS: Record<AuthorityAction, AuthorityActor[]> = {
  PROPOSE:                  ["SYSTEM", "ANALYST", "OPERATOR"],
  SUBMIT_FOR_REVIEW:        ["OPERATOR", "ANALYST", "EXECUTIVE"],
  APPROVE:                  ["EXECUTIVE", "ADMIN"],
  REJECT:                   ["EXECUTIVE", "ADMIN"],
  RETURN_FOR_REVISION:      ["EXECUTIVE", "REGULATOR"],
  ESCALATE:                 ["OPERATOR", "EXECUTIVE", "REGULATOR"],
  QUEUE_EXECUTION:          ["OPERATOR", "ADMIN"],
  EXECUTE:                  ["OPERATOR", "ADMIN"],
  REPORT_EXECUTION_FAILURE: ["OPERATOR", "SYSTEM"],
  REVOKE:                   ["EXECUTIVE", "REGULATOR", "ADMIN"],
  WITHDRAW:                 ["ANALYST", "OPERATOR"],  // only proposer's role
  OVERRIDE:                 ["REGULATOR", "ADMIN"],
  ANNOTATE:                 ["ANALYST", "OPERATOR", "EXECUTIVE", "REGULATOR", "ADMIN"],
};

// ─── Authority Envelope ─────────────────────────────────────────────────────

/**
 * The authority envelope wrapping an existing OperatorDecision.
 * This is the DAL's primary entity. One per decision.
 */
export interface DecisionAuthority {
  /** Unique DAL envelope ID */
  authority_id: string;

  /** Foreign key to OperatorDecision.decision_id — the wrapped decision */
  decision_id: string;

  /** Current authority lifecycle state */
  authority_status: AuthorityStatus;

  // ── Proposal ──
  /** Who proposed this decision for authority review */
  proposed_by: string;
  /** Actor role of the proposer */
  proposed_by_role: AuthorityActor;
  /** When proposed */
  proposed_at: string;
  /** Proposer's justification */
  proposal_rationale: string | null;

  // ── Review ──
  /** Who is currently reviewing (null if not under review) */
  reviewer_id: string | null;
  /** Role of the reviewer */
  reviewer_role: AuthorityActor | null;
  /** When review started */
  review_started_at: string | null;

  // ── Approval / Rejection ──
  /** Who approved or rejected */
  authority_actor_id: string | null;
  /** Role of the authority actor */
  authority_actor_role: AuthorityActor | null;
  /** When authority decision was made */
  authority_decided_at: string | null;
  /** Authority's rationale for approval/rejection */
  authority_rationale: string | null;

  // ── Execution ──
  /** Who executed the decision */
  executed_by: string | null;
  /** Role of the executor */
  executed_by_role: AuthorityActor | null;
  /** When execution occurred */
  executed_at: string | null;
  /** Execution result summary */
  execution_result: string | null;

  // ── Linkage ──
  /** Linked outcome_id (from Outcome layer — NOT duplicated) */
  linked_outcome_id: string | null;
  /** Linked value_id (from DecisionValue layer — NOT duplicated) */
  linked_value_id: string | null;

  // ── Priority ──
  /** Authority priority level (1=highest, 5=lowest) */
  priority: 1 | 2 | 3 | 4 | 5;
  /** Deadline for authority action (ISO timestamp, null = no deadline) */
  authority_deadline: string | null;
  /** Is this decision overdue? */
  is_overdue: boolean;

  // ── Metadata ──
  /** Revision count (incremented on resubmission from REJECTED/RETURNED) */
  revision_number: number;
  /** Escalation level (0 = normal, 1+ = escalated) */
  escalation_level: number;
  /** Tags for filtering */
  tags: string[];

  // ── Timestamps ──
  created_at: string;
  updated_at: string;
}

// ─── Authority Audit Event ──────────────────────────────────────────────────

/**
 * Immutable audit event for every authority action.
 * One event per state transition. Append-only log.
 */
export interface AuthorityEvent {
  /** Unique event ID */
  event_id: string;

  /** FK to DecisionAuthority.authority_id */
  authority_id: string;

  /** FK to OperatorDecision.decision_id */
  decision_id: string;

  /** What action was taken */
  action: AuthorityAction;

  /** State BEFORE this action */
  from_status: AuthorityStatus | null;

  /** State AFTER this action */
  to_status: AuthorityStatus;

  /** Who performed the action */
  actor_id: string;

  /** Role of the actor */
  actor_role: AuthorityActor;

  /** When the action occurred */
  timestamp: string;

  /** Human-readable notes */
  notes: string | null;

  /** Structured metadata (e.g., escalation target, rejection reason codes) */
  metadata: Record<string, unknown>;

  /** SHA-256 hash of this event for tamper detection */
  event_hash: string;

  /** Hash of the previous event (chain integrity) */
  previous_event_hash: string | null;
}

// ─── Authority Queue Views ──────────────────────────────────────────────────

/** Summary counts for the Control Tower authority console */
export interface AuthorityQueueSummary {
  proposed: number;
  under_review: number;
  approved_pending_execution: number;
  executed: number;
  rejected: number;
  failed: number;
  escalated: number;
  overdue: number;
  total_active: number;
}

/** A single item in an authority queue (for rendering in lists) */
export interface AuthorityQueueItem {
  authority_id: string;
  decision_id: string;
  authority_status: AuthorityStatus;
  decision_type: string;
  proposed_by: string;
  proposed_by_role: AuthorityActor;
  proposed_at: string;
  priority: 1 | 2 | 3 | 4 | 5;
  is_overdue: boolean;
  rationale_preview: string | null;
  /** Denormalized from OperatorDecision for display (no re-fetch needed) */
  source_run_id: string | null;
  source_scenario_label: string | null;
  revision_number: number;
  escalation_level: number;
  /** Most recent authority actor (reviewer / approver / rejector) */
  last_authority_actor: string | null;
  last_authority_action: AuthorityAction | null;
  last_authority_at: string | null;
}

// ─── Persona Authority Capabilities ─────────────────────────────────────────

/** What a persona can SEE and DO on the authority layer */
export interface PersonaAuthorityCapabilities {
  /** Actions this persona can perform */
  allowed_actions: AuthorityAction[];
  /** Queue states this persona can view */
  visible_queues: AuthorityStatus[];
  /** Can this persona see the full audit trail? */
  can_view_audit_trail: boolean;
  /** Can this persona see other personas' actions? */
  can_view_cross_persona_actions: boolean;
  /** Label for this persona's authority surface */
  surface_label: string;
  surface_label_ar: string;
}

/** Persona capability definitions */
export const PERSONA_AUTHORITY_CAPABILITIES: Record<string, PersonaAuthorityCapabilities> = {
  executive: {
    allowed_actions: [
      "SUBMIT_FOR_REVIEW", "APPROVE", "REJECT", "RETURN_FOR_REVISION", "ESCALATE", "REVOKE", "ANNOTATE",
    ],
    visible_queues: [
      "PROPOSED", "UNDER_REVIEW", "APPROVED", "EXECUTION_PENDING", "EXECUTED",
      "REJECTED", "ESCALATED", "REVOKED",
    ],
    can_view_audit_trail: true,
    can_view_cross_persona_actions: true,
    surface_label: "Authority Console",
    surface_label_ar: "وحدة الصلاحيات",
  },
  analyst: {
    allowed_actions: [
      "PROPOSE", "SUBMIT_FOR_REVIEW", "WITHDRAW", "ANNOTATE",
    ],
    visible_queues: [
      "PROPOSED", "UNDER_REVIEW", "APPROVED", "REJECTED", "RETURNED",
    ],
    can_view_audit_trail: false,
    can_view_cross_persona_actions: false,
    surface_label: "Recommendation Queue",
    surface_label_ar: "قائمة التوصيات",
  },
  regulator: {
    allowed_actions: [
      "OVERRIDE", "RETURN_FOR_REVISION", "ESCALATE", "REVOKE", "ANNOTATE",
    ],
    visible_queues: [
      "PROPOSED", "UNDER_REVIEW", "APPROVED", "REJECTED", "RETURNED",
      "ESCALATED", "EXECUTION_PENDING", "EXECUTED", "EXECUTION_FAILED",
      "REVOKED", "WITHDRAWN",
    ],
    can_view_audit_trail: true,
    can_view_cross_persona_actions: true,
    surface_label: "Compliance & Authority Audit",
    surface_label_ar: "تدقيق الامتثال والصلاحيات",
  },
};
