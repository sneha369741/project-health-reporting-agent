const pptxgen = require("pptxgenjs");
let pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Professional Services";
pres.title = "Monthly Portfolio Health Review";

// Palette: Midnight Executive
const NAVY = "1E2761";
const ICE = "CADCFC";
const WHITE = "FFFFFF";
const RED = "C0362C";
const AMBER = "D98E04";
const GREEN = "1E7145";
const SLATE = "5B6B8C";
const INK = "1F2430";

const W = 13.33, H = 7.5;

function footer(slide, pageNum) {
  slide.addText(`Zycus Professional Services  |  Confidential`, {
    x: 0.5, y: H - 0.42, w: 6, h: 0.3, fontSize: 9, color: SLATE, fontFace: "Calibri",
  });
  slide.addText(`${pageNum}`, {
    x: W - 1, y: H - 0.42, w: 0.5, h: 0.3, fontSize: 9, color: SLATE, align: "right", fontFace: "Calibri",
  });
}

function ragColor(rag) {
  if (rag.startsWith("Green")) return GREEN;
  if (rag.startsWith("Amber")) return AMBER;
  if (rag.startsWith("Red")) return RED;
  return SLATE;
}

// ---------------------------------------------------------------- Slide 1
{
  let s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("Monthly Portfolio Health Review", {
    x: 0.9, y: 2.55, w: 11.5, h: 1.3, fontSize: 40, bold: true, color: WHITE, fontFace: "Cambria",
  });
  s.addText("Professional Services — Client Implementation Portfolio", {
    x: 0.9, y: 3.75, w: 11, h: 0.6, fontSize: 18, color: ICE, fontFace: "Calibri",
  });
  s.addText("July 2026  |  Prepared for Executive Review", {
    x: 0.9, y: 4.35, w: 11, h: 0.5, fontSize: 14, color: ICE, fontFace: "Calibri", italic: true,
  });
}

// ---------------------------------------------------------------- Slide 2: Portfolio snapshot
{
  let s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Portfolio Snapshot", { x: 0.6, y: 0.4, w: 8, h: 0.6, fontSize: 30, bold: true, color: INK, fontFace: "Cambria" });
  s.addText("Two active implementations — one Amber, one Red. Neither is Green this month.", {
    x: 0.6, y: 0.98, w: 11, h: 0.4, fontSize: 14, color: SLATE, fontFace: "Calibri",
  });

  const projects = [
    { name: "Meridian S2P Implementation", pm: "Arjun Mehta", rag: "Amber", score: 68.9, pct: 71, stage: "Configuration & Build" },
    { name: "Solvara S2P Implementation", pm: "Rohan Kapoor", rag: "Red", score: 45.5, pct: 44, stage: "Training Phase I" },
  ];
  let cardW = 5.55, gap = 0.5, startX = 0.6, y0 = 1.65;
  projects.forEach((p, i) => {
    let x = startX + i * (cardW + gap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: y0, w: cardW, h: 4.6, fill: { color: "F7F8FC" }, line: { type: "none" },
    });
    s.addText(p.name, { x: x + 0.35, y: y0 + 0.28, w: cardW - 0.7, h: 0.6, fontSize: 18, bold: true, color: INK, fontFace: "Cambria" });
    s.addText(`PM: ${p.pm}  |  Stage: ${p.stage}`, { x: x + 0.35, y: y0 + 0.95, w: cardW - 0.7, h: 0.35, fontSize: 11.5, color: SLATE, fontFace: "Calibri" });

    s.addText(p.rag.toUpperCase(), {
      x: x + 0.35, y: y0 + 1.5, w: cardW - 0.7, h: 0.55, fontSize: 26, bold: true, color: ragColor(p.rag), fontFace: "Cambria",
    });
    s.addText(`Composite score: ${p.score}/100`, { x: x + 0.35, y: y0 + 2.1, w: cardW - 0.7, h: 0.35, fontSize: 12.5, color: SLATE, fontFace: "Calibri" });

    // progress bar
    let barY = y0 + 2.65, barW = cardW - 0.7;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.35, y: barY, w: barW, h: 0.28, rectRadius: 0.14, fill: { color: "E4E7F0" }, line: { type: "none" } });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.35, y: barY, w: barW * (p.pct / 100), h: 0.28, rectRadius: 0.14, fill: { color: NAVY }, line: { type: "none" } });
    s.addText(`${p.pct}% complete`, { x: x + 0.35, y: barY + 0.32, w: barW, h: 0.3, fontSize: 11, color: SLATE, fontFace: "Calibri" });

    s.addText("Bottom line:", { x: x + 0.35, y: y0 + 3.45, w: barW, h: 0.3, fontSize: 12, bold: true, color: INK, fontFace: "Calibri" });
    let note = i === 0
      ? "Ahead on completion %, but critical-path tasks are slipping ~47 days on average — the schedule tag doesn't yet reflect it."
      : "Behind the planned pace (44% done vs 59% of time elapsed) with a Red PM-reported schedule status.";
    s.addText(note, { x: x + 0.35, y: y0 + 3.75, w: barW, h: 0.75, fontSize: 11.5, color: INK, fontFace: "Calibri" });
  });
  footer(s, 2);
}

