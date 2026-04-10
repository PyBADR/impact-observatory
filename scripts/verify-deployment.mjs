#!/usr/bin/env node
/**
 * ─────────────────────────────────────────────────────────────────────────────
 * Impact Observatory | مرصد الأثر — Deployment Auto-Verification Script
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Layer:      Governance (L7) — CI/CD Observability
 * Purpose:    Validates that a Vercel production deployment matches the
 *             expected GitHub commit SHA and reaches READY state.
 *
 * Usage:
 *   VERCEL_TOKEN=xxx VERCEL_PROJECT_ID=yyy node scripts/verify-deployment.mjs [--commit <sha>] [--timeout 300] [--poll 15]
 *
 * Environment:
 *   VERCEL_TOKEN        — Vercel API bearer token           (required)
 *   VERCEL_PROJECT_ID   — Vercel project ID                 (required)
 *   VERCEL_TEAM_ID      — Vercel team/org ID                (optional)
 *   PRODUCTION_URL      — Production URL for health check   (optional, default: https://deevo-sim.vercel.app)
 *   GITHUB_SHA          — Commit SHA to verify against      (optional, overridden by --commit)
 *
 * Exit codes:
 *   0 — Deployment verified: SHA match + READY state + health OK
 *   1 — Verification failed: mismatch, timeout, or health failure
 *   2 — Configuration error: missing secrets or bad arguments
 *
 * Audit trail:
 *   Every verification run emits a structured JSON log line with SHA-256
 *   fingerprint for compliance traceability (PDPL / IFRS 17 audit chain).
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { createHash } from "node:crypto";

// ── Configuration ────────────────────────────────────────────────────────────

const VERCEL_API = "https://api.vercel.com";

function loadConfig() {
  const args = process.argv.slice(2);
  const flagIndex = (flag) => args.indexOf(flag);

  const commitIdx = flagIndex("--commit");
  const timeoutIdx = flagIndex("--timeout");
  const pollIdx = flagIndex("--poll");

  const config = {
    vercelToken: process.env.VERCEL_TOKEN,
    projectId: process.env.VERCEL_PROJECT_ID,
    teamId: process.env.VERCEL_TEAM_ID || null,
    expectedSha: (commitIdx !== -1 ? args[commitIdx + 1] : null) || process.env.GITHUB_SHA || null,
    productionUrl: process.env.PRODUCTION_URL || "https://deevo-sim.vercel.app",
    timeoutSeconds: parseInt((timeoutIdx !== -1 ? args[timeoutIdx + 1] : null) || "300", 10),
    pollIntervalSeconds: parseInt((pollIdx !== -1 ? args[pollIdx + 1] : null) || "15", 10),
    slackWebhookUrl: process.env.SLACK_WEBHOOK_URL || null,
  };

  if (!config.vercelToken) {
    console.error("✗ VERCEL_TOKEN is required. Set it as an environment variable or GitHub Secret.");
    process.exit(2);
  }
  if (!config.projectId) {
    console.error("✗ VERCEL_PROJECT_ID is required. Set it as an environment variable or GitHub Secret.");
    process.exit(2);
  }

  return config;
}

// ── Logging ──────────────────────────────────────────────────────────────────

const LOG_PREFIX = "[deploy-verify]";

function log(level, message, data = {}) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    service: "deployment-verifier",
    message,
    ...data,
  };
  const line = JSON.stringify(entry);
  if (level === "error") {
    console.error(`${LOG_PREFIX} ${line}`);
  } else {
    console.log(`${LOG_PREFIX} ${line}`);
  }
}

function sha256(input) {
  return createHash("sha256").update(input).digest("hex");
}

function emitAuditRecord(result) {
  const payload = JSON.stringify(result);
  const fingerprint = sha256(payload);
  log("info", "AUDIT_RECORD", { ...result, sha256_fingerprint: fingerprint });
  return fingerprint;
}

// ── Vercel API Client ────────────────────────────────────────────────────────

async function vercelFetch(path, config) {
  const url = new URL(path, VERCEL_API);
  if (config.teamId) {
    url.searchParams.set("teamId", config.teamId);
  }

  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${config.vercelToken}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Vercel API ${response.status}: ${body}`);
  }

  return response.json();
}

/**
 * Fetch the latest production deployment for the project.
 * Vercel's list-deployments endpoint returns newest-first.
 */
async function getLatestProductionDeployment(config) {
  const data = await vercelFetch(
    `/v6/deployments?projectId=${config.projectId}&target=production&limit=5&state=READY,BUILDING,QUEUED,ERROR`,
    config
  );

  if (!data.deployments || data.deployments.length === 0) {
    return null;
  }

  return data.deployments[0];
}

/**
 * Fetch a specific deployment by ID for detailed status.
 */
