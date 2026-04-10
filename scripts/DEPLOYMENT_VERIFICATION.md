# Deployment Auto-Verification System

## Architecture Decision

**Layer:** Governance (L7) — CI/CD Observability  
**What:** Automated post-deployment verification pipeline that runs on every push to `main`, comparing GitHub commit SHAs with Vercel deployment SHAs and validating production health.  
**Why:** Manual deployment checks are error-prone and do not scale. This system provides deterministic, auditable verification with SHA-256 fingerprinted records for PDPL/IFRS 17 compliance traceability.

## Data Flow

```
GitHub Push (main)
    │
    ▼
GitHub Actions Trigger
    │
    ├──► Resolve commit SHA from $GITHUB_SHA
    │
    ├──► Wait 30s for Vercel webhook
    │
    ▼
verify-deployment.mjs
    │
    ├──► Poll Vercel API (GET /v6/deployments?target=production)
    │     └──► Extract: deployment.meta.githubCommitSha
    │
    ├──► Compare: GITHUB_SHA == deployed SHA
    │
    ├──► Check: deployment.state == "READY"
    │
    ├──► Health check: GET https://deevo-sim.vercel.app → HTTP 200
    │
    ├──► Emit: SHA-256 audit record (structured JSON)
    │
    └──► Output: verified | failed + exit code
         │
         ▼
smoke-test.mjs (on success)
    │
    ├──► Homepage loads with expected title
    ├──► Next.js markers present
    ├──► Static assets reachable
    ├──► Vercel headers present
    ├──► Key pages accessible (no 5xx)
    ├──► Response time < 10s
    └──► Content-Type is text/html
         │
         ▼
GitHub Actions Summary + Optional Slack
```

## Setup Guide

### 1. Required GitHub Secrets

Go to **Repository Settings → Secrets and variables → Actions** and add:

| Secret | Description | How to obtain |
|--------|-------------|---------------|
| `VERCEL_TOKEN` | Vercel API bearer token | Vercel Dashboard → Settings → Tokens → Create |
| `VERCEL_PROJECT_ID` | Vercel project identifier | Vercel Dashboard → Project → Settings → General → Project ID |

### 2. Optional GitHub Secrets

| Secret | Description |
|--------|-------------|
| `VERCEL_TEAM_ID` | Required if project is under a Vercel team (not personal) |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL for failure/success notifications |

### 3. Finding Your Vercel Project ID

```bash
# Option A: From the Vercel Dashboard
# Project → Settings → General → "Project ID"

# Option B: From the Vercel CLI
npx vercel link
cat .vercel/project.json
# Look for "projectId" field
```

### 4. Creating a Vercel Token

1. Go to https://vercel.com/account/tokens
2. Click "Create" 
3. Name: `github-deploy-verify`
4. Scope: Select only the relevant project (principle of least privilege)
5. Expiration: Set an appropriate TTL (90 days recommended, rotate before expiry)
6. Copy the token immediately — it will not be shown again

### 5. Optional: Slack Notifications

1. Go to https://api.slack.com/apps → Create New App → From Scratch
2. Enable "Incoming Webhooks" 
3. Add a webhook to a channel (e.g., `#deployments`)
4. Copy the webhook URL to `SLACK_WEBHOOK_URL` secret

## File Inventory

| File | Purpose |
|------|---------|
| `.github/workflows/verify-deployment.yml` | GitHub Actions workflow — orchestrates the full pipeline |
| `scripts/verify-deployment.mjs` | Core verification script — Vercel API polling + SHA comparison |
| `scripts/smoke-test.mjs` | Post-deployment smoke tests — page loads, assets, headers |
| `scripts/DEPLOYMENT_VERIFICATION.md` | This documentation file |

## How It Works

### Automatic Mode (default)

Every push to `main` triggers the workflow:

1. **Checkout + resolve SHA** — captures the exact commit that triggered the build
2. **30s initial delay** — gives Vercel time to receive the GitHub webhook and start building
3. **Polling loop** — calls Vercel API every 15s (configurable), up to 5 minutes (configurable):
   - Fetches latest production deployment
   - Checks if deployment SHA matches the pushed commit
   - Waits if deployment is still BUILDING/QUEUED
   - Fails if deployment reaches ERROR/CANCELED state
4. **SHA comparison** — verifies the deployed commit matches the expected commit
5. **Health check** — confirms the production URL returns HTTP 200
6. **Audit record** — emits a SHA-256 fingerprinted JSON log for compliance
7. **Smoke tests** — validates key pages and static assets load correctly
8. **Summary** — writes a formatted table to the GitHub Actions run summary

### Manual Mode

Trigger via **Actions → Verify Production Deployment → Run workflow**:

- Optionally specify a specific commit SHA to verify
- Optionally adjust the timeout (default: 300s)

### Local Execution

```bash
# Verify current production deployment
VERCEL_TOKEN=your_token \
VERCEL_PROJECT_ID=your_project_id \
node scripts/verify-deployment.mjs

# Verify a specific commit
VERCEL_TOKEN=your_token \
VERCEL_PROJECT_ID=your_project_id \
node scripts/verify-deployment.mjs --commit abc1234 --timeout 120

# Run smoke tests only
PRODUCTION_URL=https://deevo-sim.vercel.app \
node scripts/smoke-test.mjs
```

## Risk Register

| Failure Mode | Probability | Mitigation |
|-------------|-------------|------------|
| Vercel API rate limit hit during polling | Low | 15s poll interval keeps well under 60 req/min limit |
| Vercel deployment takes longer than timeout | Medium | Default 300s covers most builds; configurable via workflow_dispatch |
| Vercel webhook not received (deployment never starts) | Low | 30s initial delay + 300s timeout provides ample window |
| GitHub Secret rotation missed | Medium | Set 90-day TTL, add calendar reminder, Slack alert on auth failure |
| False positive (SHA matches but code is broken) | Low | Smoke tests validate actual page content and asset loading |
| Network failure during health check | Low | Retry is implicit via polling loop; health runs after READY state confirmed |

## Observability

- **Structured JSON logs** — every poll attempt and the final result are logged as parseable JSON
- **SHA-256 audit fingerprint** — each verification run produces a unique, tamper-evident fingerprint
- **GitHub Actions Step Summary** — human-readable table rendered in the Actions UI
- **GitHub Actions Outputs** — machine-readable outputs for downstream job consumption
- **Optional Slack** — real-time notifications on failure or success

## Decision Gate

Before considering this system operational, the following must be true:

- [ ] `VERCEL_TOKEN` and `VERCEL_PROJECT_ID` secrets are configured in GitHub
- [ ] A test push to `main` triggers the workflow and it completes successfully
- [ ] The verification report shows SHA match = true and state = READY
- [ ] Smoke tests pass with all checks green
- [ ] (Optional) Slack notifications are received on the target channel
