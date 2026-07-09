# Project Health Reporting Agent

This is my submission for the AI Engineer Intern assignment — a small agent that reads
project plans and turns them into a RAG status with actual reasoning behind it, plus a
monthly deck that rolls those up for leadership.

## Layout

```
docs/
  RAG_Methodology.md      # Phase 1 write-up
agent/
  rag_engine.py            # scoring logic
  run_weekly_report.py     # the thing you actually run
  plans/                   # the two sample workbooks
outputs/
  weekly/                  # sample reports from running the agent on both plans
  deck/                    # the monthly presentation
README.md
```

## Running it

```bash
cd agent
pip install pandas openpyxl
python run_weekly_report.py --input-dir ./plans --output-dir ../outputs/weekly
```

That reads every `.xlsx` in `plans/` and, per project, spits out a markdown report
(readable), a JSON file (for whatever consumes this next — a dashboard, the deck
builder, whatever), and an index across all projects in the run.

Single file: `python run_weekly_report.py --input-file ./plans/S2P_Project.xlsx`

For the weekly-schedule bonus, this is stateless and takes no interactive input, so it
drops straight into cron:
```
0 8 * * MON  cd /path/to/agent && python run_weekly_report.py --input-dir ./plans --output-dir ../outputs/weekly >> agent.log 2>&1
```
(GitHub Actions or Task Scheduler work the same way — I just tested with cron since
that's what I had handy.)

## The deck
`outputs/deck/build_deck.js` builds the monthly presentation with pptxgenjs, off the
same JSON the weekly agent produces. Rebuild with:
```
cd outputs/deck && node build_deck.js
```
I tried to make the deck actually say something across the two projects instead of
just restating each one — slide 3 is the real finding: the PM-reported status and the
task-level data disagree on both projects, in opposite directions, which I think is
more useful to a VP than "here's project A, here's project B."

## Why I made the calls I made

**Weighted composite instead of one rule.** No single signal here is trustworthy
alone. A PM's own status tag can lag reality — that's literally what happened with the
Titan plan, which is tagged Green at the top while 63% of its tasks are Yellow/Red
underneath. And a project with zero flagged blockers can still be quietly behind pace,
which is what's happening on UniSan. Four signals, weighted, with override rules for
the "this alone should force Red" cases, felt like the right level of complexity — not
so simple it's gameable, not so complex nobody can explain it in a client call.

**Missing data stays missing, it doesn't get defaulted.** The brief specifically calls
out messy/incomplete data, so I didn't want a missing signal to silently turn into a
50 (neutral) or worse, quietly boost the score. If a signal can't be computed it drops
out of the weighted average and the weights renormalize across what's left. If nothing
at all can be parsed, the status is Grey, not a guessed color. Same logic is why every
report explicitly says "budget: not scored" instead of just not mentioning it —
missing-but-labeled is very different from missing-and-silent.

**Keywords instead of an LLM call for blockers/sentiment.** The status comments in
this data are short and pretty templated ("yet to receive sign-off," "TBD, depends on
X"). A keyword pass handles that fine, and it's free, deterministic, and easy to
explain to someone auditing the numbers. I pulled the keyword lists out to the top of
`rag_engine.py` on purpose — that's the obvious place to swap in a real classifier
later once there's enough comment volume to make it worth training or prompting one.

**Schedule weighted highest.** In a fixed-scope implementation, schedule slip is the
thing a client notices first, so it gets 40%. Progress-vs-time-elapsed is 25% because
that's the earlier warning sign for the same underlying problem. Blockers and
sentiment are lower-weighted (20% / 15%) but I kept them in the mix on purpose — they
tend to move before the schedule numbers do, and that's exactly the Titan pattern:
blocker language and a middling sentiment score showed up even though the top-line
tag was still Green.

## If I had another week
- Add budget as a real fifth signal the moment cost/hours data exists — the code
  already renormalizes weights automatically when a signal is added or missing, so
  it's mostly just a new `score_budget()` function and one line in `WEIGHTS`.
- Swap the keyword scorer for a proper classifier once there's more comment history to
  learn from.
- Store each week's run so the deck can chart a project against its own history
  instead of just comparing two projects to each other — I only had one snapshot in
  time to work with here, so that's the honest limitation of this version.

Didn't record the Loom — no audio/video output on my end — so this README is doing
that job instead. Happy to walk through any part of it live if that's useful.
