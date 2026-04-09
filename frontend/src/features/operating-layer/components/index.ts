/**
 * Operating Layer — Component Barrel
 *
 * Decision Operating Layer Phase 1:
 *   - DecisionAnchorCard: owner, type, deadline, tradeoffs
 *   - CounterfactualBlock: baseline vs recommended vs alternative outcomes
 *   - DecisionGatePanel: approval workflow, escalation triggers
 *   - OperatingLayerView: unified composition of all three
 */
export { DecisionAnchorCard } from "./DecisionAnchorCard";
export { CounterfactualBlock } from "./CounterfactualBlock";
export { DecisionGatePanel } from "./DecisionGatePanel";
export { OperatingLayerView } from "./OperatingLayerView";
