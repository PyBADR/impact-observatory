const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat, ExternalHyperlink,
  TabStopType, TabStopPosition,
} = require("docx");

// ── Colors ──────────────────────────────────────────────────────────────
const NAVY = "0A1628";
const BLUE = "2563EB";
const DARK_BLUE = "1E3A5F";
const LIGHT_BG = "F0F4F8";
const ACCENT = "F59E0B";
const GREEN = "059669";
const RED = "DC2626";
const GRAY = "6B7280";
const WHITE = "FFFFFF";
const BORDER_COLOR = "D1D5DB";

// ── Reusable Elements ───────────────────────────────────────────────────
const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: BORDER_COLOR };
const borders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const noBorder = { style: BorderStyle.NONE, size: 0 };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

const CONTENT_WIDTH = 9360; // US Letter 1" margins

function spacer(pts = 120) {
  return new Paragraph({ spacing: { before: pts, after: pts }, children: [] });
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 32, color: NAVY })],
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 26, color: DARK_BLUE })],
  });
}

function heading3(text) {
  return new Paragraph({
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 22, color: BLUE })],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120, line: 276 },
    children: [new TextRun({ text, font: "Arial", size: 21, color: opts.color || "374151", ...opts })],
  });
}

function bodyBold(label, text) {
  return new Paragraph({
    spacing: { after: 100, line: 276 },
    children: [
      new TextRun({ text: label, font: "Arial", size: 21, bold: true, color: NAVY }),
      new TextRun({ text, font: "Arial", size: 21, color: "374151" }),
    ],
  });
}

function bulletItem(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { after: 60, line: 276 },
    children: [new TextRun({ text, font: "Arial", size: 21, color: "374151" })],
  });
}

function numberedItem(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "steps", level },
    spacing: { after: 80, line: 276 },
    children: [new TextRun({ text, font: "Arial", size: 21, color: "374151" })],
  });
}

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: NAVY, type: ShadingType.CLEAR },
    margins: cellMargins,
    verticalAlign: "center",
    children: [new Paragraph({ children: [new TextRun({ text, font: "Arial", size: 18, bold: true, color: WHITE })] })],
  });
}

function dataCell(text, width, opts = {}) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.shade ? { fill: opts.shade, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({
      children: [new TextRun({ text, font: "Arial", size: 18, color: opts.color || "374151", bold: opts.bold || false })],
    })],
  });
}

function accentBox(children) {
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    rows: [new TableRow({
      children: [new TableCell({
        borders: { top: noBorder, bottom: noBorder, right: noBorder,
          left: { style: BorderStyle.SINGLE, size: 12, color: BLUE } },
        width: { size: CONTENT_WIDTH, type: WidthType.DXA },
        shading: { fill: "EFF6FF", type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 200, right: 200 },
        children,
      })],
    })],
  });
}

function calloutBox(title, textContent, color = ACCENT) {
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    rows: [new TableRow({
      children: [new TableCell({
        borders: { top: { style: BorderStyle.SINGLE, size: 8, color },
          bottom: noBorder, left: noBorder, right: noBorder },
        width: { size: CONTENT_WIDTH, type: WidthType.DXA },
        shading: { fill: "FFFBEB", type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 200, right: 200 },
        children: [
          new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: title, font: "Arial", size: 20, bold: true, color })] }),
          new Paragraph({ children: [new TextRun({ text: textContent, font: "Arial", size: 19, color: "374151" })] }),
        ],
      })],
    })],
  });
}

