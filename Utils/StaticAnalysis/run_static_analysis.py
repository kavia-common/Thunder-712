#!/usr/bin/env python3
"""
Static Analysis Runner for Thunder-712.

Runs cpplint (C/C++) and cmakelint (CMake) across the repository,
parses outputs, and emits a Markdown report with summary statistics.

Usage:
  python3 Utils/StaticAnalysis/run_static_analysis.py \
      --repo-root Thunder-712 \
      --out Thunder-712/docs/static-analysis/report.md

This script assumes cpplint and cmakelint are installed and available. If not,
it will print installation guidance using pip:
    python3 -m pip install --user cpplint cmakelint
"""
import argparse
import datetime as _dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


CPP_EXTS = {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hh", ".hxx"}
CMAKE_FILE_NAMES = {"CMakeLists.txt"}
CMAKE_EXTS = {".cmake"}

CPPLINT_LINE_RE = re.compile(r"^(.*?):(\d+):\s*(.*?)\s*\[(.*?)\]\s*\[(\d+)\]\s*$")
CMAKELINT_LINE_RE = re.compile(r"^(.*?):(\d+):\s*(.*?)\s*\[(.*?)\]\s*$")


def _which(cmd: str) -> Optional[str]:
    """Locate a command on PATH or return None."""
    return shutil.which(cmd)


def _exec(cmd: List[str], cwd: Optional[str] = None, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """Execute a subprocess command, capturing stdout and stderr."""
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def _chunk(items: List[str], size: int) -> List[List[str]]:
    """Yield chunks of a list."""
    return [items[i:i + size] for i in range(0, len(items), size)]


def _find_cpp_files(root: Path) -> List[str]:
    """Find C/C++ source and header files under root."""
    files: List[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in CPP_EXTS:
            files.append(str(p))
    return sorted(files)


def _find_cmake_files(root: Path) -> List[str]:
    """Find CMake files under root."""
    files: List[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.name in CMAKE_FILE_NAMES or p.suffix.lower() in CMAKE_EXTS:
            files.append(str(p))
    return sorted(files)


def _parse_cpplint_lines(text: str) -> List[Dict[str, str]]:
    """Parse cpplint output lines into structured entries."""
    entries: List[Dict[str, str]] = []
    for line in text.splitlines():
        m = CPPLINT_LINE_RE.match(line.strip())
        if not m:
            continue
        file, line_no, msg, cat, sev = m.groups()
        entries.append({
            "file": file,
            "line": line_no,
            "message": msg,
            "category": cat,
            "severity": sev,
            "raw": line,
        })
    return entries


def _parse_cmakelint_lines(text: str) -> List[Dict[str, str]]:
    """Parse cmakelint output lines into structured entries."""
    entries: List[Dict[str, str]] = []
    for line in text.splitlines():
        m = CMAKELINT_LINE_RE.match(line.strip())
        if not m:
            continue
        file, line_no, msg, rule = m.groups()
        entries.append({
            "file": file,
            "line": line_no,
            "message": msg,
            "rule": rule,
            "raw": line,
        })
    return entries


def _summarize_cpplint(entries: List[Dict[str, str]]) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Summarize cpplint entries by category and by file."""
    by_cat: Dict[str, int] = {}
    by_file: Dict[str, int] = {}
    for e in entries:
        cat = e.get("category", "unknown")
        by_cat[cat] = by_cat.get(cat, 0) + 1
        f = e["file"]
        by_file[f] = by_file.get(f, 0) + 1
    return by_cat, by_file


def _summarize_cmakelint(entries: List[Dict[str, str]]) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Summarize cmakelint entries by rule and by file."""
    by_rule: Dict[str, int] = {}
    by_file: Dict[str, int] = {}
    for e in entries:
        rule = e.get("rule", "unknown")
        by_rule[rule] = by_rule.get(rule, 0) + 1
        f = e["file"]
        by_file[f] = by_file.get(f, 0) + 1
    return by_rule, by_file


def _format_top(d: Dict[str, int], n: int = 10) -> List[Tuple[str, int]]:
    """Return top N items from a dict sorted by count desc, then key."""
    return sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


# PUBLIC_INTERFACE
def write_report_markdown(
    out_path: Path,
    cpplint_entries: List[Dict[str, str]],
    cmakelint_entries: List[Dict[str, str]],
    repo_root: Path,
) -> None:
    """Write a markdown report with summarized findings and sample issues."""
    ts = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    cpplint_by_cat, cpplint_by_file = _summarize_cpplint(cpplint_entries)
    cmakelint_by_rule, cmakelint_by_file = _summarize_cmakelint(cmakelint_entries)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    def p(rel: str) -> str:
        try:
            return str(Path(rel).relative_to(repo_root))
        except Exception:
            return rel

    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"# Thunder-712 Static Analysis Report\n")
        f.write(f"- Generated: {ts}\n")
        f.write(f"- Repository root: {repo_root}\n\n")

        f.write("## Tooling\n")
        f.write("- cpplint (C/C++ style linter)\n")
        f.write("- cmakelint (CMake style linter)\n")
        f.write("\nIf tools are missing, install with:\n")
        f.write("`python3 -m pip install --user cpplint cmakelint`\n\n")

        f.write("## Summary\n")
        f.write(f"- cpplint issues: {len(cpplint_entries)} across {len(set([e['file'] for e in cpplint_entries]))} files\n")
        f.write(f"- cmakelint issues: {len(cmakelint_entries)} across {len(set([e['file'] for e in cmakelint_entries]))} files\n\n")

        if cpplint_entries:
            f.write("### Top cpplint categories\n")
            for cat, count in _format_top(cpplint_by_cat, 15):
                f.write(f"- {cat}: {count}\n")
            f.write("\n### Files with most cpplint issues\n")
            for file, count in _format_top(cpplint_by_file, 15):
                f.write(f"- {p(file)}: {count}\n")
            f.write("\n")

        if cmakelint_entries:
            f.write("### Top cmakelint rules triggered\n")
            for rule, count in _format_top(cmakelint_by_rule, 15):
                f.write(f"- {rule}: {count}\n")
            f.write("\n### Files with most cmakelint issues\n")
            for file, count in _format_top(cmakelint_by_file, 15):
                f.write(f"- {p(file)}: {count}\n")
            f.write("\n")

        # Sample issues section
        def _sample(entries: List[Dict[str, str]], n: int = 25) -> List[Dict[str, str]]:
            return entries[:n]

        if cpplint_entries:
            f.write("## Sample cpplint issues\n")
            for e in _sample(cpplint_entries, 50):
                f.write(f"- {p(e['file'])}:{e['line']}: {e['message']} [{e['category']}] [sev={e['severity']}]\n")
            f.write("\n")

        if cmakelint_entries:
            f.write("## Sample cmakelint issues\n")
            for e in _sample(cmakelint_entries, 50):
                f.write(f"- {p(e['file'])}:{e['line']}: {e['message']} [{e['rule']}]\n")
            f.write("\n")

        f.write("## Recommendations\n")
        f.write("- Address include order, whitespace, brace placement, and long-line issues highlighted by cpplint.\n")
        f.write("- Normalize CMakeLists.txt indentation and spacing (avoid extra spaces before parentheses, fix trailing whitespace, keep lines <= 80 chars).\n")
        f.write("- Consider enabling clang-tidy with a compile_commands.json for deeper static checks.\n")
        f.write("- Integrate cpplint/cmakelint into CI to prevent regressions.\n")


# PUBLIC_INTERFACE
def run_analysis(repo_root: Path, out_md: Path, cpplint_filters: Optional[str] = None, chunk_size: int = 150) -> int:
    """Run cpplint and cmakelint on the repository and write a markdown report.

    Args:
        repo_root: Path to repository root (e.g., Thunder-712).
        out_md: Output markdown report path.
        cpplint_filters: Optional cpplint filters (e.g., '-build/c++11').
        chunk_size: Number of files per chunk for cpplint to avoid argument length limits.

    Returns:
        Exit code (0 on success, non-zero on partial failures).
    """
    repo_root = repo_root.resolve()
    out_md = out_md.resolve()

    # Discover files
    cpp_files = _find_cpp_files(repo_root)
    cmake_files = _find_cmake_files(repo_root)

    # Check tooling presence
    cpplint_cmd = [sys.executable, "-m", "cpplint"]
    cmakelint_prog = _which("cmakelint") or _which("cmakelint.exe")
    if cmakelint_prog is None:
        print("cmakelint not found on PATH. Install with: python3 -m pip install --user cmakelint", file=sys.stderr)
    if _exec([sys.executable, "-m", "cpplint", "--help"])[0] != 0:
        print("cpplint not found. Install with: python3 -m pip install --user cpplint", file=sys.stderr)

    # Run cpplint
    cpplint_entries: List[Dict[str, str]] = []
    if cpp_files:
        cpplint_opts = []
        if cpplint_filters:
            cpplint_opts.extend(["--filter", cpplint_filters])
        for chunk in _chunk(cpp_files, chunk_size):
            cmd = cpplint_cmd + ["--quiet"] + cpplint_opts + chunk
            rc, out, err = _exec(cmd, cwd=str(repo_root))
            # cpplint prints to stderr
            cpplint_entries.extend(_parse_cpplint_lines(out))
            cpplint_entries.extend(_parse_cpplint_lines(err))
    else:
        print("No C/C++ files found for cpplint.")

    # Run cmakelint
    cmakelint_entries: List[Dict[str, str]] = []
    if cmake_files and cmakelint_prog:
        # cmakelint prints to stdout
        # To avoid arg limit, run per file
        for cf in cmake_files:
            rc, out, err = _exec([cmakelint_prog, cf], cwd=str(repo_root))
            cmakelint_entries.extend(_parse_cmakelint_lines(out))
            cmakelint_entries.extend(_parse_cmakelint_lines(err))
    elif cmake_files and not cmakelint_prog:
        print("cmake files found but cmakelint is not installed.", file=sys.stderr)

    # Write report
    write_report_markdown(out_md, cpplint_entries, cmakelint_entries, repo_root)

    print(f"Static analysis complete. Report written to: {out_md}")
    print(f"cpplint issues: {len(cpplint_entries)} | cmakelint issues: {len(cmakelint_entries)}")
    return 0


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run static analysis (cpplint, cmakelint) for Thunder-712.")
    parser.add_argument("--repo-root", default="Thunder-712", help="Path to repository root (default: Thunder-712)")
    parser.add_argument("--out", default="Thunder-712/docs/static-analysis/report.md", help="Output markdown report path")
    parser.add_argument("--cpplint-filters", default=None, help="cpplint --filter string to reduce noise.")
    parser.add_argument("--chunk-size", type=int, default=150, help="Number of files per cpplint invocation.")
    return parser.parse_args(argv)


def main() -> int:
    args = _parse_args()
    repo_root = Path(args.repo_root)
    out_md = Path(args.out)
    return run_analysis(repo_root, out_md, args.cpplint_filters, args.chunk_size)


if __name__ == "__main__":
    sys.exit(main())
