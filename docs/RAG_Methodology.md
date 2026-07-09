# RAG Methodology — Project Health Reporting Agent

## What this is for
The goal is simple: give leadership a status they can trust without having to ping a PM
every Friday for an update. That only works if the status is explainable — a red/amber/green
color with no reasoning behind it isn't actually more useful than what we have today.

## What I had to work with
Each project plan is basically an exported task list (MS Project style) — Status, %
Complete, Start/End dates, Baseline dates, Variance, whether a task is Critical or On
Hold, a task-level RAG tag, and some free-text status comments. There's also a Summary
tab with project-level rollups (PM name, dates, overall % complete, task counts).

Notably absent: anything about cost, hours, or budget. More on that below.

## The four signals I'm using

**Schedule Health (40% of the score)**
This is the biggest chunk because in a services engagement, schedule slip is what a
client actually notices. I look at three things and average them: the PM's own
project-level "Schedule Health" tag, how many tasks are individually tagged Red/Yellow
vs Green, and — this is the important one — how much the *critical path* specifically
is slipping (Variance on tasks flagged Critical). I weight critical-path slippage
because a non-critical task running late doesn't move the finish date; a critical one
does.

**Progress vs. plan (25%)**
This just compares % Complete to how much of the timeline has actually elapsed. A
project sitting at 40% done at the halfway mark is fine. One at 40% done with 70% of
the calendar gone is not — even if nobody's raised a flag about it yet. This is
actually the signal that catches the "quiet" version of a schedule problem, before it
shows up anywhere else.

**Blockers (20%)**
On Hold tasks, tasks flagged At Risk, and a keyword scan of the comment fields for
words like "pending," "TBD," "awaiting," "escalate." Not fancy NLP, just pattern
matching — but it works well enough on the kind of short, templated status comments
these plans actually contain.

**Stakeholder sentiment (15%)**
There's no sentiment field in the data, so this is the same keyword approach applied
to comment tone (positive words like "signed off," "approved" vs. negative ones like
"delay," "concern," "no response"). I want to be upfront that this is a rough
directional signal, not something I'd trust on its own — it's weighted lowest for
that reason, and every report says so explicitly.

**What about budget?** None of the sample workbooks have cost, hours, or invoicing
data, so I'm not scoring it. I didn't want to fake a fifth signal or just quietly drop
it — every report calls out "budget: not scored, no data" so leadership knows the gap
exists rather than assuming it was checked. Adding it later is a small change (see
README).

## Turning scores into a color
Each signal comes out 0–100, they get combined using the weights above, and:

- 75+ → Green
- 50–74 → Amber
- under 50 → Red

A couple of override rules sit on top of that, because averages can hide bad news:
- If more than 5% of active tasks are On Hold, the status is forced to Red regardless
  of the composite — that's a systemic blocking problem, not noise.
- If the PM's own Schedule Health tag is Red, the composite can't come out Green — it
  gets capped at Amber. I don't want the agent to override a PM's explicit red flag in
  the optimistic direction.
- If a workbook can't be parsed at all, the status is "Grey / Data Incomplete." It
  never guesses Green just because nothing came back.

## Assumptions worth flagging
- Dates in these files are Excel serial numbers — I convert those, and use the
  workbook's own "Today's Date" from the Summary tab when it's there, otherwise the
  actual run date.
- Blank or #UNPARSEABLE cells are treated as unknown, not zero and not "fine." Missing
  data should never quietly become a good score.
- I'm treating one workbook as one project, and the first/top-level task row as the
  project rollup where the sheet doesn't otherwise say.
- The keyword lists for blockers and sentiment are a first pass — they're pulled out
  into their own constants in the code specifically so they're easy to tune once
  there's more comment data to look at, per client if needed.
