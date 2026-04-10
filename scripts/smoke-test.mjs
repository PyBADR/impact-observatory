#!/usr/bin/env node
/**
 * ─────────────────────────────────────────────────────────────────────────────
 * Impact Observatory | مرصد الأثر — Production Smoke Test
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Layer:      Governance (L7) — Post-Deployment Validation
 * Purpose:    Verifies production endpoints return expected responses
 *             after a Vercel deployment is marked READY.
 *
 * Usage:
 *   PRODUCTION_URL=https://deevo-sim.vercel.app node scripts/smoke-test.mjs
 *
 * Exit codes:
 *   0 — All smoke tests passed
 *   1 — One or more smoke tests failed
 * ─────────────────────────────────────────────────────────────────────────────
 */

const PRODUCTION_URL = process.env.PRODUCTION_URL || "https://deevo-sim.vercel.app";

const tests = [];
let passed = 0;
let failed = 0;

function log(status, name, detail = "") {
  const icon = status === "pass" ? "✓" : "✗";
  console.log(`  ${icon} ${name}${detail ? ` — ${detail}` : ""}`);
}

async function runTest(name, fn) {
  try {
    await fn();
    passed++;
    log("pass", name);
    tests.push({ name, status: "pass" });
  } catch (err) {
    failed++;
    log("fail", name, err.message);
    tests.push({ name, status: "fail", error: err.message });
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

// ── Test Definitions ─────────────────────────────────────────────────────────

async function testHomepageLoads() {
  const res = await fetch(PRODUCTION_URL, { redirect: "follow" });
  assert(res.ok, `Expected 2xx, got ${res.status}`);
  const html = await res.text();
  assert(html.includes("Impact Observatory"), "Page title not found in HTML");
}

async function testHomepageContainsKeyContent() {
  const res = await fetch(PRODUCTION_URL);
  const html = await res.text();
  assert(html.includes("__NEXT_DATA__") || html.includes("_next/static"), "Missing Next.js markers");
}

async function testStaticAssetsLoad() {
  const res = await fetch(PRODUCTION_URL);
  const html = await res.text();

  // Extract first CSS or JS static asset path
  const assetMatch = html.match(/_next\/static\/[a-zA-Z0-9/_.-]+\.(js|css)/);
  assert(assetMatch, "No _next/static assets found in HTML");

  const assetUrl = `${PRODUCTION_URL}/${assetMatch[0]}`;
  const assetRes = await fetch(assetUrl);
  assert(assetRes.ok, `Static asset returned ${assetRes.status}: ${assetUrl}`);
}

async function testNoCacheHeaders() {
  const res = await fetch(PRODUCTION_URL, {
    headers: { "Cache-Control": "no-cache" },
  });
  // Vercel should serve with appropriate cache headers
  assert(res.ok, `Expected 2xx, got ${res.status}`);
  // Check x-vercel-id header exists (confirms Vercel is serving)
  const vercelId = res.headers.get("x-vercel-id");
  assert(vercelId, "Missing x-vercel-id header — response may not be from Vercel");
}

async function testMapPageLoads() {
  const res = await fetch(`${PRODUCTION_URL}/map`, { redirect: "follow" });
  // Next.js app router may return 200 or soft-navigate; either is fine
  assert(res.status < 500, `Map page returned server error: ${res.status}`);
}

async function testGraphExplorerPageLoads() {
  const res = await fetch(`${PRODUCTION_URL}/graph-explorer`, { redirect: "follow" });
  assert(res.status < 500, `Graph Explorer returned server error: ${res.status}`);
}

async function testResponseTime() {
  const start = Date.now();
  await fetch(PRODUCTION_URL);
  const elapsed = Date.now() - start;
  assert(elapsed < 10000, `Homepage took ${elapsed}ms (>10s threshold)`);
}

async function testSecurityHeaders() {
  const res = await fetch(PRODUCTION_URL);
  // Vercel adds some security headers by default
  const xFrame = res.headers.get("x-frame-options");
  const contentType = res.headers.get("content-type");
  assert(contentType && contentType.includes("text/html"), `Unexpected content-type: ${contentType}`);
}

// ── Runner ───────────────────────────────────────────────────────────────────

async function main() {
  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║   Impact Observatory — Production Smoke Tests               ║");
  console.log("╚══════════════════════════════════════════════════════════════╝");
  console.log();
  console.log(`  Target: ${PRODUCTION_URL}`);
  console.log();

  await runTest("Homepage returns 200 with expected title", testHomepageLoads);
  await runTest("Homepage contains Next.js markers", testHomepageContainsKeyContent);
  await runTest("Static assets are reachable", testStaticAssetsLoad);
  await runTest("Vercel headers present (x-vercel-id)", testNoCacheHeaders);
  await runTest("Map page accessible (no 5xx)", testMapPageLoads);
  await runTest("Graph Explorer accessible (no 5xx)", testGraphExplorerPageLoads);
  await runTest("Response time under 10s", testResponseTime);
  await runTest("Content-Type is text/html", testSecurityHeaders);

  console.log();
  console.log(`  Results: ${passed} passed, ${failed} failed, ${passed + failed} total`);
  console.log();

  // Write GitHub Actions summary if available
  if (process.env.GITHUB_STEP_SUMMARY) {
    const { appendFileSync } = await import("node:fs");
    let md = "## Smoke Test Results\n\n| Test | Status |\n|------|--------|\n";
    for (const t of tests) {
      md += `| ${t.name} | ${t.status === "pass" ? "✅" : "❌"} ${t.status === "fail" ? t.error : ""} |\n`;
    }
    md += `\n**${passed}/${passed + failed} passed**\n`;
    appendFileSync(process.env.GITHUB_STEP_SUMMARY, md);
  }

  if (failed > 0) {
    console.error("  Smoke tests FAILED — production may not be healthy.");
    process.exit(1);
  }

  console.log("  All smoke tests PASSED.");
  process.exit(0);
}

main().catch((err) => {
  console.error("Fatal error:", err.message);
  process.exit(1);
});
