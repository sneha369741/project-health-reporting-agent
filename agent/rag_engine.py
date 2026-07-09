"""
rag_engine.py
Core scoring engine for the Project Health Reporting Agent.
Reads a project-plan workbook (task list + Summary sheet) and produces a
weighted RAG status with plain-English reasoning. See docs/RAG_Methodology.md
for the full methodology writeup.
"""

import re
import math
from datetime import datetime, timedelta
import pandas as pd

# ---------------------------------------------------------------------------
# Keyword heuristics (see methodology doc — tunable per engagement)
# ---------------------------------------------------------------------------
BLOCKER_KEYWORDS = [
    "pending", "yet to receive", "yet to recieve", "tbd", "awaiting",
    "blocked", "escalate", "on hold", "delay", "no response", "not received",
    "waiting on", "yet to be", "risk", "dependent on", "issue",
]
POSITIVE_KEYWORDS = [
    "signed off", "sign off", "sign-off", "approved", "completed", "aligned",
    "confirmed", "on track", "closed", "resolved",
]
NEGATIVE_KEYWORDS = [
    "delay", "escalate", "no response", "concern", "risk", "issue",
    "blocked", "not received", "pending", "reschedule", "gap",
]

EXCEL_EPOCH = datetime(1899, 12, 30)


def excel_to_date(val):
    try:
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return None
        if isinstance(val, (int, float)):
            return EXCEL_EPOCH + timedelta(days=float(val))
        if isinstance(val, datetime):
            return val
        return None
    except Exception:
        return None


def _clean_text_series(series):
    return series.dropna().astype(str)


def _score_from_ratio(good, total, invert=False):
    """0-100 score from a good/total ratio; returns None if total is 0 (unknown)."""
    if total == 0:
        return None
    ratio = good / total
    if invert:
        ratio = 1 - ratio
    return round(ratio * 100, 1)


class ProjectPlan:
    """Loads and normalizes one project-plan workbook."""

    def __init__(self, path):
        self.path = path
        self.xl = pd.ExcelFile(path)
        self.task_sheet_name = self.xl.sheet_names[0]
        self.tasks = self.xl.parse(self.task_sheet_name)
        self.summary = self._load_summary()
        self.comments = self._load_comments()
        self.project_name = self._infer_project_name()
        self.today = self._infer_today()

    def _load_summary(self):
        if "Summary" not in self.xl.sheet_names:
            return {}
        df = self.xl.parse("Summary")
        if df.shape[1] < 2:
            return {}
        d = {}
        for _, row in df.iterrows():
            key = row.iloc[0]
            val = row.iloc[1]
            if isinstance(key, str):
                d[key.strip()] = val
        return d

    def _load_comments(self):
        if "Comments" not in self.xl.sheet_names:
            return []
        df = self.xl.parse("Comments")
        if df.empty:
            return []
        texts = []
        # first column of each populated row after header tends to hold the comment text
        for _, row in df.iterrows():
            for v in row.values:
                if isinstance(v, str) and len(v.strip()) > 8 and not v.strip().startswith("Row"):
                    texts.append(v.strip())
        return texts

    def _infer_project_name(self):
        name = self.summary.get("Project Name")
        if isinstance(name, str) and name.strip() and name != "Project Name":
            return name.strip()
        # fall back: first non-empty Project Name cell in task sheet
        if "Project Name" in self.tasks.columns:
            vals = self.tasks["Project Name"].dropna()
            if len(vals):
                return str(vals.iloc[0])
        # fall back: the top-level rollup row's Task Name (row 0 is usually the
        # project-level summary task, e.g. "Zycus - UniSan S2P Implementation")
        if "Task Name" in self.tasks.columns:
            vals = self.tasks["Task Name"].dropna()
            if len(vals):
                return str(vals.iloc[0])
        # fall back: sheet name
        return self.task_sheet_name

    def _infer_today(self):
        d = excel_to_date(self.summary.get("Today's Date"))
        return d or datetime.now()

    # -- derived task-level frames -----------------------------------------
    def active_tasks(self):
        df = self.tasks.copy()
        if "Not Applicable?" in df.columns:
            df = df[df["Not Applicable?"] != True]  # noqa: E712
        return df

    def rag_tag_counts(self):
        col = "RAG" if "RAG" in self.tasks.columns else None
        if col is None:
            return {}
        vc = self.tasks[col].dropna().value_counts()
        return {str(k): int(v) for k, v in vc.items()}

    def all_comment_text(self):
        texts = list(self.comments)
        for col in ("Status Comment", "Comments"):
            if col in self.tasks.columns:
                texts.extend(_clean_text_series(self.tasks[col]).tolist())
        return texts


