#!/usr/bin/env python3
"""
Reads JSON/SARIF output from each scanner, merges with previous state,
applies status transition rules, and produces:
  - findings-state.json  (persistent state for next run)
  - SECURITY_FINDINGS.md (human/agent-readable output)
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

NOW = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_previous_state(path):
    if path and Path(path).exists():
        return json.loads(Path(path).read_text())
    return {}


def fingerprint(f):
    return f"{f['tool']}|{f['rule']}|{f['file']}|{f['line']}"


# ---------------------------------------------------------------------------
# Scanner loaders
# ---------------------------------------------------------------------------

def load_codeql(path="codeql-results.sarif"):
    findings = []
    if not Path(path).exists():
        return findings
    data = json.loads(Path(path).read_text())
    severity_map = {"error": "HIGH", "warning": "MEDIUM", "note": "LOW"}
    for run in data.get("runs", []):
        tool_name = run.get("tool", {}).get("driver", {}).get("name", "CodeQL")
        rules = {
            r["id"]: r
            for r in run.get("tool", {}).get("driver", {}).get("rules", [])
        }
        for result in run.get("results", []):
            rule_id = result.get("ruleId", "unknown")
            rule_meta = rules.get(rule_id, {})
            location = {}
            if result.get("locations"):
                phys = result["locations"][0].get("physicalLocation", {})
                location = {
                    "file": phys.get("artifactLocation", {}).get("uri", ""),
                    "line": phys.get("region", {}).get("startLine", "?"),
                }
            findings.append({
                "tool": tool_name,
                "rule": rule_id,
                "file": location.get("file", ""),
                "line": str(location.get("line", "?")),
                "severity": severity_map.get(
                    result.get("level", "warning"), "MEDIUM"
                ),
                "summary": result.get("message", {}).get("text", "")[:200],
                "detail": rule_meta.get("fullDescription", {}).get(
                    "text",
                    rule_meta.get("shortDescription", {}).get("text", ""),
                ),
            })
    return findings


def load_semgrep(path="semgrep-results.json"):
    findings = []
    if not Path(path).exists():
        return findings
    data = json.loads(Path(path).read_text())
    severity_map = {"ERROR": "HIGH", "WARNING": "MEDIUM", "INFO": "LOW"}
    for r in data.get("results", []):
        findings.append({
            "tool": "Semgrep",
            "rule": r.get("check_id", "unknown"),
            "file": r.get("path", ""),
            "line": str(r.get("start", {}).get("line", "?")),
            "severity": severity_map.get(
                r.get("extra", {}).get("severity", "WARNING"), "MEDIUM"
            ),
            "summary": r.get("extra", {}).get("message", "")[:200],
            "detail": r.get("extra", {}).get("message", ""),
        })
    return findings


def load_sonarcloud(path="sonarcloud-results.json"):
    findings = []
    if not Path(path).exists():
        return findings
    data = json.loads(Path(path).read_text())
    severity_map = {
        "BLOCKER": "CRITICAL",
        "CRITICAL": "HIGH",
        "MAJOR": "MEDIUM",
        "MINOR": "LOW",
        "INFO": "LOW",
    }
    for issue in data.get("issues", []):
        component = issue.get("component", "")
        file_path = component.split(":", 1)[1] if ":" in component else component
        findings.append({
            "tool": "SonarCloud",
            "rule": issue.get("rule", "unknown"),
            "file": file_path,
            "line": str(issue.get("line", "?")),
            "severity": severity_map.get(
                issue.get("severity", "MAJOR"), "MEDIUM"
            ),
            "summary": issue.get("message", "")[:200],
            "detail": (
                f"Type: {issue.get('type', '')}. "
                f"Effort: {issue.get('effort', 'unknown')}."
            ),
        })
    return findings


def load_gitleaks(path="gitleaks-results.json"):
    findings = []
    if not Path(path).exists():
        return findings
    data = json.loads(Path(path).read_text())
    if not isinstance(data, list):
        return findings
    for leak in data:
        findings.append({
            "tool": "Gitleaks",
            "rule": leak.get("RuleID", "unknown"),
            "file": leak.get("File", ""),
            "line": str(leak.get("StartLine", "?")),
            "severity": "CRITICAL",
            "summary": f"Potential secret: {leak.get('Description', '')}",
            "detail": f"Match in {leak.get('File', '')}",
        })
    return findings


def load_trivy(path="trivy-results.json"):
    findings = []
    if not Path(path).exists():
        return findings
    data = json.loads(Path(path).read_text())
    severity_map = {
        "CRITICAL": "CRITICAL",
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW",
    }
    for result_block in data.get("Results", []):
        target = result_block.get("Target", "")
        for vuln in result_block.get("Vulnerabilities", []):
            findings.append({
                "tool": "Trivy",
                "rule": vuln.get("VulnerabilityID", "unknown"),
                "file": target,
                "line": "N/A",
                "severity": severity_map.get(
                    vuln.get("Severity", "MEDIUM"), "MEDIUM"
                ),
                "summary": vuln.get("Title", vuln.get("VulnerabilityID", ""))[:200],
                "detail": (
                    f"Package: {vuln.get('PkgName', '')} "
                    f"Installed: {vuln.get('InstalledVersion', '')} "
                    f"Fixed: {vuln.get('FixedVersion', 'N/A')}"
                ),
            })
    return findings


# ---------------------------------------------------------------------------
# Status transition logic
# ---------------------------------------------------------------------------

def apply_transitions(current_scan_fps, previous_state):
    """
    Merge current scan results with previous state.
    Returns the new state dict keyed by fingerprint.
    """
    new_state = {}

    # Process findings from the current scan
    for fp, finding in current_scan_fps.items():
        if fp in previous_state:
            prev = previous_state[fp]
            prev["last_seen"] = NOW

            # If previously RESOLVED but scanner still reports it, reopen
            if prev["status"] == "RESOLVED":
                prev["status"] = "OPEN"
                prev["status_changed_by"] = "SCRIPT"
                prev["detail"] = (
                    finding["detail"]
                    + " [REOPENED: scanner reports this finding again after "
                    + "previous resolution]"
                )
                prev["resolution"] = ""
                prev["resolved_in"] = ""

            # Update summary/detail from latest scan but keep status
            prev["summary"] = finding["summary"]
            if prev["status"] == "OPEN":
                prev["detail"] = finding["detail"]

            new_state[fp] = prev
        else:
            # New finding
            new_state[fp] = {
                "tool": finding["tool"],
                "rule": finding["rule"],
                "file": finding["file"],
                "line": finding["line"],
                "severity": finding["severity"],
                "summary": finding["summary"],
                "detail": finding["detail"],
                "fingerprint": fp,
                "first_seen": NOW,
                "last_seen": NOW,
                "status": "OPEN",
                "status_changed_by": "SCRIPT",
                "justification": "",
                "resolution": "",
                "resolved_in": "",
            }

    # Handle findings in previous state but NOT in current scan
    for fp, prev in previous_state.items():
        if fp not in current_scan_fps:
            if prev["status"] == "RESOLUTION_PROPOSED":
                # Scanner no longer reports it — promote to RESOLVED
                prev["status"] = "RESOLVED"
                prev["status_changed_by"] = "SCRIPT"
                prev["last_seen"] = prev.get("last_seen", NOW)
                new_state[fp] = prev
            elif prev["status"] in ("ACCEPTED_RISK", "RESOLVED"):
                # Keep historical record
                new_state[fp] = prev
            elif prev["status"] == "PROPOSED_ACCEPTED_RISK":
                # Scanner no longer reports it but human hasn't decided.
                # Keep it so the human can still finalise.
                new_state[fp] = prev
            else:
                # OPEN finding that scanner no longer reports.
                # Promote to RESOLVED (the issue is gone).
                prev["status"] = "RESOLVED"
                prev["status_changed_by"] = "SCRIPT"
                new_state[fp] = prev

    return new_state


def is_blocking(finding):
    return (
        finding["severity"] in ("CRITICAL", "HIGH")
        and finding["status"] in ("OPEN", "PROPOSED_ACCEPTED_RISK", "RESOLUTION_PROPOSED")
    )


# ---------------------------------------------------------------------------
# Output generation
# ---------------------------------------------------------------------------

def write_state(state, path="findings-state.json"):
    Path(path).write_text(json.dumps(state, indent=2))


def write_markdown(state, path="SECURITY_FINDINGS.md"):
    sorted_findings = sorted(
        state.values(),
        key=lambda f: (
            {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(f["severity"], 4),
            f.get("first_seen", ""),
        ),
    )

    open_count = sum(1 for f in sorted_findings if f["status"] == "OPEN")
    blocking_count = sum(1 for f in sorted_findings if is_blocking(f))

    lines = [
        "# Security Findings",
        "",
        f"_Auto-generated by CI at {NOW}. "
        f"{open_count} open findings, {blocking_count} blocking._",
        "",
    ]

    for i, f in enumerate(sorted_findings, 1):
        blocking_flag = "YES" if is_blocking(f) else "NO"
        lines.append(f"## FINDING-{i:04d}")
        lines.append("")
        lines.append(f"- **Status:** {f.get('status', 'OPEN')}")
        lines.append(f"- **Severity:** {f.get('severity', 'MEDIUM')}")
        lines.append(f"- **Blocking:** {blocking_flag}")
        lines.append(f"- **Tool:** {f.get('tool', '')}")
        lines.append(f"- **Rule:** {f.get('rule', '')}")
        lines.append(f"- **File:** {f.get('file', '')}")
        lines.append(f"- **Line:** {f.get('line', '')}")
        lines.append(f"- **Summary:** {f.get('summary', '')}")
        lines.append(f"- **Detail:** {f.get('detail', '')}")
        lines.append(f"- **Fingerprint:** {f.get('fingerprint', '')}")
        lines.append(f"- **First-Seen:** {f.get('first_seen', '')}")
        lines.append(f"- **Last-Seen:** {f.get('last_seen', '')}")
        lines.append(f"- **Status-Changed-By:** {f.get('status_changed_by', 'SCRIPT')}")
        lines.append(f"- **Justification:** {f.get('justification', '')}")
        lines.append(f"- **Resolution:** {f.get('resolution', '')}")
        lines.append(f"- **Resolved-In:** {f.get('resolved_in', '')}")
        lines.append("")

    Path(path).write_text("\n".join(lines))
    print(
        f"Wrote {len(sorted_findings)} findings to {path} "
        f"({open_count} open, {blocking_count} blocking)"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous-state", default=None)
    args = parser.parse_args()

    previous_state = load_previous_state(args.previous_state)

    # Load all scanner results
    all_findings = (
        load_codeql()
        + load_semgrep()
        + load_sonarcloud()
        + load_gitleaks()
        + load_trivy()
    )

    # Key by fingerprint
    current_scan = {}
    for f in all_findings:
        fp = fingerprint(f)
        f["fingerprint"] = fp
        # Keep the highest severity if multiple tools report the same fingerprint
        if fp in current_scan:
            severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            if severity_rank.get(f["severity"], 4) < severity_rank.get(
                current_scan[fp]["severity"], 4
            ):
                current_scan[fp] = f
        else:
            current_scan[fp] = f

    # Merge with previous state
    new_state = apply_transitions(current_scan, previous_state)

    # Write outputs
    write_state(new_state)
    write_markdown(new_state)


if __name__ == "__main__":
    main()