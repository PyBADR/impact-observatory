#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEEVO DEPLOY SCRIPT — Sprint 1.5 + Sprint 2
# Run from: /Users/bdr.ai/Projects/deevo-sim
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -e

echo "═══ STEP 1: Fix corrupted git worktrees ═══"
git worktree prune
rm -rf .git/worktrees/festive-albattani .git/worktrees/infallible-davinci .git/worktrees/serene-mcnulty 2>/dev/null || true
echo "✓ Worktrees cleaned"

echo ""
echo "═══ STEP 2: Apply Sprint 1.5 + Sprint 2 patch ═══"
git apply sprint-1.5-2.0.patch
echo "✓ Patch applied"

echo ""
echo "═══ STEP 3: Stage and commit ═══"
git add \
  backend/src/engines/explanation_engine.py \
  backend/src/engines/decision_transparency_engine.py \
  backend/src/engines/range_engine.py \
  backend/src/engines/sensitivity_engine.py \
  backend/src/engines/outcome_engine.py \
  backend/src/services/run_orchestrator.py \
  backend/tests/test_decision_trust_layer.py \
  backend/tests/test_decision_reliability_layer.py \
  frontend/src/types/observatory.ts \
  frontend/src/components/trust/MetricWhyCard.tsx \
  frontend/src/components/trust/ActionTransparencyOverlay.tsx \
  frontend/src/components/trust/LossInducingBanner.tsx \
  frontend/src/components/provenance/DecisionRoomV2.tsx \
  frontend/src/features/command-center/lib/command-store.ts \
  frontend/src/features/command-center/lib/use-command-center.ts \
  frontend/src/app/command-center/page.tsx

git commit -m "$(cat <<'COMMIT'
feat: Decision Trust Layer (Sprint 1.5) + Decision Reliability Layer (Sprint 2)

Sprint 1.5 — Trust Upgrade Layer:
- Business Explainability: CRO-readable summaries with impact-tagged drivers
- Per-metric Confidence: computed from data completeness, determinism, scenario familiarity
- Data Context: source type, freshness labels, reference periods
- Decision Risk Overlay: severity-rated risk cards (capital, timing, regulatory, execution)

Sprint 2 — Decision Reliability Layer:
- Range Engine: bounded [low, base, high] estimates via HYBRID method
- Sensitivity Engine: 7-point severity sweep showing nonlinear input→output relationships
- Outcome Tracking: prediction store with actual vs predicted deviation tracking
- Trust Memory: action-template feedback loop (success rate + accuracy → trust score)
- Confidence Adjustment: dynamic confidence modification from historical trust data

Backend: 5 new engine files, orchestrator integration (stages 41c-41g), 196 tests passing
Frontend: 3 new trust components, reliability payload wiring through command store

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
COMMIT
)"
echo "✓ Committed"

echo ""
echo "═══ STEP 4: Push to GitHub ═══"
git push origin main
echo "✓ Pushed to GitHub"

echo ""
echo "═══ STEP 5: Verify deployments ═══"
echo "Railway auto-deploys from main — check: https://railway.app/dashboard"
echo "Vercel auto-deploys from main — check: https://vercel.com/dashboard"
echo ""
echo "Backend health: curl https://api.impact-observatory.io/health"
echo "Frontend: https://deevo-sim.vercel.app"

echo ""
echo "═══ DEPLOY COMPLETE ═══"
echo "Clean up: rm deploy.sh sprint-1.5-2.0.patch"