async function getDeployment(deploymentId, config) {
  return vercelFetch(`/v13/deployments/${deploymentId}`, config);
}

// ── Health Check ─────────────────────────────────────────────────────────────

async function checkProductionHealth(url) {
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: { "Cache-Control": "no-cache" },
      redirect: "follow",
    });

    return {
      healthy: response.ok,
      statusCode: response.status,
      headers: {
        server: response.headers.get("server"),
        cacheControl: response.headers.get("cache-control"),
        xVercelId: response.headers.get("x-vercel-id"),
      },
    };
  } catch (err) {
    return {
      healthy: false,
      statusCode: 0,
      error: err.message,
    };
  }
}

// ── Notification (Optional Slack) ────────────────────────────────────────────

async function notifySlack(webhookUrl, payload) {
  if (!webhookUrl) return;

  try {
    await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    log("info", "Slack notification sent");
  } catch (err) {
    log("warn", "Slack notification failed", { error: err.message });
  }
}

function buildSlackMessage(result) {
  const icon = result.verified ? "✅" : "🚨";
  const status = result.verified ? "VERIFIED" : "FAILED";

  return {
    text: `${icon} Deployment ${status} — Impact Observatory`,
    blocks: [
      {
        type: "header",
        text: { type: "plain_text", text: `${icon} Deployment ${status}` },
      },
      {
        type: "section",
        fields: [
          { type: "mrkdwn", text: `*Expected SHA:*\n\`${result.expectedSha || "N/A"}\`` },
          { type: "mrkdwn", text: `*Deployed SHA:*\n\`${result.deployedSha || "N/A"}\`` },
          { type: "mrkdwn", text: `*Deployment ID:*\n\`${result.deploymentId || "N/A"}\`` },
          { type: "mrkdwn", text: `*State:*\n${result.deploymentState}` },
          { type: "mrkdwn", text: `*Health:*\n${result.healthCheck?.healthy ? "OK" : "FAIL"}` },
          { type: "mrkdwn", text: `*URL:*\n${result.deploymentUrl || "N/A"}` },
        ],
      },
    ],
  };
}