// ── Build Document ──────────────────────────────────────────────────────

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: DARK_BLUE },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [
        { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "\u25E6", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
      ]},
      { reference: "steps", levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
      ]},
    ],
  },
  sections: [
    // ════════════════════════════════════════════════════════════════════
    // COVER PAGE
    // ════════════════════════════════════════════════════════════════════
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      children: [
        spacer(2400),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 80 },
          children: [new TextRun({ text: "IMPACT OBSERVATORY", font: "Arial", size: 44, bold: true, color: NAVY })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 40 },
          children: [new TextRun({ text: "\u0645\u0631\u0635\u062F \u0627\u0644\u0623\u062B\u0631", font: "Arial", size: 36, color: BLUE })],
        }),
        spacer(200),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 2, color: BLUE, space: 12 } },
          spacing: { before: 200, after: 200 },
          children: [new TextRun({ text: "GO-TO-MARKET STRATEGY", font: "Arial", size: 36, bold: true, color: DARK_BLUE })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "Enterprise Decision Intelligence for GCC Financial Infrastructure", font: "Arial", size: 22, color: GRAY })],
        }),
        spacer(800),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 60 },
          children: [new TextRun({ text: "CONFIDENTIAL", font: "Arial", size: 20, bold: true, color: RED })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 60 },
          children: [new TextRun({ text: "Deevo Analytics  |  April 2026", font: "Arial", size: 20, color: GRAY })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "v1.0  |  Chief GTM Strategist Brief", font: "Arial", size: 18, color: GRAY })],
        }),
      ],
    },

    // ════════════════════════════════════════════════════════════════════
    // MAIN CONTENT
    // ════════════════════════════════════════════════════════════════════
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1080, left: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: BORDER_COLOR, space: 4 } },
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
            children: [
              new TextRun({ text: "Impact Observatory  |  GTM Strategy", font: "Arial", size: 16, color: GRAY }),
              new TextRun({ text: "\tCONFIDENTIAL", font: "Arial", size: 16, color: RED, bold: true }),
            ],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            border: { top: { style: BorderStyle.SINGLE, size: 1, color: BORDER_COLOR, space: 4 } },
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
            children: [
              new TextRun({ text: "Deevo Analytics  |  April 2026", font: "Arial", size: 16, color: GRAY }),
              new TextRun({ text: "\tPage ", font: "Arial", size: 16, color: GRAY }),
              new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: GRAY }),
            ],
          })],
        }),
      },
      children: [

        // ── SECTION 1: EXECUTIVE POSITION ──────────────────────────────
        heading1("1. Executive Position"),

        accentBox([
          new Paragraph({ spacing: { after: 80 }, children: [
            new TextRun({ text: "One-Liner: ", font: "Arial", size: 21, bold: true, color: NAVY }),
            new TextRun({ text: "Impact Observatory is the first deterministic decision intelligence system purpose-built for GCC financial infrastructure risk. It models how a single event\u2014a Hormuz blockage, a banking liquidity shock, a cyber attack on SWIFT\u2014cascades across 42 interconnected nodes spanning 9 sectors, then generates ranked operator actions with regulatory risk scoring, IFRS 17 compliance, and SHA-256 audit trails.", font: "Arial", size: 21, color: "374151" }),
          ]})
        ]),

        spacer(80),
        body("This is not a dashboard. It is not a BI layer. It is a simulation engine with a 17-stage computational pipeline that produces auditable, deterministic outputs from scenario injection to decision recommendation. Every run is reproducible. Every number is traceable."),

        heading2("What We Sell"),
        body("We sell the answer to one question that every GCC central bank, insurer, sovereign fund, and systemically important bank needs answered but cannot answer today:"),

        accentBox([
          new Paragraph({ alignment: AlignmentType.CENTER, children: [
            new TextRun({ text: "\"If [scenario X] happens in the next 72 hours, which sectors cascade, what is the total loss exposure, and what actions should we take\u2014in what order\u2014to minimize systemic damage?\"", font: "Arial", size: 22, italics: true, color: DARK_BLUE }),
          ]}),
        ]),

        spacer(60),
        body("Nobody else answers this question for the GCC. Global risk platforms (Moody\u2019s, Bloomberg PORT, Verisk) model single-sector risk in Western markets. They do not model cross-sector cascade in a Hormuz-dependent, oil-denominated, IFRS 17-governed, Arabic-bilingual financial ecosystem."),

        heading2("Competitive Moat"),
        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2800, 3280, 3280],
          rows: [
            new TableRow({ children: [
              headerCell("Dimension", 2800),
              headerCell("Impact Observatory", 3280),
              headerCell("Global Incumbents", 3280),
            ]}),
            new TableRow({ children: [
              dataCell("Knowledge Graph", 2800, { bold: true }),
              dataCell("42-node GCC-native (Hormuz, Aramco, SAMA, Jebel Ali, SWIFT GCC, mada...)", 3280),
              dataCell("Generic global; GCC is a footnote", 3280),
            ]}),
            new TableRow({ children: [
              dataCell("Cascade Modeling", 2800, { bold: true, shade: LIGHT_BG }),
              dataCell("Cross-sector propagation: maritime \u2192 energy \u2192 banking \u2192 insurance \u2192 fintech", 3280, { shade: LIGHT_BG }),
              dataCell("Single-sector stress tests", 3280, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("Decision Layer", 2800, { bold: true }),
              dataCell("Ranked actions with owner, cost, loss avoided, regulatory risk, IFRS 17 flags", 3280),
              dataCell("Risk score only; no action generation", 3280),
            ]}),
            new TableRow({ children: [
              dataCell("Auditability", 2800, { bold: true, shade: LIGHT_BG }),
              dataCell("SHA-256 audit hash, deterministic pipeline, full trace ID per run", 3280, { shade: LIGHT_BG }),
              dataCell("Black-box ML models", 3280, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("Compliance", 2800, { bold: true }),
              dataCell("IFRS 17 native, PDPL-ready, GCC regulatory references in actions", 3280),
              dataCell("Western regulatory focus (Basel/Solvency II)", 3280),
            ]}),
            new TableRow({ children: [
              dataCell("Language", 2800, { bold: true, shade: LIGHT_BG }),
              dataCell("Arabic/English bilingual (labels, actions, narratives)", 3280, { shade: LIGHT_BG }),
              dataCell("English only", 3280, { shade: LIGHT_BG }),
            ]}),
          ],
        }),


        // ── SECTION 2: TARGET CUSTOMERS ────────────────────────────────
        new Paragraph({ children: [new PageBreak()] }),
        heading1("2. Target Customer Segments"),

        body("Three tiers, sequenced by conversion speed, deal size, and strategic leverage. Tier 1 accounts are the beachhead\u2014they have the clearest pain, the largest budgets, and the regulatory authority to mandate adoption downstream."),

        heading2("Tier 1: Regulators & Central Banks"),
        bodyBold("Pain: ", "No cross-sector systemic risk simulation exists for GCC. SAMA, CBUAE, and CBB rely on single-sector stress tests (Basel ICAAP) that cannot model how a Hormuz closure cascades from maritime through energy into banking liquidity and insurance claims simultaneously."),
        bodyBold("Budget: ", "$500K\u2013$2M annual for risk intelligence platforms. Procurement through direct RFP or national security advisory channel."),
        bodyBold("Decision Cycle: ", "6\u20139 months. Requires sandbox evaluation + technical audit."),

        heading3("Named Accounts"),
        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2200, 2200, 2400, 2560],
          rows: [
            new TableRow({ children: [
              headerCell("Entity", 2200), headerCell("Country", 2200),
              headerCell("Entry Point", 2400), headerCell("Scenario Hook", 2560),
            ]}),
            new TableRow({ children: [
              dataCell("SAMA", 2200, { bold: true }), dataCell("Saudi Arabia", 2200),
              dataCell("Financial Stability Dept.", 2400), dataCell("saudi_oil_shock + regional_liquidity_stress", 2560),
            ]}),
            new TableRow({ children: [
              dataCell("CBUAE", 2200, { bold: true, shade: LIGHT_BG }), dataCell("UAE", 2200, { shade: LIGHT_BG }),
              dataCell("Risk & Compliance Division", 2400, { shade: LIGHT_BG }), dataCell("uae_banking_crisis + hormuz_disruption", 2560, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("CBB", 2200, { bold: true }), dataCell("Bahrain", 2200),
              dataCell("Financial Stability Unit", 2400), dataCell("bahrain_sovereign_stress", 2560),
            ]}),
            new TableRow({ children: [
              dataCell("Insurance Authority (IA)", 2200, { bold: true, shade: LIGHT_BG }), dataCell("UAE", 2200, { shade: LIGHT_BG }),
              dataCell("Prudential Regulation", 2400, { shade: LIGHT_BG }), dataCell("IFRS 17 catastrophe reserving demo", 2560, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("CMA", 2200, { bold: true }), dataCell("Saudi Arabia", 2200),
              dataCell("Market Risk Division", 2400), dataCell("energy_market_volatility_shock", 2560),
            ]}),
          ],
        }),

        spacer(60),
        calloutBox("STRATEGIC LEVERAGE", "A single regulator adoption creates downstream mandated demand. If SAMA deploys Impact Observatory for systemic risk monitoring, every systemically important bank in Saudi Arabia needs compatible stress testing. This is the force multiplier.", BLUE),

        spacer(120),
        heading2("Tier 2: Sovereign Wealth Funds & National Oil Companies"),
        bodyBold("Pain: ", "Portfolio stress testing for GCC-specific geopolitical scenarios. PIF, ADIA, KIA, and QIA hold trillions in assets correlated to GCC infrastructure. They need to model what happens to their portfolio when Hormuz closes or energy prices crash."),
        bodyBold("Budget: ", "$300K\u2013$1.5M. Procurement through investment risk office or CRO."),
        bodyBold("Decision Cycle: ", "4\u20136 months. Faster if positioned as a scenario planning tool, not an IT procurement."),

        heading3("Named Accounts"),
        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2400, 2000, 2560, 2400],
          rows: [
            new TableRow({ children: [
              headerCell("Entity", 2400), headerCell("Country", 2000),
              headerCell("Entry Point", 2560), headerCell("Scenario Hook", 2400),
            ]}),
            new TableRow({ children: [
              dataCell("Public Investment Fund (PIF)", 2400, { bold: true }), dataCell("Saudi Arabia", 2000),
              dataCell("Risk Management Office", 2560), dataCell("saudi_oil_shock + iran_escalation", 2400),
            ]}),
            new TableRow({ children: [
              dataCell("ADIA", 2400, { bold: true, shade: LIGHT_BG }), dataCell("UAE", 2000, { shade: LIGHT_BG }),
              dataCell("Portfolio Risk Division", 2560, { shade: LIGHT_BG }), dataCell("hormuz_full_closure", 2400, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("KIA", 2400, { bold: true }), dataCell("Kuwait", 2000),
              dataCell("Strategic Planning", 2560), dataCell("kuwait_fiscal_shock", 2400),
            ]}),
            new TableRow({ children: [
              dataCell("Saudi Aramco", 2400, { bold: true, shade: LIGHT_BG }), dataCell("Saudi Arabia", 2000, { shade: LIGHT_BG }),
              dataCell("Enterprise Risk Mgmt", 2560, { shade: LIGHT_BG }), dataCell("hormuz + oil_shock supply chain", 2400, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("ADNOC", 2400, { bold: true }), dataCell("UAE", 2000),
              dataCell("Strategic Risk Office", 2560), dataCell("hormuz_chokepoint_disruption", 2400),
            ]}),
          ],
        }),

        spacer(120),
        heading2("Tier 3: Systemically Important Banks & Insurers"),
        bodyBold("Pain: ", "Basel III/IV stress testing is single-sector and backward-looking. Insurers face IFRS 17 compliance pressure with no GCC-specific catastrophe modeling tool. Both need forward-looking scenario simulation tied to GCC-specific threats."),
        bodyBold("Budget: ", "$150K\u2013$600K. Procurement through CRO or Head of Actuarial."),
        bodyBold("Decision Cycle: ", "3\u20136 months. Fastest tier if regulator is already using the platform (mandated compatibility)."),

        heading3("Named Accounts"),
        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2600, 1800, 2560, 2400],
          rows: [
            new TableRow({ children: [
              headerCell("Entity", 2600), headerCell("Country", 1800),
              headerCell("Entry Point", 2560), headerCell("Use Case", 2400),
            ]}),
            new TableRow({ children: [
              dataCell("First Abu Dhabi Bank (FAB)", 2600, { bold: true }), dataCell("UAE", 1800),
              dataCell("Group CRO", 2560), dataCell("Cross-sector stress test", 2400),
            ]}),
            new TableRow({ children: [
              dataCell("Saudi National Bank (SNB)", 2600, { bold: true, shade: LIGHT_BG }), dataCell("Saudi Arabia", 1800, { shade: LIGHT_BG }),
              dataCell("Risk Analytics", 2560, { shade: LIGHT_BG }), dataCell("Hormuz / oil supply chain", 2400, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("Emirates NBD", 2600, { bold: true }), dataCell("UAE", 1800),
              dataCell("Treasury & Risk", 2560), dataCell("Liquidity stress simulation", 2400),
            ]}),
            new TableRow({ children: [
              dataCell("Qatar Insurance Company", 2600, { bold: true, shade: LIGHT_BG }), dataCell("Qatar", 1800, { shade: LIGHT_BG }),
              dataCell("Head of Actuarial", 2560, { shade: LIGHT_BG }), dataCell("IFRS 17 catastrophe reserving", 2400, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("SALAMA Islamic Insurance", 2600, { bold: true }), dataCell("UAE", 1800),
              dataCell("Chief Actuary", 2560), dataCell("Marine P&I claims cascade", 2400),
            ]}),
            new TableRow({ children: [
              dataCell("Gulf Insurance Group", 2600, { bold: true, shade: LIGHT_BG }), dataCell("Kuwait", 1800, { shade: LIGHT_BG }),
              dataCell("Reinsurance Desk", 2560, { shade: LIGHT_BG }), dataCell("Multi-scenario loss estimation", 2400, { shade: LIGHT_BG }),
            ]}),
          ],
        }),

        // ── SECTION 3: OUTREACH PLAN ───────────────────────────────────
        new Paragraph({ children: [new PageBreak()] }),
        heading1("3. Enterprise Outreach Plan"),

        body("Outreach is NOT marketing. It is precision account penetration. Every touch delivers proprietary intelligence the prospect cannot get elsewhere."),

        heading2("3.1 The Intelligence Brief (Door Opener)"),
        body("For each Tier 1 named account, produce a bespoke 4-page intelligence brief that runs their specific scenario through Impact Observatory and presents actual simulation output. This is not a brochure\u2014it is a deliverable."),

        heading3("Brief Structure"),
        numberedItem("Scenario injection: their country, their infrastructure, their threat vector"),
        numberedItem("Cascade map: 42-node graph showing propagation path through their financial ecosystem"),
        numberedItem("Loss quantification: sector-by-sector USD impact with confidence intervals"),
        numberedItem("Decision actions: top 3 ranked actions with owner, cost, loss avoided, and regulatory risk"),
        numberedItem("Audit trail: SHA-256 hash proving the output is deterministic and reproducible"),

        spacer(40),
        calloutBox("KEY PRINCIPLE", "The brief IS the product demo. The prospect reads their own scenario, sees their own institutions in the cascade, and realizes they have no equivalent capability. The ask is not \"would you like a demo?\"\u2014it is \"would you like to run your own scenarios?\"", GREEN),

        heading2("3.2 Delivery Channels (by Tier)"),
        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [1500, 2620, 2620, 2620],
          rows: [
            new TableRow({ children: [
              headerCell("Tier", 1500), headerCell("Channel", 2620),
              headerCell("First Touch", 2620), headerCell("Ask", 2620),
            ]}),
            new TableRow({ children: [
              dataCell("Regulators", 1500, { bold: true }),
              dataCell("Direct to Financial Stability Director via gov relations or advisory board intro", 2620),
              dataCell("Deliver intelligence brief + offer sandbox evaluation", 2620),
              dataCell("30-day sandbox pilot with their scenarios", 2620),
            ]}),
            new TableRow({ children: [
              dataCell("SWFs / NOCs", 1500, { bold: true, shade: LIGHT_BG }),
              dataCell("CRO network, energy conference side meetings (ADIPEC, IPTC), Vision 2030 alignment", 2620, { shade: LIGHT_BG }),
              dataCell("Portfolio stress test on Hormuz scenario with their asset mix", 2620, { shade: LIGHT_BG }),
              dataCell("Paid proof-of-value (4 weeks, $50K)", 2620, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("Banks / Insurers", 1500, { bold: true }),
              dataCell("CRO and Head of Actuarial direct outreach, reinsurance broker intro (Guy Carpenter, Aon GCC)", 2620),
              dataCell("IFRS 17 compliance gap analysis using their loss history", 2620),
              dataCell("Free scenario run; convert to 90-day pilot", 2620),
            ]}),
          ],
        }),

        heading2("3.3 Conference & Event Strategy"),
        body("Do not sponsor booths. Instead, secure speaking slots and deliver live simulation runs from stage."),

        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2800, 2200, 2200, 2160],
          rows: [
            new TableRow({ children: [
              headerCell("Event", 2800), headerCell("Date / Location", 2200),
              headerCell("Target Audience", 2200), headerCell("Action", 2160),
            ]}),
            new TableRow({ children: [
              dataCell("ADIPEC", 2800, { bold: true }), dataCell("Abu Dhabi, Nov 2026", 2200),
              dataCell("NOCs, energy risk", 2200), dataCell("Live Hormuz scenario", 2160),
            ]}),
            new TableRow({ children: [
              dataCell("GIFS (Gulf Insurance Forum)", 2800, { bold: true, shade: LIGHT_BG }), dataCell("Bahrain, Q1 2027", 2200, { shade: LIGHT_BG }),
              dataCell("Insurers, actuaries", 2200, { shade: LIGHT_BG }), dataCell("IFRS 17 catastrophe demo", 2160, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("Saudi Capital Market Forum", 2800, { bold: true }), dataCell("Riyadh, Q4 2026", 2200),
              dataCell("CMA, banks, PIF", 2200), dataCell("Oil shock cascade demo", 2160),
            ]}),
            new TableRow({ children: [
              dataCell("Fintech Abu Dhabi", 2800, { bold: true, shade: LIGHT_BG }), dataCell("Abu Dhabi, Q4 2026", 2200, { shade: LIGHT_BG }),
              dataCell("CBUAE, fintech", 2200, { shade: LIGHT_BG }), dataCell("Cyber attack on SWIFT", 2160, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("World Government Summit", 2800, { bold: true }), dataCell("Dubai, Feb 2027", 2200),
              dataCell("Sovereign decision makers", 2200), dataCell("Cross-GCC resilience brief", 2160),
            ]}),
          ],
        }),


        // ── SECTION 4: DEMO STRATEGY ───────────────────────────────────
        new Paragraph({ children: [new PageBreak()] }),
        heading1("4. Demo Strategy"),

        body("The demo is not a product tour. It is a live simulation that produces intelligence the prospect cannot produce with any tool they currently own. Every demo is scenario-specific to the prospect\u2019s mandate."),

        heading2("4.1 Demo Architecture: The 7-Minute Protocol"),
        body("Every demo follows a strict 7-minute structure. No slides. The product IS the presentation."),

        numberedItem("INJECT (60s): Select scenario from the 15-scenario catalog. Name the prospect\u2019s country and sector. Example: \"SAMA, let\u2019s model what happens to the Saudi financial system if oil production drops 30% for 7 days.\""),
        numberedItem("CASCADE (90s): Watch the 42-node knowledge graph light up in real-time. Show the propagation path: saudi_aramco \u2192 dammam_port \u2192 saudi_banking \u2192 riyadh_financial \u2192 sama. Point at each node: \"This is your institution.\""),
        numberedItem("QUANTIFY (60s): Show the Event Header: total loss USD, nodes impacted, propagation depth, peak day, confidence. Show the Sector Rollup Bar: banking 0.52 MODERATE, energy 0.78 ELEVATED."),
        numberedItem("DECIDE (90s): Show the Decision Panel: 4 ranked actions. Click the top action\u2014show owner (\"National Oil Company\"), cost ($1.2B), loss avoided ($3.8B), regulatory risk (70%), IFRS 17 flag. Say: \"This is the action your counterpart at the Ministry of Energy needs to take in the next 6 hours.\""),
        numberedItem("AUDIT (60s): Show the Status Bar: SHA-256 hash, model version, pipeline stages, confidence score. Say: \"Every output is deterministic. Run it again tomorrow\u2014same inputs, same hash. Your auditor can verify this.\""),
        numberedItem("COMPARE (60s): Run a second scenario (different threat vector). Show how the cascade path changes. Demonstrate that the system models the GCC as an interconnected system, not isolated sectors."),
        numberedItem("ASK (30s): \"Would you like to run your own scenarios? We can set up a 30-day sandbox with your team next week.\""),

        heading2("4.2 Scenario-to-Prospect Mapping"),
        body("Each prospect gets a scenario that hits their institutional mandate directly:"),

        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2200, 3560, 3600],
          rows: [
            new TableRow({ children: [
              headerCell("Prospect", 2200), headerCell("Primary Scenario", 3560),
              headerCell("Why It Hurts", 3600),
            ]}),
            new TableRow({ children: [
              dataCell("SAMA", 2200, { bold: true }),
              dataCell("saudi_oil_shock + regional_liquidity_stress", 3560),
              dataCell("Shows fiscal revenue cascade into banking liquidity\u2014SAMA\u2019s direct mandate", 3600),
            ]}),
            new TableRow({ children: [
              dataCell("CBUAE", 2200, { bold: true, shade: LIGHT_BG }),
              dataCell("uae_banking_crisis + hormuz_disruption", 3560, { shade: LIGHT_BG }),
              dataCell("Shows UAE banking \u2192 DIFC \u2192 fintech \u2192 payment rails\u2014their supervision scope", 3600, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("PIF", 2200, { bold: true }),
              dataCell("iran_regional_escalation + hormuz_full_closure", 3560),
              dataCell("Shows portfolio-level exposure across all GCC assets they hold", 3600),
            ]}),
            new TableRow({ children: [
              dataCell("Aramco", 2200, { bold: true, shade: LIGHT_BG }),
              dataCell("hormuz_chokepoint_disruption (severity 0.95)", 3560, { shade: LIGHT_BG }),
              dataCell("Shows Ras Tanura terminal at 40% capacity, supply chain collapse, force majeure trigger", 3600, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("QIC", 2200, { bold: true }),
              dataCell("qatar_lng_disruption + red_sea_instability", 3560),
              dataCell("Shows marine P&I claims surge 4.2x\u2014their reinsurance trigger threshold", 3600),
            ]}),
            new TableRow({ children: [
              dataCell("FAB / SNB", 2200, { bold: true, shade: LIGHT_BG }),
              dataCell("uae_banking_crisis / saudi_oil_shock", 3560, { shade: LIGHT_BG }),
              dataCell("Shows their bank as a propagation node\u2014liquidity stress index, CAR erosion", 3600, { shade: LIGHT_BG }),
            ]}),
          ],
        }),

        heading2("4.3 Demo Environment"),
        bulletItem("Run from the production Decision Command Center UI (dark theme, single-screen terminal)"),
        bulletItem("Backend on Railway (live API), frontend on Vercel\u2014no local dependencies visible to prospect"),
        bulletItem("Mock mode for air-gapped environments (military, central bank secure rooms)\u2014toggle via URL param"),
        bulletItem("Pre-load 3 scenarios before the meeting. Never show setup. The system should appear always-on."),
        bulletItem("Record every demo with consent\u2014the replay becomes the follow-up collateral"),


        // ── SECTION 5: CONVERSION STEPS ────────────────────────────────
        new Paragraph({ children: [new PageBreak()] }),
        heading1("5. Pilot-to-Contract Conversion Sequence"),

        body("Conversion is a 5-gate funnel. Each gate has a deliverable, a decision maker, and a kill criterion. No gate is skipped."),

        heading2("Gate 1: Intelligence Brief (Week 0)"),
        bodyBold("Deliverable: ", "Bespoke 4-page scenario simulation output tailored to the prospect\u2019s country and institutional mandate."),
        bodyBold("Decision Maker: ", "Director-level (Financial Stability Director, CRO, Head of Actuarial)."),
        bodyBold("Success Criterion: ", "Prospect requests a live demo or asks \"can we run our own scenarios?\""),
        bodyBold("Kill Criterion: ", "No response after 2 follow-ups. Move to next named account."),
        bodyBold("Cost: ", "Zero. This is a lead-generation investment."),

        heading2("Gate 2: Live Demo (Week 1\u20132)"),
        bodyBold("Deliverable: ", "7-minute demo protocol executed on their scenario. Recorded with consent."),
        bodyBold("Decision Maker: ", "Same director + their technical lead (risk analytics team)."),
        bodyBold("Success Criterion: ", "Prospect asks for sandbox access or says \"we need to evaluate this internally.\""),
        bodyBold("Kill Criterion: ", "\"Interesting but we\u2019re not ready.\" Nurture for 6 months with quarterly scenario briefs."),
        bodyBold("Cost: ", "Zero."),

        heading2("Gate 3: Sandbox Pilot (Week 3\u20138)"),
        bodyBold("Deliverable: ", "30-day sandbox with API access. Prospect runs their own scenarios. We provide 3 onboarding sessions."),
        bodyBold("Decision Maker: ", "Technical lead + procurement."),
        bodyBold("Success Criterion: ", "Prospect runs 10+ scenarios. Their team references the output in an internal report or board deck."),
        bodyBold("Kill Criterion: ", "Fewer than 3 scenario runs in 30 days = no internal champion. Extend once. Then exit."),
        bodyBold("Pricing: ", "Free for regulators (Tier 1). $50K paid proof-of-value for SWFs/NOCs. Free for banks/insurers (Tier 3) if regulator is already onboarded."),

        heading2("Gate 4: Technical Validation (Week 6\u201310)"),
        bodyBold("Deliverable: ", "Technical audit package: deterministic replay proof (same inputs \u2192 same SHA-256 hash), pipeline stage documentation, data lineage, IFRS 17 mapping, PDPL data residency statement."),
        bodyBold("Decision Maker: ", "CISO, Head of IT, external auditor (if required)."),
        bodyBold("Success Criterion: ", "Technical clearance to proceed to procurement."),
        bodyBold("Kill Criterion: ", "Data sovereignty objection that cannot be resolved with on-premise deployment option."),
        bodyBold("Mitigation: ", "Offer Mac M4 Max local deployment (our system runs on-premise\u2014this is a core design choice)."),

        heading2("Gate 5: Contract (Week 10\u201316)"),
        bodyBold("Deliverable: ", "Annual subscription proposal: platform access + scenario library + quarterly intelligence briefs + priority support."),
        bodyBold("Decision Maker: ", "CFO or COO (budget holder) + Procurement."),
        bodyBold("Success Criterion: ", "Signed contract."),
        bodyBold("Kill Criterion: ", "Procurement stall beyond 6 weeks. Escalate through advisory board or executive sponsor."),

        heading2("Pricing Framework"),
        new Table({
          width: { size: CONTENT_WIDTH, type: WidthType.DXA },
          columnWidths: [2400, 2320, 2320, 2320],
          rows: [
            new TableRow({ children: [
              headerCell("Tier", 2400), headerCell("Annual License", 2320),
              headerCell("Includes", 2320), headerCell("Add-ons", 2320),
            ]}),
            new TableRow({ children: [
              dataCell("Regulator", 2400, { bold: true }),
              dataCell("$400K\u2013$800K", 2320, { color: GREEN }),
              dataCell("Full platform, 15 scenarios, API, custom scenarios, priority support", 2320),
              dataCell("Cross-GCC federation module ($200K)", 2320),
            ]}),
            new TableRow({ children: [
              dataCell("SWF / NOC", 2400, { bold: true, shade: LIGHT_BG }),
              dataCell("$250K\u2013$600K", 2320, { color: GREEN, shade: LIGHT_BG }),
              dataCell("Platform, portfolio overlay, 15 scenarios, quarterly briefs", 2320, { shade: LIGHT_BG }),
              dataCell("Custom scenario authoring ($75K each)", 2320, { shade: LIGHT_BG }),
            ]}),
            new TableRow({ children: [
              dataCell("Bank / Insurer", 2400, { bold: true }),
              dataCell("$120K\u2013$350K", 2320, { color: GREEN }),
              dataCell("Platform, sector-specific view, Basel/IFRS 17 compliance reports", 2320),
              dataCell("API integration with core banking ($50K)", 2320),
            ]}),
          ],
        }),

        spacer(80),
        calloutBox("REVENUE MODEL", "Year 1 target: 3 regulator pilots (2 converting to paid) + 2 SWF paid PoVs + 4 bank/insurer pilots. Revenue range: $800K\u2013$1.8M ARR. Year 2: regulator mandates create Tier 3 pull demand. Target 10\u201315 bank/insurer seats via regulatory compliance driver. Revenue range: $2.5M\u2013$5M ARR.", GREEN),


        // ── SECTION 6: EXECUTION TIMELINE ──────────────────────────────
        new Paragraph({ children: [new PageBreak()] }),
        heading1("6. 90-Day Execution Sequence"),

        heading2("Month 1: Intelligence Brief Factory"),
        numberedItem("Produce 5 bespoke intelligence briefs (one per Tier 1 named account: SAMA, CBUAE, CBB, IA, CMA)"),
        numberedItem("Each brief runs the prospect\u2019s scenario through the live backend and exports a 4-page PDF from the Decision Command Center"),
        numberedItem("Identify and brief the delivery channel for each account (gov relations intro, advisory board, direct)"),
        numberedItem("Deliver briefs. Track opens. Follow up within 48 hours."),

        heading2("Month 2: Demo Execution & Pilot Launch"),
        numberedItem("Execute 7-minute demo for every prospect that responds to the brief"),
        numberedItem("Launch sandbox pilot for first 2\u20133 accounts (likely CBUAE + one insurer)"),
        numberedItem("Begin SWF/NOC outreach with portfolio-specific scenarios (PIF, ADIA)"),
        numberedItem("Submit speaking proposals for ADIPEC and Saudi Capital Market Forum"),

        heading2("Month 3: Conversion & Expansion"),
        numberedItem("Deliver technical audit packages for prospects in Gate 4"),
        numberedItem("Convert first pilot to paid contract (target: one regulator)"),
        numberedItem("Launch Tier 3 outreach using regulator adoption as social proof"),
        numberedItem("Begin custom scenario development for first paying client"),
        numberedItem("Produce quarterly intelligence brief (public, not bespoke) as nurture content for stalled accounts"),

        spacer(120),
        heading1("7. Decision Gate: What Must Be True"),

        body("Before executing this plan, the following must hold:"),

        accentBox([
          new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 80 }, children: [
            new TextRun({ text: "Backend deployed and stable on Railway with < 2s response time for full 17-stage pipeline run", font: "Arial", size: 21, color: "374151" }),
          ]}),
          new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 80 }, children: [
            new TextRun({ text: "Decision Command Center UI is production-grade (verified: 99 tests passing, zero TS errors)", font: "Arial", size: 21, color: "374151" }),
          ]}),
          new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 80 }, children: [
            new TextRun({ text: "PDF export of simulation results works (for intelligence brief generation)", font: "Arial", size: 21, color: "374151" }),
          ]}),
          new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 80 }, children: [
            new TextRun({ text: "All 15 scenarios in the catalog produce valid, non-error outputs", font: "Arial", size: 21, color: "374151" }),
          ]}),
          new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 80 }, children: [
            new TextRun({ text: "On-premise deployment path documented (Mac M4 Max Docker Compose) for data-sovereign prospects", font: "Arial", size: 21, color: "374151" }),
          ]}),
          new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 80 }, children: [
            new TextRun({ text: "Arabic bilingual content in UI is complete (labels, actions, narratives)", font: "Arial", size: 21, color: "374151" }),
          ]}),
          new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 40 }, children: [
            new TextRun({ text: "At least one warm introduction path exists for 3 of the 5 Tier 1 named accounts", font: "Arial", size: 21, color: "374151" }),
          ]}),
        ]),

        spacer(200),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 2, color: BORDER_COLOR, space: 12 } },
          spacing: { before: 200 },
          children: [new TextRun({ text: "END OF DOCUMENT", font: "Arial", size: 18, bold: true, color: GRAY })],
        }),
      ],
    },
  ],
});

// ── Generate ────────────────────────────────────────────────────────────
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/sessions/dazzling-magical-newton/mnt/deevo-sim/Impact_Observatory_GTM_Strategy.docx", buffer);
  console.log("GTM Strategy document generated successfully.");
});
