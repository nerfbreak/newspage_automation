"""Repeatable production-readiness checks for Optimize Newspage Automation.

This script is intentionally static/offline. It does not call Supabase,
Newspage, Telegram, Playwright, or the network.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "SECURITY_AUDIT_REPORT.md",
    "tests/manual/REGRESSION_CHECKLIST.md",
    "docs/database_migrations.md",
    "docs/error_taxonomy.md",
    "error_taxonomy.py",
    "tests/smoke/README.md",
    ".github/workflows/smoke-tests.yml",
    ".github/workflows/security-audit.yml",
    "docs/spec_artifact_policy.md",
    "docs/production_readiness_status.md",
    "scripts/supabase_schema_check.py",
    "docs/supabase_live_schema_check_2026-07-07.md",
    "docs/dependency_pruning_review.md",
    "docs/antigravity_handoff.md",
    "docs/release_readiness_checklist.md",
)

LOCAL_SECRET_PATHS = (
    ".streamlit/secrets.toml",
    ".env",
)

IGNORED_SPEC_PATHS = (
    ".agents/",
    ".specify/",
    "specs/",
)

ROOT_DEBUG_ARTIFACT_PATTERNS = (
    "scratch*.py",
    "test_*.py",
    "tmp*.py",
    "dump*.py",
)

PYTHON_SCAN_GLOBS = (
    "*.py",
    "pages/*.py",
    "scripts/*.py",
    "tests/smoke/*.py",
)

SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd)\b\s*=\s*['\"][^'\"]{8,}['\"]"
)
SHELL_TRUE_PATTERN = "shell" + "=True"


@dataclass(frozen=True)
class AuditFinding:
    check: str
    status: str
    detail: str


def _repo_path(path: str) -> Path:
    return REPO_ROOT / path


def _git_ls_files() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return {line.replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def _iter_python_files() -> Iterable[Path]:
    seen: set[Path] = set()
    for pattern in PYTHON_SCAN_GLOBS:
        for path in REPO_ROOT.glob(pattern):
            if path.is_file() and path not in seen:
                seen.add(path)
                yield path


def _read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def check_required_artifacts() -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path in REQUIRED_FILES:
        exists = _repo_path(path).is_file()
        findings.append(
            AuditFinding(
                "required-artifact",
                "PASS" if exists else "FAIL",
                f"{path} {'exists' if exists else 'is missing'}",
            )
        )
    return findings


def check_secret_tracking(tracked_files: set[str]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path in LOCAL_SECRET_PATHS:
        tracked = path in tracked_files
        findings.append(
            AuditFinding(
                "secret-tracking",
                "FAIL" if tracked else "PASS",
                f"{path} {'is tracked' if tracked else 'is not tracked'}",
            )
        )
    return findings


def check_requirements_pinned() -> list[AuditFinding]:
    req_path = _repo_path("requirements.txt")
    if not req_path.is_file():
        return [AuditFinding("dependency-pinning", "FAIL", "requirements.txt is missing")]

    unpinned: list[str] = []
    for line in _read_text(req_path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "==" not in stripped:
            unpinned.append(stripped)

    return [
        AuditFinding(
            "dependency-pinning",
            "PASS" if not unpinned else "FAIL",
            "all requirements are pinned" if not unpinned else f"unpinned requirements: {', '.join(unpinned[:10])}",
        )
    ]


def check_static_python_safety() -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    shell_true_hits: list[str] = []
    hardcoded_secret_hits: list[str] = []

    for path in _iter_python_files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        text = _read_text(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if SHELL_TRUE_PATTERN in line.replace(" ", ""):
                shell_true_hits.append(f"{relative}:{line_no}")
            if SECRET_ASSIGNMENT_RE.search(line) and "os.environ" not in line and "st.secrets" not in line:
                hardcoded_secret_hits.append(f"{relative}:{line_no}")

    findings.append(
        AuditFinding(
            "subprocess-shell",
            "PASS" if not shell_true_hits else "FAIL",
            "no subprocess shell execution usage found"
            if not shell_true_hits
            else f"subprocess shell execution found at {', '.join(shell_true_hits)}",
        )
    )
    findings.append(
        AuditFinding(
            "hardcoded-secrets",
            "PASS" if not hardcoded_secret_hits else "FAIL",
            "no obvious hardcoded secret assignments found"
            if not hardcoded_secret_hits
            else f"possible hardcoded secrets at {', '.join(hardcoded_secret_hits[:10])}",
        )
    )
    return findings


def check_root_debug_artifacts() -> list[AuditFinding]:
    hits: list[str] = []
    for pattern in ROOT_DEBUG_ARTIFACT_PATTERNS:
        for path in REPO_ROOT.glob(pattern):
            if path.is_file():
                hits.append(path.name)

    return [
        AuditFinding(
            "root-debug-artifacts",
            "PASS" if not hits else "FAIL",
            "no root-level scratch/debug Python files found"
            if not hits
            else f"root-level scratch/debug files found: {', '.join(sorted(hits))}",
        )
    ]


def check_spec_policy(tracked_files: set[str]) -> list[AuditFinding]:
    policy_exists = _repo_path("docs/spec_artifact_policy.md").is_file()
    tracked_ignored = [
        path
        for path in tracked_files
        if any(path.startswith(prefix) for prefix in IGNORED_SPEC_PATHS)
    ]
    return [
        AuditFinding(
            "spec-artifact-policy",
            "PASS" if policy_exists else "FAIL",
            "docs/spec_artifact_policy.md exists" if policy_exists else "Spec Kit artifact policy is missing",
        ),
        AuditFinding(
            "spec-artifact-awareness",
            "PASS",
            f"{len(tracked_ignored)} ignored Spec/agent artifact(s) are intentionally tracked with force-add when needed",
        ),
    ]


def run_audit() -> list[AuditFinding]:
    tracked_files = _git_ls_files()
    findings: list[AuditFinding] = []
    findings.extend(check_required_artifacts())
    findings.extend(check_secret_tracking(tracked_files))
    findings.extend(check_requirements_pinned())
    findings.extend(check_static_python_safety())
    findings.extend(check_root_debug_artifacts())
    findings.extend(check_spec_policy(tracked_files))
    return findings


def render_markdown(findings: list[AuditFinding]) -> str:
    status_counts = {status: sum(1 for finding in findings if finding.status == status) for status in ("PASS", "FAIL")}
    lines = [
        "# Production Readiness Audit",
        "",
        f"PASS: {status_counts['PASS']}",
        f"FAIL: {status_counts['FAIL']}",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for finding in findings:
        detail = finding.detail.replace("|", "\\|")
        lines.append(f"| {finding.check} | {finding.status} | {detail} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run static production-readiness checks.")
    parser.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    args = parser.parse_args()

    findings = run_audit()
    failed = [finding for finding in findings if finding.status == "FAIL"]

    if args.format == "json":
        print(json.dumps([asdict(finding) for finding in findings], indent=2))
    elif args.format == "markdown":
        print(render_markdown(findings), end="")
    else:
        for finding in findings:
            print(f"{finding.status:4} {finding.check}: {finding.detail}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