// ── Polling Loop ─────────────────────────────────────────────────────────────

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForDeployment(config) {
  const deadline = Date.now() + config.timeoutSeconds * 1000;
  let attempt = 0;

  log("info", "Waiting for production deployment", {
    expectedSha: config.expectedSha,
    timeoutSeconds: config.timeoutSeconds,
    pollIntervalSeconds: config.pollIntervalSeconds,
  });

  while (Date.now() < deadline) {
    attempt++;
    log("info", `Poll attempt ${attempt}`);

    const deployment = await getLatestProductionDeployment(config);

    if (!deployment) {
      log("warn", "No deployments found for project", { projectId: config.projectId });
      await sleep(config.pollIntervalSeconds * 1000);
      continue;
    }

    const deployedSha = deployment.meta?.githubCommitSha || deployment.gitSource?.sha || null;
    const state = (deployment.state || deployment.readyState || "UNKNOWN").toUpperCase();

    log("info", "Deployment found", {
      deploymentId: deployment.uid,
      state,
      deployedSha: deployedSha?.substring(0, 7),
      createdAt: new Date(deployment.created).toISOString(),
    });

    // If we have an expected SHA and it doesn't match, check if this is an old deployment
    if (config.expectedSha && deployedSha && !deployedSha.startsWith(config.expectedSha.substring(0, 7))) {
      // The latest deployment is for a different commit — still waiting
      if (state === "READY" || state === "ERROR") {
        log("info", "Latest deployment is for a different commit, waiting for new deployment...", {
          expected: config.expectedSha.substring(0, 7),
          found: deployedSha.substring(0, 7),
        });
        await sleep(config.pollIntervalSeconds * 1000);
        continue;
      }
    }

    // Deployment is still building — wait
    if (state === "BUILDING" || state === "QUEUED" || state === "INITIALIZING") {
      log("info", "Deployment in progress, waiting...", { state });
      await sleep(config.pollIntervalSeconds * 1000);
      continue;
    }

    // Terminal states
    if (state === "ERROR" || state === "CANCELED") {
      return {
        verified: false,
        deploymentId: deployment.uid,
        deployedSha,
        expectedSha: config.expectedSha,
        deploymentState: state,
        deploymentUrl: deployment.url ? `https://${deployment.url}` : null,
        reason: `Deployment reached terminal state: ${state}`,
        healthCheck: null,
      };
    }

    // State is READY — validate
    if (state === "READY") {
      // SHA comparison
      let shaMatch = true;
      if (config.expectedSha && deployedSha) {
        shaMatch = deployedSha.startsWith(config.expectedSha) || config.expectedSha.startsWith(deployedSha);
      }

      // Health check
      const health = await checkProductionHealth(config.productionUrl);

      const verified = shaMatch && health.healthy;

      return {
        verified,
        deploymentId: deployment.uid,
        deployedSha,
        expectedSha: config.expectedSha,
        deploymentState: state,
        deploymentUrl: deployment.url ? `https://${deployment.url}` : null,
        shaMatch,
        healthCheck: health,
        reason: !shaMatch
          ? `SHA mismatch: expected ${config.expectedSha?.substring(0, 7)}, got ${deployedSha?.substring(0, 7)}`
          : !health.healthy
            ? `Health check failed: HTTP ${health.statusCode}`
            : "All checks passed",
      };
    }

    // Unknown state — wait
    log("warn", `Unknown deployment state: ${state}, waiting...`);
    await sleep(config.pollIntervalSeconds * 1000);
  }

  // Timeout
  return {
    verified: false,
    deploymentId: null,
    deployedSha: null,
    expectedSha: config.expectedSha,
    deploymentState: "TIMEOUT",
    deploymentUrl: null,
    reason: `Timed out after ${config.timeoutSeconds}s waiting for deployment`,
    healthCheck: null,
  };
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║   Impact Observatory — Deployment Auto-Verification        ║");
  console.log("║   Layer: Governance (L7) · CI/CD Observability             ║");
  console.log("╚══════════════════════════════════════════════════════════════╝");
  console.log();

  const config = loadConfig();

  log("info", "Verification started", {
    projectId: config.projectId,
    expectedSha: config.expectedSha?.substring(0, 7) || "any",
    productionUrl: config.productionUrl,
  });

  // ── Run verification loop ──
  const result = await waitForDeployment(config);

  // ── Emit audit record ──
  const fingerprint = emitAuditRecord({
    action: "deployment_verification",
    timestamp: new Date().toISOString(),
    ...result,
  });

  // ── Print summary ──
  console.log();
  console.log("┌──────────────────────────────────────────────────────────────┐");
  console.log("│  DEPLOYMENT VERIFICATION REPORT                             │");
  console.log("├──────────────────────────────────────────────────────────────┤");
  console.log(`│  Expected SHA:     ${(config.expectedSha || "any (no constraint)").padEnd(40)}│`);
  console.log(`│  Deployed SHA:     ${(result.deployedSha || "N/A").padEnd(40)}│`);
  console.log(`│  Deployment ID:    ${(result.deploymentId || "N/A").padEnd(40)}│`);
  console.log(`│  State:            ${result.deploymentState.padEnd(40)}│`);
  console.log(`│  SHA Match:        ${String(result.shaMatch ?? "N/A").padEnd(40)}│`);
  console.log(`│  Health Check:     ${(result.healthCheck?.healthy ? `OK (HTTP ${result.healthCheck.statusCode})` : result.healthCheck ? `FAIL (HTTP ${result.healthCheck.statusCode})` : "SKIPPED").padEnd(40)}│`);
  console.log(`│  Deployment URL:   ${(result.deploymentUrl || "N/A").padEnd(40)}│`);
  console.log(`│  Audit Fingerprint:${fingerprint.substring(0, 40).padEnd(40)}│`);
  console.log("├──────────────────────────────────────────────────────────────┤");

  if (result.verified) {
    console.log("│  ✓ RESULT: DEPLOYMENT VERIFIED                              │");
  } else {
    console.log("│  ✗ RESULT: VERIFICATION FAILED                              │");
    console.log(`│  Reason: ${result.reason.padEnd(51)}│`);
  }

  console.log("└──────────────────────────────────────────────────────────────┘");
  console.log();

  // ── Optional Slack notification ──
  if (config.slackWebhookUrl) {
    await notifySlack(config.slackWebhookUrl, buildSlackMessage(result));
  }

  // ── GitHub Actions output ──
  if (process.env.GITHUB_OUTPUT) {
    const { appendFileSync } = await import("node:fs");
    const outputs = [
      `verified=${result.verified}`,
      `deployment_id=${result.deploymentId || ""}`,
      `deployed_sha=${result.deployedSha || ""}`,
      `deployment_state=${result.deploymentState}`,
      `deployment_url=${result.deploymentUrl || ""}`,
      `sha_match=${result.shaMatch ?? ""}`,
      `health_status=${result.healthCheck?.healthy ?? ""}`,
      `audit_fingerprint=${fingerprint}`,
    ];
    for (const output of outputs) {
      appendFileSync(process.env.GITHUB_OUTPUT, `${output}\n`);
    }
    log("info", "GitHub Actions outputs written");
  }

  // ── Exit ──
  process.exit(result.verified ? 0 : 1);
}

main().catch((err) => {
  log("error", "Fatal error during verification", { error: err.message, stack: err.stack });
  process.exit(1);
});
