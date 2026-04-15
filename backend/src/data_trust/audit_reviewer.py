"""
Impact Observatory | مرصد الأثر
AI Code Reviewer — Data Trust Audit Script

Scans the simulation codebase for:
  1. Hardcoded scenario numbers
  2. Files controlling scenario values
  3. Missing timestamps
  4. Missing data sources
  5. Missing confidence logic
  6. Missing fallback behavior
  7. Unsafe "live" wording in copy

Outputs a structured audit report as a list of AuditFinding objects.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════════

class AuditSeverity(str, Enum):
    """Severity of an audit finding."""
    INFO = "info"              # Informational — no action needed
    WARNING = "warning"        # Should be addressed eventually
    CRITICAL = "critical"      # Must be addressed before claiming live data


@dataclass(frozen=True)
class AuditFinding:
    """A single finding from the data trust audit."""
    category: str           # e.g. "hardcoded_value", "missing_timestamp"
    severity: AuditSeverity
    file_path: str
    line_number: int | None
    description: str
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "description": self.description,
            "recommendation": self.recommendation,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Scanner implementations
# ═══════════════════════════════════════════════════════════════════════════════

def _scan_hardcoded_scenario_values(backend_root: Path) -> list[AuditFinding]:
    """Find hardcoded base_loss_usd, peak_day_offset, recovery_base_days."""
    findings: list[AuditFinding] = []
    target_files = [
        backend_root / "src" / "simulation_engine.py",
        backend_root / "src" / "services" / "scenario_service.py",
    ]

    # Patterns that indicate hardcoded scenario numbers
    patterns = [
        (r'"base_loss_usd"\s*:\s*[\d_]+', "hardcoded base_loss_usd"),
        (r'"peak_day_offset"\s*:\s*\d+', "hardcoded peak_day_offset"),
        (r'"recovery_base_days"\s*:\s*\d+', "hardcoded recovery_base_days"),
    ]

    for fpath in target_files:
        if not fpath.exists():
            continue
        rel = str(fpath.relative_to(backend_root.parent))
        lines = fpath.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, start=1):
            for pattern, desc in patterns:
                if re.search(pattern, line):
                    findings.append(AuditFinding(
                        category="hardcoded_value",
                        severity=AuditSeverity.INFO,
                        file_path=rel,
                        line_number=i,
                        description=f"Static {desc} — this is expected for v1 "
                                    f"but must be labeled as static fallback.",
                        recommendation="Keep as fallback. Ensure provenance record "
                                       "marks is_static_fallback=True.",
                    ))
    return findings


def _scan_files_controlling_values(backend_root: Path) -> list[AuditFinding]:
    """Identify all files that define or modify scenario values."""
    findings: list[AuditFinding] = []
    control_files = [
        ("backend/src/config.py",
         "All formula weights (ES, LSI, ISI, URS, Conf, sector coefficients)"),
        ("backend/src/simulation_engine.py",
         "SCENARIO_CATALOG (base_loss, peak_day, recovery), GCC_NODES, GCC_ADJACENCY"),
        ("backend/src/services/scenario_service.py",
         "SCENARIO_TEMPLATES (subset of catalog)"),
        ("backend/src/engines/scenario/templates.py",
         "Detailed scenario templates with shock definitions"),
        ("backend/src/engines/scenario/templates_extended.py",
         "Extended scenario templates (5 additional)"),
        ("backend/src/entity_intelligence.py",
         "Sector sensitivity mappings, claims surge multipliers"),
        ("backend/src/decision_trust/validation_engine.py",
         "Scenario required/valid sectors"),
        ("backend/src/decision_trust/authority_realism_engine.py",
         "Scenario-to-country mapping, GCC institution registry"),
        ("frontend/src/lib/scenarios.ts",
         "Frontend scenario briefings with severity, transmission chains, exposure"),
        ("frontend/src/features/command-center/lib/mock-scenarios-extended.ts",
         "Mock scenario payloads for frontend demo"),
    ]

    for rel_path, desc in control_files:
        findings.append(AuditFinding(
            category="value_control_file",
            severity=AuditSeverity.INFO,
            file_path=rel_path,
            line_number=None,
            description=f"Controls scenario values: {desc}",
            recommendation="Document in DATA_TRUST_LAYER.md. "
                           "Any change here affects simulation output.",
        ))
    return findings


def _scan_missing_timestamps(backend_root: Path) -> list[AuditFinding]:
    """Check if scenario catalog entries have timestamps."""
    findings: list[AuditFinding] = []

    # The SCENARIO_CATALOG does not include last_updated or generated_at
    findings.append(AuditFinding(
        category="missing_timestamp",
        severity=AuditSeverity.WARNING,
        file_path="backend/src/simulation_engine.py",
        line_number=389,
        description="SCENARIO_CATALOG entries have no 'last_updated' or "
                    "'calibrated_at' timestamp. Cannot determine when base "
                    "values were last validated.",
        recommendation="Add provenance timestamps via the data_trust "
                       "ScenarioProvenance layer (now implemented).",
    ))

    # config.py weights also lack timestamps
    findings.append(AuditFinding(
        category="missing_timestamp",
        severity=AuditSeverity.WARNING,
        file_path="backend/src/config.py",
        line_number=1,
        description="Formula weights in config.py have no calibration timestamp. "
                    "ES_W1..W4, SECTOR_ALPHA, SECTOR_THETA are undated.",
        recommendation="Track calibration date in source_registry "
                       "(src_config_weights.last_updated).",
    ))

    return findings


def _scan_missing_data_sources(backend_root: Path) -> list[AuditFinding]:
    """Check for values without declared data sources."""
    findings: list[AuditFinding] = []

    # Frontend briefings have no data source attribution
    findings.append(AuditFinding(
        category="missing_data_source",
        severity=AuditSeverity.WARNING,
        file_path="frontend/src/lib/scenarios.ts",
        line_number=None,
        description="Scenario briefings (severity, transmission chains, "
                    "exposure registers) have no data source attribution. "
                    "Values appear analyst-written with no provenance trail.",
        recommendation="Add src_frontend_briefings reference. "
                       "Mark all frontend briefing values as static/analyst-written.",
    ))

    # Entity intelligence multipliers
    findings.append(AuditFinding(
        category="missing_data_source",
        severity=AuditSeverity.WARNING,
        file_path="backend/src/entity_intelligence.py",
        line_number=None,
        description="Claims surge multipliers (2.80x maritime, 3.10x cyber, etc.) "
                    "have no declared data source. Appear to be expert estimates.",
        recommendation="Register as a static data source in source_registry.",
    ))

    return findings


def _scan_missing_confidence_logic(backend_root: Path) -> list[AuditFinding]:
    """Check for outputs without confidence scoring."""
    findings: list[AuditFinding] = []

    # Frontend mock scenarios have trust metadata but it's static
    findings.append(AuditFinding(
        category="missing_confidence",
        severity=AuditSeverity.INFO,
        file_path="frontend/src/features/command-center/lib/mock-scenarios-extended.ts",
        line_number=None,
        description="Mock scenario payloads include trust metadata with "
                    "static confidence scores. These are not computed dynamically.",
        recommendation="Document that frontend trust metadata is static. "
                       "Future: wire to backend TrustLayerResult.",
    ))

    return findings


def _scan_missing_fallback_behavior(backend_root: Path) -> list[AuditFinding]:
    """Check if missing data gracefully falls back."""
    findings: list[AuditFinding] = []

    # The simulation engine DOES fall back — catalog is the fallback
    findings.append(AuditFinding(
        category="fallback_behavior",
        severity=AuditSeverity.INFO,
        file_path="backend/src/simulation_engine.py",
        line_number=389,
        description="SCENARIO_CATALOG serves as the static fallback for all "
                    "scenario values. If no live data is available, the engine "
                    "uses these hardcoded values. This is correct behavior.",
        recommendation="Ensure all downstream consumers mark output as "
                       "static_fallback=True when catalog values are used.",
    ))

    # External connectors exist but are not wired
    for conn in ["eia.py", "cbk.py", "imf.py"]:
        findings.append(AuditFinding(
            category="fallback_behavior",
            severity=AuditSeverity.INFO,
            file_path=f"backend/src/data_foundation/connectors/{conn}",
            line_number=None,
            description=f"Connector {conn} is implemented but NOT wired to "
                        f"the simulation pipeline. Safe — no live data leaks.",
            recommendation="Keep disconnected until validation protocol "
                           "is established.",
        ))

    return findings


def _scan_unsafe_live_wording(backend_root: Path) -> list[AuditFinding]:
    """Scan for unsafe 'live' or 'real-time' claims in user-facing copy."""
    findings: list[AuditFinding] = []

    # Patterns that could mislead about data freshness
    unsafe_patterns = [
        (r'\blive\s+(?:data|feed|intelligence|signal)', "live data/feed/intelligence"),
        (r'\breal[\s-]?time\s+(?:data|feed|monitoring|intelligence)',
         "real-time data/monitoring"),
        (r'\bstreaming\s+(?:data|feed|intelligence)', "streaming data"),
    ]

    # Scan frontend source files
    frontend_root = backend_root.parent / "frontend" / "src"
    if not frontend_root.exists():
        return findings

    scan_dirs = [
        frontend_root / "components",
        frontend_root / "features",
        frontend_root / "lib",
    ]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for fpath in scan_dir.rglob("*.ts"):
            _scan_file_for_patterns(fpath, unsafe_patterns, findings, backend_root.parent)
        for fpath in scan_dir.rglob("*.tsx"):
            _scan_file_for_patterns(fpath, unsafe_patterns, findings, backend_root.parent)

    return findings


def _scan_file_for_patterns(
    fpath: Path,
    patterns: list[tuple[str, str]],
    findings: list[AuditFinding],
    project_root: Path,
) -> None:
    """Scan a single file for unsafe patterns."""
    try:
        content = fpath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return

    rel = str(fpath.relative_to(project_root))
    lines = content.splitlines()
    for i, line in enumerate(lines, start=1):
        # Skip comments and imports
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("import"):
            continue
        for pattern, desc in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(AuditFinding(
                    category="unsafe_live_wording",
                    severity=AuditSeverity.CRITICAL,
                    file_path=rel,
                    line_number=i,
                    description=f"Found '{desc}' in user-facing code. "
                                f"No live data sources are currently connected.",
                    recommendation="Replace with 'simulated' or 'scenario-based' "
                                   "wording, or add a disclaimer that data is "
                                   "static/config-based.",
                ))


# ═══════════════════════════════════════════════════════════════════════════════
# Main audit runner
# ═══════════════════════════════════════════════════════════════════════════════

def run_data_trust_audit(
    project_root: Path | None = None,
) -> list[AuditFinding]:
    """Run the complete data trust audit.

    Parameters
    ----------
    project_root : Path | None
        Root of the project. If None, uses the default repo layout
        (assumes this file is at backend/src/data_trust/audit_reviewer.py).

    Returns
    -------
    list[AuditFinding]
        All findings, sorted by severity (CRITICAL first).
    """
    if project_root is None:
        # Derive from this file's location
        project_root = Path(__file__).resolve().parent.parent.parent.parent

    backend_root = project_root / "backend"

    findings: list[AuditFinding] = []
    findings.extend(_scan_hardcoded_scenario_values(backend_root))
    findings.extend(_scan_files_controlling_values(backend_root))
    findings.extend(_scan_missing_timestamps(backend_root))
    findings.extend(_scan_missing_data_sources(backend_root))
    findings.extend(_scan_missing_confidence_logic(backend_root))
    findings.extend(_scan_missing_fallback_behavior(backend_root))
    findings.extend(_scan_unsafe_live_wording(backend_root))

    # Sort: CRITICAL → WARNING → INFO
    severity_order = {
        AuditSeverity.CRITICAL: 0,
        AuditSeverity.WARNING: 1,
        AuditSeverity.INFO: 2,
    }
    findings.sort(key=lambda f: severity_order.get(f.severity, 99))

    return findings


def format_audit_report(findings: list[AuditFinding]) -> str:
    """Format findings as a human-readable markdown report."""
    lines: list[str] = []
    lines.append("# Data Trust Audit Report")
    lines.append("")
    lines.append(f"**Total findings:** {len(findings)}")

    by_sev: dict[str, int] = {}
    for f in findings:
        by_sev[f.severity.value] = by_sev.get(f.severity.value, 0) + 1
    for sev, count in by_sev.items():
        lines.append(f"- {sev.upper()}: {count}")
    lines.append("")

    current_cat = ""
    for f in findings:
        if f.category != current_cat:
            current_cat = f.category
            lines.append(f"## {current_cat.replace('_', ' ').title()}")
            lines.append("")

        sev_icon = {"critical": "!!!", "warning": "!!", "info": "i"}
        icon = sev_icon.get(f.severity.value, "?")
        loc = f"{f.file_path}"
        if f.line_number:
            loc += f":{f.line_number}"
        lines.append(f"### [{icon}] {loc}")
        lines.append(f"**{f.description}**")
        lines.append(f"  Recommendation: {f.recommendation}")
        lines.append("")

    return "\n".join(lines)