# ---------------------------------------------------------------------------
# Signal scoring
# ---------------------------------------------------------------------------

def score_schedule_health(plan: ProjectPlan):
    notes = []
    rag_counts = plan.rag_tag_counts()
    tagged_total = sum(rag_counts.get(k, 0) for k in ("Red", "Yellow", "Green"))
    task_tag_score = None
    if tagged_total:
        healthy = rag_counts.get("Green", 0)
        risky = rag_counts.get("Red", 0) * 2 + rag_counts.get("Yellow", 0)  # Red counts double
        raw = max(0, healthy * 100 - risky * 25)
        task_tag_score = round(min(100, raw / tagged_total), 1)
        notes.append(
            f"{rag_counts.get('Red', 0)} tasks tagged Red and "
            f"{rag_counts.get('Yellow', 0)} tagged Yellow out of {tagged_total} tagged tasks."
        )

    # critical-path variance
    crit_score = None
    if "Critical ?" in plan.tasks.columns and "Variance" in plan.tasks.columns:
        crit = plan.tasks[plan.tasks["Critical ?"] == True]  # noqa: E712
        var = pd.to_numeric(
            crit["Variance"].astype(str).str.replace("d", "", regex=False),
            errors="coerce",
        ).dropna()
        if len(var):
            avg_slip = var.mean()
            # -0 days = 100, -15 days or worse = 0
            crit_score = round(max(0, 100 + avg_slip * (100 / 15)), 1)
            crit_score = min(100, crit_score)
            if avg_slip < -1:
                notes.append(f"Critical-path tasks are slipping by an average of {abs(avg_slip):.1f} days.")
            elif avg_slip > 1:
                notes.append(f"Critical-path tasks are running ahead by {avg_slip:.1f} days on average.")

    # project-level Schedule Health tag from Summary
    proj_tag = plan.summary.get("Schedule Health")
    proj_tag_score = {"Green": 100, "Yellow": 55, "Amber": 55, "Red": 15}.get(str(proj_tag), None)
    if proj_tag_score is not None:
        notes.append(f"PM-reported project-level Schedule Health is '{proj_tag}'.")

    components = [s for s in (task_tag_score, crit_score, proj_tag_score) if s is not None]
    score = round(sum(components) / len(components), 1) if components else None
    return score, notes, proj_tag


def score_progress_health(plan: ProjectPlan):
    notes = []
    pct = plan.summary.get("% Complete")
    start = excel_to_date(plan.summary.get("Project Start Date"))
    end = excel_to_date(plan.summary.get("Project End Date"))
    if pct is None or start is None or end is None or end <= start:
        return None, ["Insufficient data to compare actual progress to planned schedule."]
    total_days = (end - start).days
    elapsed_days = (plan.today - start).days
    time_frac = max(0, min(1, elapsed_days / total_days)) if total_days else None
    if time_frac is None:
        return None, ["Could not compute elapsed-time fraction."]
    actual = float(pct)
    gap = actual - time_frac
    # gap of 0 = 100 score; gap of -0.30 (30pts behind) = 0
    score = round(max(0, min(100, 100 + gap * (100 / 0.30))), 1)
    notes.append(
        f"Project is {actual*100:.0f}% complete against {time_frac*100:.0f}% of the "
        f"planned timeline elapsed ({'ahead' if gap >= 0 else 'behind'} by {abs(gap)*100:.0f} points)."
    )
    return score, notes