// ---------------------------------------------------------------- Slide 3: Trend - the reporting gap
{
  let s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Trend: PM-Reported Status Understates Ground-Level Risk", {
    x: 0.6, y: 0.4, w: 12.1, h: 0.9, fontSize: 27, bold: true, color: INK, fontFace: "Cambria",
  });
  s.addText("Across both projects, the task-level data tells a more cautious story than the top-line status field.", {
    x: 0.6, y: 1.15, w: 11.5, h: 0.4, fontSize: 14, color: SLATE, fontFace: "Calibri",
  });

  s.addChart(pres.charts.BAR, [
    { name: "Red-tagged tasks", labels: ["Meridian"], values: [60] },
    { name: "Yellow-tagged tasks", labels: ["Meridian"], values: [146] },
    { name: "Green-tagged tasks", labels: ["Meridian"], values: [121] },
  ], {
    x: 0.6, y: 1.85, w: 5.6, h: 3.5, barDir: "col", barGrouping: "stacked",
    chartColors: [RED, AMBER, GREEN], showTitle: true, title: "Meridian: task RAG mix (PM status = Green)",
    titleFontSize: 13, showLegend: true, legendPos: "b", legendFontSize: 10,
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, chartArea: { fill: { color: "FFFFFF" } },
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.55, y: 1.85, w: 6.2, h: 3.5, rectRadius: 0.08, fill: { color: "F7F8FC" }, line: { type: "none" },
  });
  s.addText("What the numbers show", { x: 6.9, y: 2.05, w: 5.5, h: 0.4, fontSize: 15, bold: true, color: INK, fontFace: "Cambria" });
  s.addText([
    { text: "Meridian's project-level Schedule Health is reported Green, but 206 of 327 tagged tasks (63%) sit at Yellow or Red, and critical-path tasks are slipping ~47 days on average.", options: { bullet: true, breakLine: true, fontSize: 12.5 } },
    { text: "Solvara carries no On Hold tasks or blocker flags at the task level, yet is 15 points behind its planned pace and self-reports Red — the opposite gap direction.", options: { bullet: true, breakLine: true, fontSize: 12.5 } },
    { text: "Pattern: top-line RAG fields move on PM judgment calls; task-level signals move independently and sometimes lead them by weeks.", options: { bullet: true, fontSize: 12.5 } },
  ], { x: 6.9, y: 2.55, w: 5.5, h: 2.6, color: INK, fontFace: "Calibri", lineSpacingMultiple: 1.15 });
  footer(s, 3);
}

