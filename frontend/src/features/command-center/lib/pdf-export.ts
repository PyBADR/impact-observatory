/**
 * PDF Export — Client-side scenario report generator
 *
 * Generates a professional institutional-grade PDF for the currently
 * active scenario using jsPDF + jspdf-autotable.
 *
 * 8 sections:
 * 1. Executive Briefing
 * 2. Macro Metrics
 * 3. Transmission Chain
 * 4. GCC Country Exposure
 * 5. Sector Impact Formula Lab
 * 6. Decision ROI
 * 7. Outcome Confirmation
 * 8. Audit / Sources / Confidence
 */

import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

import type { CommandCenterScenario, CommandCenterHeadline } from "./command-store";
import type {
  ExecutiveStatusResult,
  CountryBakeEntry,
  SectorFormulaResult,
  DecisionROIEntry,
  OutcomeConfirmation,
} from "./intelligence-engine";
import type { CausalStep } from "@/types/observatory";
import type { UnifiedScenarioRun } from "@/types/observatory";

// ── Formatting helpers ──

function fmtUsd(v: number): string {
  if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  return `$${v.toLocaleString()}`;
}

function fmtPct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

function safeStr(v: string | null | undefined, fallback = "—"): string {
  return v && v.length > 0 ? v : fallback;
}

// ── Colors ──

type RGB = [number, number, number];
const IO_DARK: RGB = [15, 23, 42];       // slate-900
const IO_ACCENT: RGB = [5, 102, 68];     // emerald-800
const IO_HEADER: RGB = [241, 245, 249];  // slate-100
const IO_BORDER: RGB = [203, 213, 225];  // slate-300
const IO_RED: RGB = [185, 28, 28];       // red-700

// ── Types for the export payload ──

export interface PdfExportPayload {
  scenario: CommandCenterScenario;
  headline: CommandCenterHeadline;
  narrativeEn: string;
  confidence: number;
  causalChain: CausalStep[];
  executiveStatus: ExecutiveStatusResult | null;
  countryBake: CountryBakeEntry[];
  sectorFormulas: SectorFormulaResult[];
  decisionROI: DecisionROIEntry[];
  outcomeConfirmation: OutcomeConfirmation | null;
  demoContract: UnifiedScenarioRun | null;
  sectorRollups: Record<string, { aggregate_stress?: number; total_loss?: number; stress?: number; loss_usd?: number }>;
}

// ── Section builder helpers ──

function addSectionTitle(doc: jsPDF, title: string, y: number): number {
  if (y > 260) {
    doc.addPage();
    y = 20;
  }
  doc.setFontSize(13);
  doc.setTextColor(...IO_ACCENT);
  doc.setFont("helvetica", "bold");
  doc.text(title, 14, y);
  doc.setDrawColor(...IO_BORDER);
  doc.line(14, y + 2, 196, y + 2);
  return y + 8;
}

function checkPage(doc: jsPDF, y: number, needed: number): number {
  if (y + needed > 280) {
    doc.addPage();
    return 20;
  }
  return y;
}

// ── Main export function ──