def score_blockers(plan: ProjectPlan):
    notes = []
    df = plan.active_tasks()
    total = len(df)
    if total == 0:
        return None, ["No task data available to assess blockers."]

    on_hold = 0
    if "On Hold?" in df.columns:
        on_hold = int((df["On Hold?"] == True).sum())  # noqa: E712
    at_risk = 0
    if "At Risk?" in df.columns:
        at_risk = int((df["At Risk?"] == True).sum())  # noqa: E712

    text = " | ".join(plan.all_comment_text()).lower()
    kw_hits = sum(text.count(k) for k in BLOCKER_KEYWORDS)

    on_hold_pct = on_hold / total
    at_risk_pct = at_risk / total
    # weighted penalty
    penalty = on_hold_pct * 200 + at_risk_pct * 150 + min(kw_hits, 20) * 1.5
    score = round(max(0, 100 - penalty), 1)

    if on_hold:
        notes.append(f"{on_hold} task(s) are On Hold ({on_hold_pct*100:.1f}% of active tasks).")
    if at_risk:
        notes.append(f"{at_risk} task(s) are explicitly flagged At Risk.")
    if kw_hits:
        notes.append(f"Comments/status fields contain {kw_hits} blocker-related mentions (e.g. pending, TBD, awaiting sign-off).")
    if not (on_hold or at_risk or kw_hits):
        notes.append("No On Hold tasks, At Risk flags, or blocker language detected in comments.")
    return score, notes


def score_sentiment(plan: ProjectPlan):
    texts = plan.all_comment_text()
    if not texts:
        return None, ["No free-text comments available to gauge stakeholder sentiment."]
    joined = " | ".join(texts).lower()
    pos = sum(joined.count(k) for k in POSITIVE_KEYWORDS)
    neg = sum(joined.count(k) for k in NEGATIVE_KEYWORDS)
    total = pos + neg
    if total == 0:
        return 60.0, ["Comments are largely neutral / factual in tone (no strong positive or negative language)."]
    score = round((pos / total) * 100, 1)
    tone = "positive" if score >= 60 else ("mixed" if score >= 40 else "negative")
    return score, [f"Comment tone reads as {tone} ({pos} positive vs {neg} negative signal words)."]


# ---------------------------------------------------------------------------
# Composite RAG
# ---------------------------------------------------------------------------
WEIGHTS = {"schedule": 0.40, "progress": 0.25, "blockers": 0.20, "sentiment": 0.15}


def compute_project_rag(path):
    plan = ProjectPlan(path)
    sched_score, sched_notes, proj_tag = score_schedule_health(plan)
    prog_score, prog_notes = score_progress_health(plan)
    block_score, block_notes = score_blockers(plan)
    sent_score, sent_notes = score_sentiment(plan)

    scores = {
        "schedule": sched_score,
        "progress": prog_score,
        "blockers": block_score,
        "sentiment": sent_score,
    }
    available = {k: v for k, v in scores.items() if v is not None}
    if not available:
        composite = None
    else:
        wsum = sum(WEIGHTS[k] for k in available)
        composite = round(sum(v * WEIGHTS[k] for k, v in available.items()) / wsum, 1)

    if composite is None:
        rag = "Grey (Data Incomplete)"
    elif composite >= 75:
        rag = "Green"
    elif composite >= 50:
        rag = "Amber"
    else:
        rag = "Red"

    # override rules
    df_active = plan.active_tasks()
    on_hold_pct = 0
    if len(df_active) and "On Hold?" in df_active.columns:
        on_hold_pct = (df_active["On Hold?"] == True).sum() / len(df_active)  # noqa: E712
    override_notes = []
    if on_hold_pct > 0.05 and rag != "Red":
        rag = "Red"
        override_notes.append(
            f"Overridden to Red: {on_hold_pct*100:.1f}% of active tasks are On Hold, exceeding the 5% systemic-blocker threshold."
        )
    if str(proj_tag) == "Red" and rag == "Green":
        rag = "Amber"
        override_notes.append("Capped at Amber: PM-reported project-level Schedule Health is Red.")

    reasoning = {
        "schedule": sched_notes,
        "progress": prog_notes,
        "blockers": block_notes,
        "sentiment": sent_notes,
        "overrides": override_notes,
    }

    return {
        "project_name": plan.project_name,
        "project_manager": plan.summary.get("Project Manager"),
        "project_stage": plan.summary.get("Project Stage"),
        "pct_complete": plan.summary.get("% Complete"),
        "as_of": plan.today.strftime("%Y-%m-%d") if plan.today else None,
        "scores": scores,
        "composite_score": composite,
        "rag": rag,
        "reasoning": reasoning,
        "task_counts": {
            "not_started": plan.summary.get("Not Started"),
            "in_progress": plan.summary.get("In Progress"),
            "completed": plan.summary.get("Completed"),
            "on_hold": plan.summary.get("On Hold"),
        },
        "source_file": str(path),
    }