// ---------------------------------------------------------------- Slide 4: Emerging risks
{
  let s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Emerging Risks", { x: 0.6, y: 0.4, w: 8, h: 0.6, fontSize: 30, bold: true, color: INK, fontFace: "Cambria" });
  s.addText("Three patterns to watch over the next reporting cycle.", {
    x: 0.6, y: 0.98, w: 11, h: 0.4, fontSize: 14, color: SLATE, fontFace: "Calibri",
  });

  const risks = [
    {
      title: "Critical-path erosion is invisible at the summary level",
      body: "Meridian's critical-path tasks are slipping an average of 47 days while the project-level tag stays Green. If uncorrected, this gap surfaces as a missed go-live date with no early warning.",
    },
    {
      title: "Client-side sign-off is the recurring blocker language",
      body: "Comment text on both projects clusters around \"pending,\" \"TBD,\" and \"awaiting sign-off\" — almost always attributed to the client side, not Zycus delivery capacity.",
    },
    {
      title: "Solvara's pace deficit is widening without a matching blocker count",
      body: "44% complete against 59% of elapsed time, with zero flagged blockers — the shortfall looks like scope, resourcing, or engagement pace rather than a single stuck task.",
    },
  ];
  let y = 1.75;
  risks.forEach((r, i) => {
    s.addText(`0${i + 1}`, { x: 0.55, y: y - 0.05, w: 0.9, h: 0.55, fontSize: 22, bold: true, color: NAVY, fontFace: "Cambria" });
    s.addText(r.title, { x: 1.45, y: y, w: 11.2, h: 0.4, fontSize: 15.5, bold: true, color: INK, fontFace: "Calibri" });
    s.addText(r.body, { x: 1.45, y: y + 0.42, w: 11.2, h: 0.6, fontSize: 12.5, color: SLATE, fontFace: "Calibri" });
    y += 1.55;
  });
  footer(s, 4);
}

// ---------------------------------------------------------------- Slide 5: Recommendations
{
  let s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Recommendations", { x: 0.6, y: 0.4, w: 8, h: 0.6, fontSize: 30, bold: true, color: INK, fontFace: "Cambria" });
  s.addText("Where executive attention will have the most leverage this month.", {
    x: 0.6, y: 0.98, w: 11, h: 0.4, fontSize: 14, color: SLATE, fontFace: "Calibri",
  });

  const recs = [
    ["Require critical-path variance, not just the summary tag, in weekly PM reporting", "Closes the Green-status / Red-reality gap seen on Meridian before it becomes a date slip."],
    ["Escalate outstanding client sign-offs directly with Solvara and Meridian sponsors", "Both projects' blockers trace back to client-side approvals — a sponsor-level nudge outperforms PM-level follow-up."],
    ["Reset Solvara's delivery pace conversation this week", "A 15-point pace deficit with no active blockers points to a capacity or scope conversation, not a task fix."],
  ];
  let cardW = (11.3 - 0.8) / 3, x0 = 0.6, y0 = 1.85;
  recs.forEach((r, i) => {
    let x = x0 + i * (cardW + 0.4);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: y0, w: cardW, h: 3.4, fill: { color: "F7F8FC" }, line: { type: "none" },
    });
    s.addText(`0${i + 1}`, { x: x + 0.3, y: y0 + 0.25, w: 1, h: 0.5, fontSize: 20, bold: true, color: NAVY, fontFace: "Cambria" });
    s.addText(r[0], { x: x + 0.3, y: y0 + 0.85, w: cardW - 0.6, h: 1.3, fontSize: 13.5, bold: true, color: INK, fontFace: "Calibri" });
    s.addText(r[1], { x: x + 0.3, y: y0 + 2.15, w: cardW - 0.6, h: 1.1, fontSize: 11.5, color: SLATE, fontFace: "Calibri" });
  });
  footer(s, 5);
}

// ---------------------------------------------------------------- Slide 6: Closing / next steps
{
  let s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("Next Steps", { x: 0.9, y: 0.75, w: 8, h: 0.7, fontSize: 30, bold: true, color: WHITE, fontFace: "Cambria" });
  const steps = [
    "This report regenerates automatically each week directly from the live project plans — no manual chasing required.",
    "Executive sponsors receive the Meridian critical-path variance and Solvara pace numbers ahead of next steering call.",
    "Escalation owners follow up on outstanding client sign-offs within 5 business days.",
  ];
  let y = 1.85;
  steps.forEach((t, i) => {
    s.addText(`0${i + 1}`, { x: 0.9, y: y - 0.05, w: 0.7, h: 0.5, fontSize: 18, bold: true, color: ICE, fontFace: "Cambria" });
    s.addText(t, { x: 1.55, y: y, w: 10.8, h: 0.7, fontSize: 15, color: WHITE, fontFace: "Calibri" });
    y += 1.05;
  });
  s.addText("Prepared by the Project Health Reporting Agent  |  Professional Services", {
    x: 0.9, y: H - 0.75, w: 10, h: 0.35, fontSize: 11, color: ICE, italic: true, fontFace: "Calibri",
  });
}

pres.writeFile({ fileName: "Monthly_Portfolio_Health_Review.pptx" }).then(() => console.log("done"));
