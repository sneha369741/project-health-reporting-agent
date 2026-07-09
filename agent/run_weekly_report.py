#!/usr/bin/env python3
"""
run_weekly_report.py
Project Health Reporting Agent — weekly run.

Usage:
    python run_weekly_report.py --input-dir /path/to/plans --output-dir /path/to/reports
    python run_weekly_report.py --input-file /path/to/single_plan.xlsx

Reads every .xlsx project plan in the input directory, computes a RAG status
with plain-English reasoning for each (see rag_engine.py / docs/RAG_Methodology.md),
writes one Markdown report + one JSON record per project, and an index summary
across all projects for that run.

To run weekly on a schedule (bonus requirement), add to crontab:
    0 8 * * MON  cd /path/to/agent && python run_weekly_report.py \
                  --input-dir ./plans --output-dir ./outputs/weekly >> agent.log 2>&1
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from rag_engine import compute_project_rag  # noqa: E402

RAG_EMOJI = {"Green": "🟢", "Amber": "🟡", "Red": "🔴", "Grey (Data Incomplete)": "⚪"}


def format_markdown_report(result: dict) -> str:
    rag = result["rag"]
    emoji = RAG_EMOJI.get(rag, "")
    lines = []
    lines.append(f"# Weekly Project Health Report — {result['project_name']}")
    lines.append("")
    lines.append(f"**Status: {emoji} {rag}**  |  Composite score: {result['composite_score']}/100")
    lines.append(f"**As of:** {result['as_of']}  |  **PM:** {result['project_manager']}  |  **Stage:** {result['project_stage']}")
    lines.append("")

    tc = result["task_counts"]
    lines.append(
        f"Tasks — Completed: {tc['completed']}, In Progress: {tc['in_progress']}, "
        f"Not Started: {tc['not_started']}, On Hold: {tc['on_hold']}"
    )
    lines.append("")
    lines.append("## Why this status")
    lines.append("")

    labels = {
        "schedule": "Schedule Health (40%)",
        "progress": "Milestone / Progress Health (25%)",
        "blockers": "Blockers (20%)",
        "sentiment": "Stakeholder Sentiment (15%)",
    }
    for key, label in labels.items():
        score = result["scores"].get(key)
        score_str = f"{score}/100" if score is not None else "N/A (insufficient data)"
        lines.append(f"**{label} — {score_str}**")
        for n in result["reasoning"].get(key, []):
            lines.append(f"- {n}")
        lines.append("")

    if result["reasoning"].get("overrides"):
        lines.append("## Overrides applied")
        for n in result["reasoning"]["overrides"]:
            lines.append(f"- {n}")
        lines.append("")

    lines.append("## Budget burn")
    lines.append("- Not scored — no cost/hours/invoicing data present in this workbook. "
                  "See RAG methodology for how this signal would be added.")
    lines.append("")
    lines.append(f"_Source: {result['source_file']}_")
    return "\n".join(lines)


def run(input_files, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for f in input_files:
        try:
            result = compute_project_rag(f)
        except Exception as e:
            result = {
                "project_name": Path(f).stem,
                "rag": "Grey (Data Incomplete)",
                "error": str(e),
                "source_file": str(f),
            }
        results.append(result)

        safe_name = "".join(c if c.isalnum() else "_" for c in result["project_name"])[:60]
        md_path = output_dir / f"{safe_name}_weekly_report.md"
        json_path = output_dir / f"{safe_name}_weekly_report.json"

        if "error" not in result:
            md_path.write_text(format_markdown_report(result))
        else:
            md_path.write_text(
                f"# Weekly Project Health Report — {result['project_name']}\n\n"
                f"**Status: ⚪ Grey (Data Incomplete)**\n\n"
                f"Could not parse this workbook: `{result['error']}`\n"
            )
        json_path.write_text(json.dumps(result, indent=2, default=str))
        print(f"[ok] {result['project_name']}: {result['rag']}  -> {md_path.name}")

    # cross-project index
    index_lines = [f"# Weekly Health Index — run {datetime.now().strftime('%Y-%m-%d')}", ""]
    index_lines.append("| Project | RAG | Composite Score | PM |")
    index_lines.append("|---|---|---|---|")
    for r in results:
        emoji = RAG_EMOJI.get(r.get("rag"), "")
        index_lines.append(
            f"| {r.get('project_name')} | {emoji} {r.get('rag')} | "
            f"{r.get('composite_score', 'N/A')} | {r.get('project_manager', 'N/A')} |"
        )
    (output_dir / "index.md").write_text("\n".join(index_lines))
    (output_dir / "index.json").write_text(json.dumps(results, indent=2, default=str))
    print(f"\nIndex written to {output_dir / 'index.md'}")
    return results


def main():
    ap = argparse.ArgumentParser(description="Project Health Reporting Agent - weekly run")
    ap.add_argument("--input-dir", type=str, help="Directory of .xlsx project plans")
    ap.add_argument("--input-file", type=str, help="Single .xlsx project plan")
    ap.add_argument("--output-dir", type=str, default="./outputs/weekly")
    args = ap.parse_args()

    if args.input_file:
        files = [Path(args.input_file)]
    elif args.input_dir:
        files = sorted(Path(args.input_dir).glob("*.xlsx"))
    else:
        ap.error("Provide --input-dir or --input-file")
        return

    if not files:
        print("No .xlsx files found.")
        return

    run(files, Path(args.output_dir))


if __name__ == "__main__":
    main()