export function generateScenarioPdf(payload: PdfExportPayload): void {
  const {
    scenario,
    headline,
    narrativeEn,
    confidence,
    causalChain,
    executiveStatus,
    countryBake,
    sectorFormulas,
    decisionROI,
    outcomeConfirmation,
    demoContract,
    sectorRollups,
  } = payload;

  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  let y = 14;

  // ════════════════════════════════════════════════════════════════
  // COVER HEADER
  // ════════════════════════════════════════════════════════════════

  doc.setFillColor(...IO_DARK);
  doc.rect(0, 0, 210, 44, "F");

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text("IMPACT OBSERVATORY", 14, 12);
  doc.text("GCC Macro Financial Intelligence Platform", 14, 17);

  doc.setFontSize(16);
  doc.setFont("helvetica", "bold");
  const titleLines = doc.splitTextToSize(scenario.label, 140);
  doc.text(titleLines, 14, 28);

  // Right side — run metadata
  doc.setFontSize(8);
  doc.setFont("helvetica", "normal");
  doc.text(new Date().toISOString().slice(0, 19).replace("T", " "), 196, 12, { align: "right" });
  doc.text(`Confidence: ${(confidence * 100).toFixed(0)}%`, 196, 17, { align: "right" });
  if (demoContract?.runId) {
    doc.text(`Run: ${demoContract.runId.slice(0, 24)}`, 196, 22, { align: "right" });
  }
  doc.text(`Domain: ${scenario.domain}`, 196, 27, { align: "right" });

  y = 52;

  // ════════════════════════════════════════════════════════════════
  // 1. EXECUTIVE BRIEFING
  // ════════════════════════════════════════════════════════════════

  y = addSectionTitle(doc, "1. Executive Briefing", y);

  // Narrative
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(...IO_DARK);
  const narrativeLines = doc.splitTextToSize(safeStr(narrativeEn, "No briefing available."), 178);
  doc.text(narrativeLines, 14, y);
  y += narrativeLines.length * 4.2 + 4;

  // Headline metrics table
  y = checkPage(doc, y, 20);
  autoTable(doc, {
    startY: y,
    head: [["Headline Loss", "Avg Stress", "Propagation Depth", "Peak Day", "Nodes Impacted", "Recovery Days"]],
    body: [[
      fmtUsd(headline.totalLossUsd),
      `${(headline.averageStress * 100).toFixed(0)}%`,
      String(headline.propagationDepth),
      `Day ${headline.peakDay}`,
      String(headline.nodesImpacted),
      String(headline.maxRecoveryDays),
    ]],
    theme: "grid",
    styles: { fontSize: 8, cellPadding: 2.5 },
    headStyles: { fillColor: IO_HEADER, textColor: IO_DARK, fontStyle: "bold" },
    margin: { left: 14, right: 14 },
  });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  y = (doc as any).lastAutoTable.finalY + 8;

  // ════════════════════════════════════════════════════════════════
  // 2. MACRO METRICS — Executive Status
  // ════════════════════════════════════════════════════════════════

  y = checkPage(doc, y, 30);
  y = addSectionTitle(doc, "2. Macro Metrics — Executive Decision Status", y);

  if (executiveStatus) {
    autoTable(doc, {
      startY: y,
      head: [["Status", "Urgency", "Decision Window", "Affected Countries", "Affected Sectors"]],
      body: [[
        executiveStatus.status,
        executiveStatus.decisionUrgency,
        `${executiveStatus.decisionUrgencyHours}h`,
        executiveStatus.affectedCountries.join(", "),
        executiveStatus.affectedSectors.join(", "),
      ]],
      theme: "grid",
      styles: { fontSize: 8, cellPadding: 2.5 },
      headStyles: { fillColor: IO_HEADER, textColor: IO_DARK, fontStyle: "bold" },
      margin: { left: 14, right: 14 },
    });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    y = (doc as any).lastAutoTable.finalY + 4;

    doc.setFontSize(8);
    doc.setTextColor(...IO_DARK);
    const rationaleLines = doc.splitTextToSize(`Rationale: ${executiveStatus.severityRationale}`, 178);
    doc.text(rationaleLines, 14, y);
    y += rationaleLines.length * 3.5 + 6;
  } else {
    doc.setFontSize(8);
    doc.text("Executive status not computed for this scenario.", 14, y);
    y += 8;
  }

  // ════════════════════════════════════════════════════════════════
  // 3. TRANSMISSION CHAIN
  // ════════════════════════════════════════════════════════════════

  y = checkPage(doc, y, 30);
  y = addSectionTitle(doc, "3. Transmission Chain", y);

  if (causalChain.length > 0) {
    autoTable(doc, {
      startY: y,
      head: [["Step", "Entity", "Event", "Impact (USD)", "Stress \u0394", "Mechanism"]],
      body: causalChain.map((s) => [
        String(s.step),
        s.entity_label,
        s.event,
        fmtUsd(s.impact_usd),
        `+${(s.stress_delta * 100).toFixed(1)}%`,
        s.mechanism,
      ]),
      theme: "grid",
      styles: { fontSize: 7, cellPadding: 2 },
      headStyles: { fillColor: IO_HEADER, textColor: IO_DARK, fontStyle: "bold" },
      columnStyles: { 0: { cellWidth: 10 }, 3: { halign: "right" }, 4: { halign: "right" } },
      margin: { left: 14, right: 14 },
    });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    y = (doc as any).lastAutoTable.finalY + 8;
  } else {
    doc.setFontSize(8);
    doc.text("No transmission chain data available.", 14, y);
    y += 8;
  }

  // ════════════════════════════════════════════════════════════════
  // 4. GCC COUNTRY EXPOSURE
  // ════════════════════════════════════════════════════════════════

  y = checkPage(doc, y, 30);
  y = addSectionTitle(doc, "4. GCC Country Exposure", y);

  if (countryBake.length > 0) {
    autoTable(doc, {
      startY: y,
      head: [["Country", "Exposure (USD)", "Stress", "Primary Sector", "Driver", "Transmission", "Policy Lever"]],
      body: countryBake.map((c) => [
        c.name,
        fmtUsd(c.exposureUsd),
        fmtPct(c.stressPercent / 100),
        c.primarySector,
        c.primaryDriver,
        c.transmissionChannel,
        c.policyLever,
      ]),
      theme: "grid",
      styles: { fontSize: 7, cellPadding: 2 },
      headStyles: { fillColor: IO_HEADER, textColor: IO_DARK, fontStyle: "bold" },
      columnStyles: { 1: { halign: "right" }, 2: { halign: "right" } },
      margin: { left: 14, right: 14 },
    });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    y = (doc as any).lastAutoTable.finalY + 8;
  } else {
    doc.setFontSize(8);
    doc.text("Country exposure data not available.", 14, y);
    y += 8;
  }

  // ════════════════════════════════════════════════════════════════
  // 5. SECTOR IMPACT FORMULA LAB
  // ════════════════════════════════════════════════════════════════

  y = checkPage(doc, y, 30);
  y = addSectionTitle(doc, "5. Sector Impact — Formula Lab", y);

  if (sectorFormulas.length > 0) {
    autoTable(doc, {
      startY: y,
      head: [["Sector", "Loss (USD)", "Allocation", "Sensitivity", "Propagation Wt", "Confidence"]],
      body: sectorFormulas.map((s) => [
        s.sectorLabel,
        fmtUsd(s.sectorLoss),
        fmtPct(s.allocationWeight),
        s.scenarioSensitivity.toFixed(2),
        s.propagationWeight.toFixed(2),
        fmtPct(s.confidence),
      ]),
      theme: "grid",
      styles: { fontSize: 7, cellPadding: 2 },
      headStyles: { fillColor: IO_HEADER, textColor: IO_DARK, fontStyle: "bold" },
      columnStyles: { 1: { halign: "right" }, 2: { halign: "right" }, 3: { halign: "right" }, 4: { halign: "right" }, 5: { halign: "right" } },
      margin: { left: 14, right: 14 },
    });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    y = (doc as any).lastAutoTable.finalY + 8;
  } else if (Object.keys(sectorRollups).length > 0) {
    // Fallback: use sectorRollups
    autoTable(doc, {
      startY: y,
      head: [["Sector", "Stress", "Loss (USD)"]],
      body: Object.entries(sectorRollups).map(([sector, data]) => [
        sector,
        fmtPct(data.aggregate_stress ?? data.stress ?? 0),
        fmtUsd(data.total_loss ?? data.loss_usd ?? 0),
      ]),
      theme: "grid",
      styles: { fontSize: 8, cellPadding: 2.5 },
      headStyles: { fillColor: IO_HEADER, textColor: IO_DARK, fontStyle: "bold" },
      margin: { left: 14, right: 14 },
    });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    y = (doc as any).lastAutoTable.finalY + 8;
  } else {
    doc.setFontSize(8);
    doc.text("Sector formula data not available.", 14, y);
    y += 8;
  }

  // ════════════════════════════════════════════════════════════════
  // 6. DECISION ROI
  // ════════════════════════════════════════════════════════════════

  y = checkPage(doc, y, 30);
  y = addSectionTitle(doc, "6. Decision ROI Analysis", y);

  if (decisionROI.length > 0) {
    autoTable(doc, {
      startY: y,
      head: [["#", "Action", "Owner", "Cost", "Loss Avoided", "Net Benefit", "ROI", "Deadline"]],
      body: decisionROI.map((d, i) => [
        String(i + 1),
        d.action.slice(0, 50),
        d.owner,
        fmtUsd(d.costUsd),
        fmtUsd(d.lossAvoidedUsd),
        fmtUsd(d.netBenefit),
        `${d.roiMultiple.toFixed(1)}x`,
        `${d.deadlineHours}h`,
      ]),
      theme: "grid",
      styles: { fontSize: 7, cellPadding: 2 },
      headStyles: { fillColor: IO_HEADER, textColor: IO_DARK, fontStyle: "bold" },
      columnStyles: { 3: { halign: "right" }, 4: { halign: "right" }, 5: { halign: "right" }, 6: { halign: "right" }, 7: { halign: "right" } },
      margin: { left: 14, right: 14 },
    });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    y = (doc as any).lastAutoTable.finalY + 8;
  } else {
    doc.setFontSize(8);
    doc.text("Decision ROI data not available.", 14, y);
    y += 8;
  }

  // ════════════════════════════════════════════════════════════════
  // 7. OUTCOME CONFIRMATION
  // ════════════════════════════════════════════════════════════════

  y = checkPage(doc, y, 30);
  y = addSectionTitle(doc, "7. Outcome Confirmation — Counterfactual", y);

  if (outcomeConfirmation) {
    const oc = outcomeConfirmation;
    autoTable(doc, {
      startY: y,
      head: [["Scenario", "Projected Loss (Low)", "Projected Loss (High)", "Recovery Days"]],
      body: [
        [
          "Without Intervention",
          fmtUsd(oc.withoutAction.projectedLossLow),
          fmtUsd(oc.withoutAction.projectedLossHigh),
          String(oc.withoutAction.recoveryDays),
        ],
        [
          "Coordinated Response",
          fmtUsd(oc.coordinatedResponse.projectedLossLow),
          fmtUsd(oc.coordinatedResponse.projectedLossHigh),
          String(oc.coordinatedResponse.recoveryDays),
        ],
      ],
      theme: "grid",
      styles: { fontSize: 8, cellPadding: 2.5 },
      headStyles: { fillColor: IO_HEADER, textColor: IO_DARK, fontStyle: "bold" },
      columnStyles: { 1: { halign: "right" }, 2: { halign: "right" }, 3: { halign: "right" } },
      margin: { left: 14, right: 14 },
    });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    y = (doc as any).lastAutoTable.finalY + 4;

    doc.setFontSize(8);
    doc.setTextColor(...IO_RED);
    doc.text(`Expected Loss Reduction: ${fmtUsd(oc.expectedLossReduction)} (${fmtPct(oc.expectedLossReductionPercent)})`, 14, y);
    y += 4;
    doc.setTextColor(...IO_DARK);
    doc.text(`Recovery Horizon Reduction: ${oc.recoveryHorizonReduction} days`, 14, y);
    y += 8;
  } else {
    doc.setFontSize(8);
    doc.text("Outcome confirmation data not available.", 14, y);
    y += 8;
  }

  // ════════════════════════════════════════════════════════════════
  // 8. AUDIT / SOURCES / CONFIDENCE
  // ════════════════════════════════════════════════════════════════

  y = checkPage(doc, y, 40);
  y = addSectionTitle(doc, "8. Audit Trail — Sources & Confidence", y);

  const auditRows: string[][] = [];
  auditRows.push(["Scenario ID", scenario.templateId]);
  auditRows.push(["Run ID", demoContract?.runId ?? "—"]);
  auditRows.push(["Mode", demoContract?.mode ?? "—"]);
  auditRows.push(["Data Source", demoContract?.dataSourceType ?? "—"]);
  auditRows.push(["Generated At", demoContract?.generatedAt ?? new Date().toISOString()]);
  auditRows.push(["Pipeline Confidence", `${(confidence * 100).toFixed(0)}%`]);
  auditRows.push(["Provenance", (demoContract?.provenance ?? []).join(" → ")]);
  auditRows.push(["Scenario Complete", demoContract?.isScenarioComplete ? "Yes" : "No"]);
  if (demoContract?.fallbackStatus && demoContract.fallbackStatus !== "none") {
    auditRows.push(["Fallback Status", demoContract.fallbackStatus]);
  }

  autoTable(doc, {
    startY: y,
    body: auditRows,
    theme: "plain",
    styles: { fontSize: 8, cellPadding: 2 },
    columnStyles: { 0: { fontStyle: "bold", cellWidth: 40, textColor: IO_ACCENT } },
    margin: { left: 14, right: 14 },
  });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  y = (doc as any).lastAutoTable.finalY + 6;

  // Footer disclaimer
  y = checkPage(doc, y, 15);
  doc.setFontSize(7);
  doc.setTextColor(148, 163, 184); // slate-400
  doc.text(
    "This report is generated by Impact Observatory — a macro-financial simulation platform for the GCC region.",
    14, y
  );
  doc.text(
    "Data is for analytical purposes only and does not constitute financial advice.",
    14, y + 3.5
  );

  // ── Save ──
  const safeName = scenario.templateId.replace(/[^a-zA-Z0-9_-]/g, "_");
  doc.save(`impact-observatory-${safeName}-${new Date().toISOString().slice(0, 10)}.pdf`);
}
