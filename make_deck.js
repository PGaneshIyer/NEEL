const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.3 x 7.5
pres.author = "MAGNITO computational screening";
pres.title = "Fe-HREE Magnet Screening";

// ---- palette: two opposing sublattices (Fe up / RE down) drive the colour story
const NAVY = "101B33";   // dark ground
const NAVY2 = "1B2A4A";  // dark panel
const FE = "E4572E";     // iron / spin-up
const RE = "2E86AB";     // rare earth / spin-down
const GOLD = "F2B134";   // accent
const INK = "1A2233";    // body text on light
const MUTE = "5A6478";   // muted text
const PANEL = "EEF2F7";  // light panel
const WHITE = "FFFFFF";

const HF = "Cambria";    // headers (safe list)
const BF = "Calibri";    // body (safe list)

const M = 0.7;           // left margin
const W = 13.3 - 2 * M;  // usable width

// ---------- helpers ----------
function titleBar(slide, kicker, title, dark) {
  slide.addText(kicker, {
    x: M, y: 0.38, w: W, h: 0.26, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12, bold: true, charSpacing: 2,
    color: dark ? GOLD : FE,
  });
  slide.addText(title, {
    x: M, y: 0.66, w: W, h: 0.72, isTextBox: true, margin: 0,
    fontFace: HF, fontSize: 32, bold: true, color: dark ? WHITE : INK,
  });
}

function numCircle(slide, x, y, n, fill) {
  slide.addShape(pres.ShapeType.ellipse, {
    x, y, w: 0.42, h: 0.42, fill: { color: fill },
  });
  slide.addText(String(n), {
    x, y, w: 0.42, h: 0.42, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 14, bold: true, color: WHITE,
    align: "center", valign: "middle",
  });
}

function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.08, fill: { color: fill || PANEL },
  });
}

// ================= 1. TITLE =================
let s = pres.addSlide();
s.background = { color: NAVY };
s.addText("MAGNITO  ·  COMPUTATIONAL SCREENING", {
  x: M, y: 1.5, w: 9.2, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13, bold: true, charSpacing: 3, color: GOLD,
});
s.addText("Fe-rich Heavy-Rare-Earth\nMagnet Search", {
  x: M, y: 1.95, w: 9.2, h: 1.9, isTextBox: true, margin: 0,
  fontFace: HF, fontSize: 46, bold: true, color: WHITE, lineSpacing: 50,
});
s.addText("Search criteria, database landscape, the ferro- vs ferrimagnetic test, and an active-learning path forward",
  { x: M, y: 3.95, w: 8.6, h: 0.8, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 15, color: "AEBBD0" });
s.addText("Target: μ₀Ms > 2 T  ·  Tc > 550 K  ·  uniaxial anisotropy  ·  RE-lean", {
  x: M, y: 5.0, w: 9.2, h: 0.4, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13, italic: true, color: "8FA3C0",
});
// footer strip anchors the empty lower third
s.addText("706 paired DFT calculations  ·  353 compounds  ·  180 credible RE-TM exchange labels  ·  0 ferromagnets", {
  x: M, y: 6.45, w: 8.6, h: 0.35, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 11.5, charSpacing: 1, color: "6E819E",
});

// spin-pair motif, right side
const mx = 10.6;
s.addText("Fe / Co", { x: mx - 0.35, y: 1.75, w: 1.3, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 12, bold: true, color: FE, align: "center" });
["↑", "↑", "↑", "↑"].forEach((a, i) => {
  s.addText(a, { x: mx - 0.35 + i * 0.42, y: 2.05, w: 0.4, h: 0.85, isTextBox: true, margin: 0,
    fontFace: "Arial", fontSize: 40, bold: true, color: FE, align: "center" });
});
s.addText("Gd / Tb / Dy / Ho / Er / Tm", { x: mx - 0.9, y: 3.35, w: 2.9, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 12, bold: true, color: RE, align: "center" });
s.addText("↓", { x: mx + 0.25, y: 3.62, w: 0.4, h: 0.85, isTextBox: true, margin: 0,
  fontFace: "Arial", fontSize: 40, bold: true, color: RE, align: "center" });
s.addText("4f moment antiparallel\n→ ferrimagnet, not ferromagnet", {
  x: mx - 1.15, y: 4.55, w: 3.4, h: 0.7, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 11.5, color: "AEBBD0", align: "center" });
s.addNotes("Framing: the program wants >2 T. The physics obstacle is that heavy-RE 4f moments couple antiparallel to Fe, so the default outcome is a ferrimagnet with a reduced net moment.");

// ================= 2. TARGET AND OBSTACLE =================
s = pres.addSlide();
titleBar(s, "WHY THIS SEARCH IS HARD", "The target, and the rule that fights it", false);

card(s, M, 1.62, 5.7, 4.45);
s.addText("What a viable permanent magnet needs", {
  x: M + 0.32, y: 1.85, w: 5.1, h: 0.35, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 15, bold: true, color: INK });
const needs = [
  ["μ₀Ms > 2 T", "dense Fe/Co sublattice, little dilution"],
  ["Tᴄ > 550 K", "strong TM-TM exchange"],
  ["Uniaxial anisotropy", "needs the RE 4f crystal field"],
  ["RE-lean, no critical elements", "cost and supply"],
];
needs.forEach(([h, d], i) => {
  const y = 2.35 + i * 0.86;
  numCircle(s, M + 0.32, y, i + 1, RE);
  s.addText(h, { x: M + 0.92, y: y - 0.02, w: 4.5, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 14, bold: true, color: INK });
  s.addText(d, { x: M + 0.92, y: y + 0.26, w: 4.5, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12, color: MUTE });
});

card(s, 6.9, 1.62, 5.7, 4.45, NAVY2);
s.addText("The Campbell rule", {
  x: 7.22, y: 1.85, w: 5.1, h: 0.35, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 15, bold: true, color: GOLD });
s.addText("In metallic RE-TM intermetallics the 4f spin couples to Fe through a fixed chain:",
  { x: 7.22, y: 2.22, w: 5.05, h: 0.5, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12.5, color: "C6D2E4" });
s.addText("4f spin  ↔  own 5d   (parallel, on-site)\n5d  ↔  Fe 3d   (ANTIparallel, between sites)", {
  x: 7.22, y: 2.78, w: 5.05, h: 0.72, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13, bold: true, color: WHITE, lineSpacing: 20 });
s.addText([
  { text: "Heavy RE (Gd–Tm): ", options: { bold: true, color: WHITE } },
  { text: "J = L + S, so the total moment follows the spin → antiparallel to Fe → ", options: { color: "C6D2E4" } },
  { text: "ferrimagnet", options: { bold: true, color: FE } },
], { x: 7.22, y: 3.66, w: 5.05, h: 0.62, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12.5 });
s.addText([
  { text: "Light RE (Nd, Sm, Pr): ", options: { bold: true, color: WHITE } },
  { text: "J = L − S, so the total moment opposes the spin → parallel to Fe → ", options: { color: "C6D2E4" } },
  { text: "ferromagnet", options: { bold: true, color: GOLD } },
], { x: 7.22, y: 4.34, w: 5.05, h: 0.62, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12.5 });
s.addText("Consequence: a genuinely ferromagnetic Fe-HREE phase is the exception, not the target to assume. The screen must test it, not presume it.",
  { x: 7.22, y: 5.15, w: 5.05, h: 0.72, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12, italic: true, color: GOLD });
card(s, M, 6.1, W, 0.62, NAVY2);
s.addText("Outcome of the campaign: tested on 180 credible Fe/Co-Gd compounds - 180 ferrimagnets, 0 ferromagnets. The rule held everywhere; what varied, by 10x, was its strength.",
  { x: M + 0.25, y: 6.1, w: W - 0.5, h: 0.62, isTextBox: true, margin: 0, fontFace: BF, fontSize: 11, bold: true, color: GOLD, valign: "middle" });
s.addNotes("Campbell rule: 4f-5d-3d chain fixes the sign. Heavy RE gives ferrimagnetism; light RE gives net-parallel alignment. This is why every database 'FM' label on a Gd-Fe compound deserves suspicion.");

// ================= 3. SEARCH CRITERIA =================
s = pres.addSlide();
titleBar(s, "SCREEN DEFINITION", "Search criteria", false);
const crit = [
  ["Fe or Co ≥ 60 at.%", "a dense 3d sublattice is the only route to >2 T; dilute phases cannot reach it"],
  ["Contains one heavy RE", "Gd, Tb, Dy, Ho, Er, Tm — the 4f source of anisotropy"],
  ["Ternary compositions", "keeps the phase space synthesisable and the DFT tractable"],
  ["E above hull ≤ 0.2 eV/atom", "on, below, or metastably above — many real magnets are metastable"],
  ["Magnetic, or unknown", "moment > 0.3 μᴮ/atom; 'no data' is kept, not discarded"],
  ["Ordering decided by us", "no database can answer FM vs ferri — that is the calculation"],
];
crit.forEach(([h, d], i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = M + col * 6.25, y = 1.72 + row * 1.5;
  card(s, x, y, 5.75, 1.25, i >= 4 ? "E6EEF6" : PANEL);
  numCircle(s, x + 0.3, y + 0.26, i + 1, i >= 4 ? FE : RE);
  s.addText(h, { x: x + 0.92, y: y + 0.2, w: 4.6, h: 0.32, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 14.5, bold: true, color: INK });
  s.addText(d, { x: x + 0.92, y: y + 0.55, w: 4.65, h: 0.6, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, color: MUTE });
});
s.addText("Criteria 5 and 6 are deliberately permissive: an unlabelled compound is a candidate, not a rejection.",
  { x: M, y: 6.42, w: W, h: 0.4, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12, italic: true, color: FE });

// ================= 4. DATABASE LANDSCAPE =================
s = pres.addSlide();
titleBar(s, "WHERE WE LOOKED", "What each database can and cannot answer", false);
const rows = [
  [{ text: "Database", options: { bold: true } }, { text: "Hits", options: { bold: true } },
   { text: "Filters natively", options: { bold: true } }, { text: "Key limitation", options: { bold: true } }],
  ["GNoME", "749", "composition, stability", "no magnetic data at all; on-hull set only"],
  ["Materials Project", "178", "ordering label, hull, moment", "FM-initialised label; 4f frozen in core"],
  ["OQMD", "283", "hull, composition", "moments not exposed; structures via slow API"],
  ["Alexandria", "73", "elements, nelements", "moments response-only; server outages"],
  ["AFLOW", "29", "spin per atom, species", "no hull distance; thin RE-TM ternary coverage"],
];
s.addTable(rows, {
  x: M, y: 1.68, w: W, colW: [2.5, 0.95, 3.6, 4.85],
  fontFace: BF, fontSize: 12, color: INK, border: { type: "solid", color: "D5DDE8", pt: 1 },
  fill: { color: WHITE }, rowH: 0.42, valign: "middle",
});
card(s, M, 4.65, W, 1.55, NAVY2);
s.addText("The limitation they share", {
  x: M + 0.35, y: 4.85, w: 6, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 14, bold: true, color: GOLD });
s.addText("Every large database runs ONE spin-polarised calculation per structure, initialised ferromagnetically, with heavy-RE 4f frozen in the PAW core. So a “FM” label means “the Fe sublattice kept its moments” — never that the RE couples parallel. Nine FM-labelled Fe/Co-HREE candidates were found across all five databases; all nine contained Gd, the one heavy RE these codes treat explicitly.",
  { x: M + 0.35, y: 5.2, w: W - 0.7, h: 0.9, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12, color: "C6D2E4" });
s.addNotes("The nine FM-labelled hits being all-Gd is a tell: it is an artefact of which element is treated with explicit 4f, not a physical discovery.");


// ================= 4b. ANISOTROPY-BEARING DATASETS =================
s = pres.addSlide();
titleBar(s, "THE SCARCE COMMODITY", "Datasets that actually contain anisotropy", false);
const drows = [
  [{ text: "Source", options: { bold: true } }, { text: "What it uniquely has", options: { bold: true } },
   { text: "Role in this campaign", options: { bold: true } }],
  ["Novamag", "DFT K₁/MAE, exchange, Tc for RE-lean magnets", "train + validate the MAE surrogate; calibrate A₂⁰"],
  ["MAGNDATA", "~2,000 EXPERIMENTAL magnetic structures", "ground truth for the fm/ferri coupling sign"],
  ["C2DB", "systematic MAE + exchange (2D materials)", "benchmark an MAE model before trusting it in 3D"],
  ["Heusler set (Sanvito)", "~236k compositions, moments + est. Tc", "Tc training data; funnel-reporting template"],
  ["Nelson–Sanvito Tc", "~2,500 experimental Curie temperatures", "screen Tc before computing exchange constants"],
  ["NIMS MatNavi / MDR", "curated Nd-Fe-B and 1-12 experiment", "validation targets (registration required)"],
];
s.addTable(drows, {
  x: M, y: 1.66, w: W, colW: [2.7, 4.5, 4.7],
  fontFace: BF, fontSize: 11.5, color: INK, border: { type: "solid", color: "D5DDE8", pt: 1 },
  fill: { color: WHITE }, rowH: 0.4, valign: "middle",
});
card(s, M, 4.75, 7.6, 1.55, NAVY2);
s.addText("Why these are worth more per entry", {
  x: M + 0.32, y: 4.93, w: 7, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 14, bold: true, color: GOLD });
s.addText("The five large databases we screened carry composition, stability and a moment. None carries MAE, exchange constants or Tc at scale — the quantities a permanent magnet is actually judged on. Novamag is the only open source of systematic anisotropy, which is what makes an MAE surrogate trainable at all.",
  { x: M + 0.32, y: 5.28, w: 7.0, h: 0.9, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, color: "C6D2E4" });
card(s, 8.55, 4.75, 4.05, 1.55, "FCEDE8");
s.addText("Not open — do not plan around", {
  x: 8.85, y: 4.93, w: 3.5, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13.5, bold: true, color: FE });
s.addText("MPDS / Pauling File and Springer Materials hold the deepest experimental magnet record, but neither is openly accessible.",
  { x: 8.85, y: 5.28, w: 3.5, h: 0.9, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, color: "7A4034" });
s.addNotes("Novamag: CC-BY-4.0, auto-fetched from Zenodo record 3241267 (160 MB). MAGNDATA is the strongest available test of the coupling-sign protocol - every experimental RE-TM entry is a check.");

// ================= 5. FUNNEL =================
s = pres.addSlide();
titleBar(s, "FROM DATABASES TO CALCULATIONS", "Screening funnel", false);
const funnel = [
  ["554,055", "GNoME stable entries scanned", 11.9, RE],
  ["1,152", "unique candidate formulas across 5 databases", 9.6, RE],
  ["756", "with retrievable crystal structures", 7.6, "3E7FA6"],
  ["352", "compounds staged for DFT (24 native Gd + 328 Gd surrogates)", 5.8, FE],
  ["706", "paired fm / ferri VASP calculations", 4.2, FE],
];
funnel.forEach(([n, d, w, c], i) => {
  const y = 1.7 + i * 0.92;
  s.addShape(pres.ShapeType.roundRect, { x: M, y, w, h: 0.72, rectRadius: 0.06, fill: { color: c } });
  s.addText(n, { x: M + 0.28, y, w: 2.1, h: 0.72, isTextBox: true, margin: 0,
    fontFace: HF, fontSize: 22, bold: true, color: WHITE, valign: "middle" });
  s.addText(d, { x: M + 2.45, y, w: w - 2.6, h: 0.72, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 13, color: WHITE, valign: "middle" });
});
s.addText("726 parent compounds\ncollapse into 328\nsurrogate calculations",
  { x: 9.6, y: 4.5, w: 3.0, h: 1.0, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 13, bold: true, color: FE, align: "right" });
s.addText("Deduplicated on (substituted formula, space group); coupling transfers back to each parent by de Gennes scaling.",
  { x: 9.0, y: 5.55, w: 3.6, h: 0.8, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, color: MUTE, align: "right" });

// ================= 6. PROTOCOL =================
s = pres.addSlide();
titleBar(s, "THE DECIDING CALCULATION", "Two configurations, one energy difference", false);
const steps = [
  ["Pair every structure", "Two collinear spin-polarised PBE+U runs, identical except the SIGN of the initial Gd moment: fm (+7 μᴮ) and ferri (−7 μᴮ)."],
  ["Read the sign of ΔE", "ΔE = E(ferri) − E(fm).  Negative → ferrimagnetic ground state.  Positive → genuine FM RE-TM coupling."],
  ["Transfer across the series", "Tb–Tm ship as f-in-core potentials whose 4f cannot flip, so Gd is substituted onto every RE site and the result is carried back by de Gennes scaling, (gᴊ − 1)J."],
];
steps.forEach(([h, d], i) => {
  const x = M + i * 4.2;
  card(s, x, 1.7, 3.9, 2.5);
  numCircle(s, x + 0.3, 1.95, i + 1, FE);
  s.addText(h, { x: x + 0.3, y: 2.5, w: 3.3, h: 0.35, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 14.5, bold: true, color: INK });
  s.addText(d, { x: x + 0.3, y: 2.88, w: 3.35, h: 1.2, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, color: MUTE });
  if (i < 2) s.addText("→", { x: x + 3.92, y: 2.6, w: 0.3, h: 0.4, isTextBox: true, margin: 0,
    fontFace: "Arial", fontSize: 20, bold: true, color: RE, align: "center" });
});
card(s, M, 4.42, W, 1.85, NAVY2);
s.addText("Settings and controls", { x: M + 0.35, y: 4.6, w: 5, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 14, bold: true, color: GOLD });
s.addText([
  { text: "PBE+U  ", options: { bold: true, color: WHITE } },
  { text: "Gd 4f U = 6.7 / J = 0.7 eV (U_eff = 6)  ·  no U on metallic Fe  ·  LASPH, LMAXMIX = 6  ·  ENCUT 520  ·  8000 k-points·atom", options: { color: "C6D2E4" } },
], { x: M + 0.35, y: 4.95, w: W - 0.7, h: 0.4, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12 });
s.addText([
  { text: "Guards  ", options: { bold: true, color: WHITE } },
  { text: "statics on a common geometry so ΔE isolates exchange  ·  every run checked for SCF drift into the other spin state  ·  light RE pinned to f-in-core so only Gd carries a flippable 4f  ·  GdFe₂ (a known ferrimagnet) run as a protocol control", options: { color: "C6D2E4" } },
], { x: M + 0.35, y: 5.38, w: W - 0.7, h: 0.8, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12 });

// ================= 7. PILOT RESULT =================
s = pres.addSlide();
titleBar(s, "PILOT — 16 RUNS, 8 COMPOUNDS", "The protocol validates, and the database labels fall", false);
const prows = [
  [{ text: "Compound", options: { bold: true } }, { text: "Prototype", options: { bold: true } },
   { text: "ΔE per Gd (meV)", options: { bold: true } }, { text: "Ground state", options: { bold: true } },
   { text: "Net moment, ferri (μᴮ)", options: { bold: true } }],
  ["GdFe₂  (control)", "Laves C15", "−352", "ferrimagnetic", "−6.98"],
  ["GdAlFe₄", "CaCu₅ RT₄X", "−277", "ferrimagnetic", "−0.03"],
  ["GdGaFe₄", "CaCu₅ RT₄X", "−284", "ferrimagnetic", "0.24"],
  ["GdCo₄Si", "CaCu₅ RT₄X", "−155", "ferrimagnetic", "−3.14"],
  ["GdFe₄B", "CaCu₅ RT₄X", "−521", "ferrimagnetic", "1.08"],
  ["GdCo₄B", "CaCu₅ RT₄X", "−263", "ferrimagnetic", "−6.78"],
  ["Gd₂Fe₃Co", "Laves C14", "−329", "ferrimagnetic", "−7.53"],
  ["Gd₂Fe₁₂Ga₅C₂", "new, C2/m", "−107", "ferrimagnetic", "8.53"],
];
s.addTable(prows, {
  x: M, y: 1.66, w: W, colW: [2.85, 2.3, 2.35, 2.35, 2.05],
  fontFace: BF, fontSize: 11.5, color: INK, border: { type: "solid", color: "D5DDE8", pt: 1 },
  fill: { color: WHITE }, rowH: 0.33, valign: "middle",
});
card(s, M, 5.35, 6.05, 1.45, PANEL);
s.addText("Control passed", { x: M + 0.3, y: 5.52, w: 5.4, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13.5, bold: true, color: RE });
s.addText("GdFe₂ is experimentally a ferrimagnet and the protocol reproduces that by 352 meV/Gd — which is what licenses trusting the rest.",
  { x: M + 0.3, y: 5.85, w: 5.45, h: 0.75, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, color: MUTE });
card(s, 6.95, 5.35, 5.65, 1.45, "FCEDE8");
s.addText("Database FM labels were artefacts", { x: 7.25, y: 5.52, w: 5.1, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13.5, bold: true, color: FE });
s.addText("GdAlFe₄ and GdGaFe₄ (Alexandria) and GdCo₄Si (MP) were all FM-labelled. All three are ferrimagnetic by 155–284 meV/Gd — and the two RT₄X phases are almost fully compensated, so their true net moment is ≈ 0, not the ≈1.9 T the FM-initialised numbers implied.",
  { x: 7.25, y: 5.85, w: 5.1, h: 0.85, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, color: "7A4034" });
s.addNotes("8 of 8 pairs ferrimagnetic. 280 meV is far too large to be a convergence artefact. The compensation in RT4X is the practical kill: Fe sublattice ~14 muB cancels against Gd 7 muB x2 sites.");

// ================= 7b. SCALING THE SCREEN: WHY NUPDOWN =================
s = pres.addSlide();
titleBar(s, "SCALING THE SCREEN", "Why the fm/ferri energies had to be forced apart before they could be trusted", false);

card(s, M, 1.6, 6.1, 4.3, NAVY2);
s.addText("The problem: a plain SCF doesn't stay where you put it", {
  x: M + 0.3, y: 1.82, w: 5.5, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13.5, bold: true, color: GOLD });
s.addText("Each compound needs two static calculations - one initialised ferromagnetic, one ferrimagnetic - and the energy difference between them is the answer. At 353-compound scale, a plain unconstrained SCF too often drifts out of the state it was initialised in: LDA+U has several self-consistent solutions, and a simple collinear starting guess is not a strong enough anchor to hold either configuration in place through convergence.",
  { x: M + 0.3, y: 2.16, w: 5.5, h: 1.05, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10.5, color: "C6D2E4" });
s.addText("The fix: lock the total moment, then release it", {
  x: M + 0.3, y: 3.32, w: 5.5, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13.5, bold: true, color: GOLD });
s.addText("NUPDOWN fixes the total spin-up minus spin-down electron count, forcing the SCF to converge inside the intended basin. The target is derived from each element's own measured moment (not textbook values), never from a run already suspected of drifting.",
  { x: M + 0.3, y: 3.66, w: 5.5, h: 0.62, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10.5, color: "C6D2E4" });
const spinSteps = [
  ["Stage A - locked", "NUPDOWN set to the intended fm/ferri moment; hardened mixing (NELM, EDIFF, AMIX); CHGCAR-only restart (WAVECAR skipped - it once cost 700 GB and failed ~60 runs on disk pressure alone)"],
  ["Stage B - released", "NUPDOWN removed; one final unconstrained static from Stage A's charge density - the energy actually compared, since a locked run only proves a state exists, not that VASP would choose it freely"],
];
spinSteps.forEach(([h, d], i) => {
  const y = 4.42 + i * 0.66;
  numCircle(s, M + 0.3, y, i + 1, i === 0 ? RE : FE);
  s.addText(h, { x: M + 0.88, y: y - 0.02, w: 4.9, h: 0.22, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10.5, bold: true, color: WHITE });
  s.addText(d, { x: M + 0.88, y: y + 0.18, w: 4.9, h: 0.46, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 8.5, color: "AEBBD0" });
});

card(s, 6.95, 1.6, W - 6.25, 4.3, PANEL);
s.addText("The funnel this actually produced", {
  x: 7.23, y: 1.82, w: W - 6.8, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13.5, bold: true, color: INK });
const nupdownFunnel = [
  ["353", "compounds analysed", "static fm/ferri pair, Gd surrogate", WHITE, INK],
  ["95", "apparent ferromagnets", "naive, unconstrained SCF result - taken at face value, most are not real", "FCEDE8", "8A3B2E"],
  ["4", "survive NUPDOWN hardening", "measured-moment-derived locked rerun, released to a final unconstrained static", "FFF3D6", "8A6A1E"],
  ["0", "survive the release test", "3 of the 4 carried multi-eV exchange energies (LDA+U multi-minima artefact); the 4th, Co16Gd2Mn, was a metastable Mn-parallel-to-Gd basin that released to a ferrimagnet", NAVY2, WHITE],
];
nupdownFunnel.forEach(([n, label, note, fill, tcolor], i) => {
  const y = 2.22 + i * 0.96;
  card(s, 7.23, y, W - 6.9, 0.84, fill);
  s.addText(n, { x: 7.43, y: y + 0.1, w: 1.1, h: 0.64, isTextBox: true, margin: 0,
    fontFace: HF, fontSize: 30, bold: true, color: tcolor, valign: "middle" });
  s.addText(label, { x: 8.6, y: y + 0.1, w: W - 8.25, h: 0.28, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, bold: true, color: tcolor });
  s.addText(note, { x: 8.6, y: y + 0.38, w: W - 8.25, h: 0.42, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 8.6, color: tcolor });
});
s.addNotes("The 95->4 collapse on first hardening attempt actually went to ZERO credible - that first pass derived NUPDOWN from the same runs it was trying to fix (circular). Fixed by requiring a freely-converged reference or falling back to measured nominal per-element moments, split by high-spin/low-spin branch.");

// ================= 8. CAMPAIGN RESULTS (negative result, stated plainly) =================
s = pres.addSlide();
titleBar(s, "CAMPAIGN RESULTS", "No ferromagnet survives the release test; the false positive taught us the most", false);

card(s, M, 1.6, 5.3, 4.95, PANEL);
s.addText("The funnel, after every validity rule", {
  x: M + 0.28, y: 1.76, w: 4.8, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13, bold: true, color: INK });
const resFunnel = [
  ["353", "fm / ferri pairs staged", "Gd stand-in for Tb-Tm, PBE+U, NUPDOWN-locked then released", WHITE, INK],
  ["180", "credible exchange labels", "both configs converged, TM and spectator sublattices stable, RE sites equal, exchange energy on a physical scale", "FFF3D6", "8A6A1E"],
  ["180", "ferrimagnetic", "every credible pair: Gd antiparallel to Fe/Co, 28-371 meV per Gd", "E3F0F6", "1F5F7A"],
  ["0", "ferromagnetic", "the Campbell 4f-5d-3d chain holds in all 180 - no host, decoration or Mn trick broke it", NAVY2, WHITE],
];
resFunnel.forEach(([n, label, note, fill, tcolor], i) => {
  const y = 2.14 + i * 1.06;
  card(s, M + 0.28, y, 4.78, 0.94, fill);
  s.addText(n, { x: M + 0.45, y: y + 0.1, w: 1.0, h: 0.74, isTextBox: true, margin: 0,
    fontFace: HF, fontSize: 28, bold: true, color: tcolor, valign: "middle" });
  s.addText(label, { x: M + 1.5, y: y + 0.1, w: 3.5, h: 0.26, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, bold: true, color: tcolor });
  s.addText(note, { x: M + 1.5, y: y + 0.37, w: 3.5, h: 0.54, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 8.4, color: tcolor });
});

card(s, 6.35, 1.6, 6.25, 3.3, NAVY2);
s.addText("Co16Gd2Mn: the false positive, and why it was false", {
  x: 6.63, y: 1.76, w: 5.7, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13, bold: true, color: GOLD });
const fp = [
  ["Locked relaxation", "fm lower by 114.5 meV/Gd", "the ferri reference had Mn parallel to Gd - a metastable spectator basin, held in place by the NUPDOWN lock and -42 kbar of residual pressure"],
  ["Released statics", "ferri (Mn ∥ Co) lower by 208 meV/Gd", "E(ferri) = -146.088 eV vs E(fm) = -145.671 eV: a textbook Néel ferrimagnet once Mn is allowed to sit where it wants"],
  ["Two Mn, four spin states", "same ferrimagnet, 208 meV/Gd", "Gd↓ Mn↑↑Co lowest; Mn forced against Co costs 1.25 eV per cell; Mn–Mn exchange ferromagnetic (B − A = 180 meV). Mechanism 2 closed at every site (18f, 18h, 9d, 6c)"],
];
fp.forEach(([h, v, d], i) => {
  const y = 2.14 + i * 0.86;
  numCircle(s, 6.63, y + 0.04, i + 1, i === 1 ? FE : RE);
  s.addText(h, { x: 7.2, y, w: 2.4, h: 0.24, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10.5, bold: true, color: WHITE });
  s.addText(v, { x: 9.55, y, w: 2.9, h: 0.24, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10.5, bold: true, color: GOLD, align: "right" });
  s.addText(d, { x: 7.2, y: y + 0.26, w: 5.25, h: 0.56, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 8.4, color: "C6D2E4" });
});

card(s, 6.35, 5.05, 6.25, 1.5, "FCEDE8");
s.addText("What was learnt", { x: 6.63, y: 5.18, w: 5.7, h: 0.26, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 12, bold: true, color: FE });
s.addText("A constrained calculation proves a state exists, not that nature picks it. Three validity rules were added to the analysis - spectator-flip detection, per-config convergence, RE-site equality - and only energies that survive an unconstrained release are compared. Under those rules the 180 credible pairs are a clean, systematic measurement of RE-TM exchange, which is worth more than one unverified ferromagnet.",
  { x: 6.63, y: 5.45, w: 5.75, h: 1.05, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9.6, color: "7A4034" });
s.addNotes("Be explicit that the earlier deck claimed Co16Gd2Mn as FM. The release-stage comparison overturned it. The three validity rules now in analyze.py are the methodological product of that episode.");


// ================= 8-mn. WHY MN COULD NOT WORK =================
s = pres.addSlide();
titleBar(s, "THE Mn ARGUMENT, AND WHY IT FAILS", "The logic was sound as a syllogism; its premise was wrong, and even the corrected version cancels the magnet it tries to make", false);
card(s, M, 1.55, 5.6, 2.55, PANEL);
s.addText("The original logic", { x: M + 0.25, y: 1.68, w: 5.1, h: 0.28, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12.5, bold: true, color: INK });
const mnlog = [
  ["Gd is antiparallel to Co because its 5d sees parallel 3d neighbours (Campbell).", RE],
  ["Mn couples antiparallel to Co, so a Mn on the dumbbell next to Gd gives the 5d an antiparallel neighbour.", RE],
  ["The 5d–3d rule then flips Gd to the Co side: ferromagnet, 1.95 T projected.", RE],
];
mnlog.forEach(([t, c], i) => {
  numCircle(s, M + 0.25, 2.02 + i * 0.62, i + 1, c);
  s.addText(t, { x: M + 0.82, y: 2.0 + i * 0.62, w: 4.55, h: 0.56, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10, color: MUTE });
});
card(s, M, 4.25, 5.6, 2.5, "FCEDE8");
s.addText("What the calculations said", { x: M + 0.25, y: 4.38, w: 5.1, h: 0.28, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12.5, bold: true, color: FE });
const mnfail = [
  "Premise 2 is false here: Mn aligns WITH Co at 6c, 18f, 18h and 9d; opposing Co costs ~0.6 eV per Mn (state C, +1.25 eV for two).",
  "The +114.5 meV compared fm against the Mn-against-Co basin, held by the NUPDOWN lock and −42 kbar. Released: ferri lower by 208 meV/Gd, same as without Mn.",
  "One or two Mn cannot change what sixteen Co set: h, the summed shell polarisation, moved by < 10 %; the gap by 0 at two Mn.",
];
mnfail.forEach((t, i) => s.addText(t, { x: M + 0.25, y: 4.7 + i * 0.62, w: 5.15, h: 0.6, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.6, color: "7A4034", bullet: true }));
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/mn_compensation.png", x: 6.3, y: 1.55, w: 6.3, h: 3.55 });
card(s, 6.3, 5.2, 6.3, 1.55, NAVY2);
s.addText("The compensation argument: more Mn does not help either", { x: 6.55, y: 5.32, w: 5.9, h: 0.26, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12, bold: true, color: GOLD });
s.addText("Suppose Mn did oppose Fe/Co (true in Fe-rich hosts, R₂Fe₁₇₋ₓMnₓ). The Gd 5d follows the NET 3d spin of its shell: adding opposed Mn shrinks h and the gap, and Gd stays antiparallel to the net. At the crossover h → 0, but the net TM moment → 0 with it; past it Gd flips to oppose the Mn-dominated net. Gd is never parallel to the majority 3d moment, and the only point with no coupling is the point with no magnetisation. A Mn series measures a compensation curve, not a magnet.",
  { x: 6.55, y: 5.6, w: 5.95, h: 1.12, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.3, color: "C6D2E4" });
s.addNotes("Energies: Co16Gd2Mn released ferri (Mn||Co) -146.088 vs fm -145.671 eV; Mn-site twins released: 18f ferri_mnanti -145.886 vs fm -145.449; Co15Gd2Mn2 locked A -147.829, B -147.649, D -147.213, C -146.577 vs locked fm -147.414. Fe17Gd2H3 is the counter-example where the gap falls WITHOUT cancelling spin (H pushes the shell apart) - Ms survives but anisotropy is lost.");

// ================= 8a-i. NOT A NEIGHBOUR COUNT =================
s = pres.addSlide();
titleBar(s, "WHAT THE 180 LABELS SAY  ·  1 / 2", "The gap is not a neighbour count: the per-neighbour coupling itself varies 10-fold", false);
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/trends_neighbours.png", x: M, y: 1.55, w: 7.4, h: 5.18 });
card(s, 8.35, 1.55, 4.25, 5.18, PANEL);
s.addText("How to read it", { x: 8.6, y: 1.7, w: 3.8, h: 0.26, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12.5, bold: true, color: INK });
s.addText("Each point is one compound: the fm/ferri energy gap per Gd against the summed moment of the Fe/Co atoms touching that Gd. If the RE-TM coupling were a universal constant, the points would sit on one dotted line.",
  { x: 8.6, y: 2.0, w: 3.8, h: 1.1, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.5, color: MUTE });
s.addText("What it shows", { x: 8.6, y: 3.2, w: 3.8, h: 0.26, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12.5, bold: true, color: INK });
const nnPts = [
  "They span J_eff = 0.05 to 1.4 meV/μB²: at a fixed neighbour moment of ~25 μB the gap ranges from 110 to 370 meV.",
  "The strongest coupling sits at LOW neighbour moment (Fe/Y and Fe+Co hosts, upper left), the weakest at high neighbour moment (2-17 hydride, lower right).",
  "So neither coordination number nor TM moment predicts the gap. Something about the host, not the count, sets it.",
];
nnPts.forEach((t, i) => s.addText(t, { x: 8.6, y: 3.5 + i * 0.78, w: 3.85, h: 0.76, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.2, color: MUTE, bullet: true }));
s.addText("Conclusion: a fixed J_RT times a neighbour count - the usual mean-field shortcut - would be wrong by up to 10x across this chemistry.",
  { x: 8.6, y: 5.95, w: 3.85, h: 0.7, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10, bold: true, color: FE });

// ================= 8a-ii. GEOMETRY AND CLASS =================
s = pres.addSlide();
titleBar(s, "WHAT THE 180 LABELS SAY  ·  2 / 2", "Distance and chemistry set the coupling: short RE-TM bonds and mixed Fe+Co hosts couple hardest", false);
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/trends_geometry.png", x: M, y: 1.55, w: W, h: 4.3 });
card(s, M, 5.95, 5.8, 1.15, PANEL);
s.addText("Left: coupling falls as the Gd-TM distance grows (r = −0.61). Below 3.0 Å with 12 TM neighbours the Fe/Y hosts reach J_eff ≈ 1; above 3.15 Å - hydride, metalloid-shell and open cages - it drops to 0.05-0.4.",
  { x: M + 0.22, y: 6.02, w: 5.4, h: 1.0, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.5, color: INK });
card(s, 6.8, 5.95, 5.8, 1.15, PANEL);
s.addText("Right: mixed Fe+Co hosts have median J_eff 0.75 against 0.51 for pure Fe - Brooks' 5d-3d hybridisation argument seen on 27 compounds. The d-band centre and DOS at E_F add nothing once distance and the 5d moment are known (next slide).",
  { x: 7.02, y: 6.02, w: 5.4, h: 1.0, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.5, color: INK });
s.addNotes("Full OLS on log|dE|: 5d moment +0.34/SD, neighbour-sum +0.19, dilution +0.10, distance -0.04, d-band centre ~0; R2 0.63.");

// ================= 8b. ONE NUMBER PREDICTS THE GAP =================
s = pres.addSlide();
titleBar(s, "THE 5d METHOD", "Calibrated on 180 Gd pairs, the gap is read off a single calculation", false);
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/gap_vs_h.png",
  x: M, y: 1.55, w: 7.35, h: 5.1 });
card(s, 8.3, 1.55, 4.3, 2.55, NAVY2);
s.addText("Liebs & Fähnle (1993), used forward", { x: 8.55, y: 1.7, w: 3.9, h: 0.26, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 12, bold: true, color: GOLD });
s.addText("ΔE  =  2 · I₄f₋₅d · S₄f · S₅d", { x: 8.55, y: 2.02, w: 3.9, h: 0.4, isTextBox: true, margin: 0,
  fontFace: HF, fontSize: 18, bold: true, color: WHITE });
s.addText("h  =  −½ [ m₅d(ferri) + m₅d(fm) ]", { x: 8.55, y: 2.46, w: 3.9, h: 0.32, isTextBox: true, margin: 0,
  fontFace: HF, fontSize: 14, bold: true, color: "C6D2E4" });
s.addText("h is the part of the RE 5d moment tied to the TM neighbours; the part induced by the ion's own 4f flips with it and cancels. h is exactly what a 4f-free host (Y, or f-in-core Nd/Sm) reports as its RE moment.",
  { x: 8.55, y: 2.84, w: 3.9, h: 0.9, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9, color: "C6D2E4" });
s.addText("|ΔE| = 1574 · h meV    r = 0.89    I₄f₋₅d ≈ 225 meV", { x: 8.55, y: 3.72, w: 3.9, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 10.5, bold: true, color: GOLD });
card(s, 8.3, 4.25, 4.3, 2.45, PANEL);
s.addText("Why it matters", { x: 8.55, y: 4.38, w: 3.9, h: 0.26, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 12, bold: true, color: INK });
const whyPts = [
  "Circles mark the compounds with a measured exchange constant; stars are the gap their experimental J_RT implies. GdFe₂: J_RT 2.97 (ours) vs 2.99 × 10⁻²² J (expt). Validation slide follows.",
  "Beats the raw ground-state 5d moment as a predictor (r 0.80 → 0.89) because it removes the 4f-induced part.",
  "Turns an fm/ferri pair with 4f in the valence into ONE f-in-core run: J_RT, the RE molecular field B_RT = ΔE/2μ and T* = ΔE_RE/2k_B all follow.",
  "Applied to Tao et al. 2026 (diamonds): Sm hosts predicted at 190-220 meV per Sm, T* 1100-1260 K - the Sm anisotropy stays locked to Fe up to Tc, consistent with their ferrimagnetic ground states.",
];
whyPts.forEach((t, i) => {
  s.addText(t, { x: 8.55, y: 4.64 + i * 0.5, w: 3.95, h: 0.5, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 8, color: MUTE, bullet: true });
});
s.addNotes("Two outliers are circled: Gd2Fe17H3 far below the line (artifact suspect, in the suspects batch), and one Fe host far above (CFe17Gd2 - fm side suspect). Both are being re-run locked->released.");

// ================= 8c. VALIDATION AGAINST PRIOR WORK =================
s = pres.addSlide();
titleBar(s, "VALIDATION AGAINST PRIOR WORK", "Where literature gives a number, the campaign reproduces it", false);
const valRows = [
  [{ text: "Quantity / rule", options: { bold: true } }, { text: "Literature", options: { bold: true } },
   { text: "This campaign", options: { bold: true } }, { text: "Status", options: { bold: true } }],
  ["GdFe₂ RE-TM exchange J_RT", "2.99 × 10⁻²² J (Liebs, Hummler, Fähnle 1992; expt. molecular field)", "2.97 × 10⁻²² J from the fm/ferri gap (352 meV/Gd)", "reproduced"],
  ["ΔE ∝ S₅d (Liebs & Fähnle 1993)", "shown on 3 compounds, ab initio", "holds on 180 compounds, r = 0.89; I₄f₋₅d ≈ 225 meV", "confirmed at scale"],
  ["Campbell 4f-5d-3d sign rule", "heavy RE always antiparallel to Fe/Co", "180 / 180 credible pairs antiparallel; 0 exceptions", "confirmed"],
  ["Duc's early-TM rule", "V/Ti in GdFe₁₂₋ₓVₓ doubles A_GdFe (x = 0 → 4)", "early-TM hosts J_eff ×0.97 of the Fe baseline (CI 0.88-1.07); GdFe₁₀V₂ J_RT 1.52 vs 1.30 expt", "not resolved - needs a concentration series"],
  ["Brooks: Co strengthens 5d-3d coupling", "Co-based > Fe-based molecular fields", "Fe+Co hosts J_eff 0.75 vs Fe 0.51, Co 0.57", "confirmed"],
  ["Tao et al. 2026: Mn/Cr as weak-coupling mediators", "Sm(Fe,Mn,Cr) hosts; RE moments −0.24 … −0.33 μB (f-frozen)", "same h on our line → Gd-equivalent gaps 380-520 meV; hosts are strongly coupled, not weakly", "reinterpreted"],
  ["Mn-mediated RE-TM ferromagnetism (our own claim)", "Co16Gd2Mn, +114.5 meV/Gd (locked)", "Mn ∥ Co ferrimagnet by 208 meV/Gd after release", "rejected"],
];
s.addTable(valRows, {
  x: M, y: 1.6, w: W, colW: [3.0, 3.2, 4.0, 1.7],
  fontFace: BF, fontSize: 9.5, color: INK, border: { type: "solid", color: "D5DDE8", pt: 0.75 },
  fill: { color: WHITE }, rowH: 0.5, valign: "middle",
});
card(s, M, 5.85, W, 0.85, PANEL);
s.addText("Learnt: the campaign is a quantitative instrument, not a yes/no screen. It reproduces the one measured RE-TM exchange constant it can be checked against, generalises the two-sublattice theory from three compounds to 180, and corrects its own headline when the release test disagrees.",
  { x: M + 0.25, y: 5.85, w: W - 0.5, h: 0.85, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, italic: true, color: INK, valign: "middle" });
s.addNotes("Liebs-Hummler-Fahnle PRB 46, 11201 (1992); Liebs-Fahnle JMMM 128, L8 (1993); Duc 1998 review; Brooks-Johansson 5d-3d hybridisation; Tao et al. arXiv 2608.25270.");

// ================= 8c-ii. VALIDATION PLOT =================
s = pres.addSlide();
titleBar(s, "VALIDATION AGAINST PRIOR WORK  ·  THE NUMBERS", "Four exchange constants with experimental values: three within 25 %, the control exact", false);
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/validation_jrt.png", x: M, y: 1.55, w: 6.6, h: 5.05 });
card(s, 7.6, 1.55, 5.0, 5.05, PANEL);
s.addText("What is compared", { x: 7.85, y: 1.7, w: 4.5, h: 0.26, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12.5, bold: true, color: INK });
s.addText("J_RT in the Liebs-Fähnle two-sublattice convention, ΔE = 4 J_RT S_R S_T Z_RT, computed from our fm/ferri gap with the compound's own TM moment and neighbour count - no fitted parameter.",
  { x: 7.85, y: 2.0, w: 4.55, h: 0.95, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.5, color: MUTE });
const vPts = [
  ["GdFe₂", "2.97 vs 2.99 - the protocol control, reproduced to 1 %."],
  ["Gd₂Fe₁₄B", "1.84 vs 1.46 from inelastic neutron scattering - 26 % high; LHF's own LMTO value is 1.46, so the gap is in our Z_RT bookkeeping for the two inequivalent Gd sites."],
  ["GdFe₁₀V₂", "1.52 vs Duc's A_GdFe 1.30 at x = 2 - 17 % high, and inside the spread of Duc's own series (1.13-2.25)."],
  ["Gd₂Fe₁₇N₂ ↔ Ho₂Fe₁₇", "1.21 vs 1.2-1.4 (Ho₂Fe₁₇, INS). Open marker: a nitride compared to a binary, because no Gd₂Fe₁₇ pair survived the validity rules."],
];
vPts.forEach(([h, d], i) => {
  const y = 3.0 + i * 0.78;
  s.addText(h, { x: 7.85, y, w: 4.5, h: 0.22, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10, bold: true, color: RE });
  s.addText(d, { x: 7.85, y: y + 0.21, w: 4.55, h: 0.56, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.6, color: MUTE });
});
s.addText("Learnt: the campaign's exchange energies are on the experimental scale, biased ≤ 25 % high where the RE sites are inequivalent. Good enough to rank hosts; not yet good enough to resolve Duc's 15-20 % early-TM effect, which needs a concentration series on one lattice.",
  { x: M, y: 6.7, w: W, h: 0.5, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10, italic: true, color: INK });
s.addNotes("Sources: Liebs-Hummler-Fahnle PRB 46 11201 (1992) Table III (Loewenhaupt INS); Liebs-Fahnle JMMM 128 L8 (1993); Duc et al. JMMM 177-181 1107 (1998) Table 1. Ho2Fe17 used as the 2-17 reference since J_RT in this convention is nearly RE-independent.");

// ================= 8d. DESIGN-PRINCIPLE AUDIT =================
s = pres.addSlide();
titleBar(s, "DESIGN PRINCIPLES, AUDITED", "Every rule used to build permanent magnets, checked against the same 180 labels", false);
const dpRows = [
  [{ text: "Principle", options: { bold: true } }, { text: "What it predicts", options: { bold: true } },
   { text: "What the dataset shows", options: { bold: true } }, { text: "Verdict", options: { bold: true } }],
  ["Heavy RE couples antiparallel (Campbell)", "no FM Fe/Co-heavy-RE compound", "180/180 ferrimagnetic", "confirmed"],
  ["Gap scales with RE 5d spin (Liebs-Fähnle)", "ΔE ∝ S₅d, host-independent I₄f₋₅d", "r = 0.89 on h; d-band centre adds nothing", "confirmed"],
  ["de Gennes scaling across the RE series", "ΔE_RE = ΔE_Gd · (g−1)J / 3.5", "assumed to project Tb-Tm and Nd/Sm; explicit-4f Tb-Tm runs under way", "in test"],
  ["Fe-rich, dense lattices for Ms", "Ms ceiling set by Fe density", "best Gd hosts 0.9-1.06 T; light-RE projection ceiling ≈ 1.75 T (0 K, no SOC)", "confirmed"],
  ["Light RE (J = L − S) adds to Ms", "Nd/Sm moment parallel to Fe", "projected +0.6-0.9 T over Gd; 20 f-in-core runs queued", "in test"],
  ["Interstitial N / C raise Ms and Tc", "lattice expansion, stronger Fe-Fe", "Gd₂Fe₁₇N₂ is the top Ms host; C analogues close behind", "confirmed"],
  ["Interstitial H is harmless", "mild expansion only", "Gd₂Fe₁₇H₃ gap 28 meV (×0.10): H in the RE shell nearly switches off RE-TM coupling - one compound, re-running", "rejected if it survives release"],
  ["Early-TM stabilisers (Ti, V, Zr, Nb) help", "stabilise 1:12-type cells, stronger coupling (Duc)", "coupling ×0.97 of baseline, no effect resolved; hull: Fe₅GdV on hull, Ti variants 12-19 meV above", "stability yes, coupling unresolved"],
  ["Partial Co for Tc and coupling", "Co raises Tc and RE-TM field", "Fe+Co hosts strongest J_eff (0.75); Ms cost small at low Co", "confirmed"],
  ["Mn as a sign-flipping mediator", "Mn ∥ RE breaks the antiparallel rule", "Mn ∥ Co in every released state", "rejected"],
  ["Metalloid-rich cages (B, Si, Ga, Al in RE shell)", "stabilise structures cheaply", "systematically lower gaps - anisotropy decouples first", "use with care"],
];
s.addTable(dpRows, {
  x: M, y: 1.55, w: W, colW: [3.1, 2.9, 4.4, 1.5],
  fontFace: BF, fontSize: 8.8, color: INK, border: { type: "solid", color: "D5DDE8", pt: 0.75 },
  fill: { color: WHITE }, rowH: 0.4, valign: "middle",
});
s.addText("Learnt: most principles hold in direction but their magnitudes differ by an order of magnitude, one (early TM) is not resolved by cross-host data, and only the 5d-spin rule is quantitative enough to rank candidates.",
  { x: M, y: 6.62, w: W, h: 0.5, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10.5, italic: true, color: INK });

// ================= 8d-ii. EFFECT SIZES =================
s = pres.addSlide();
titleBar(s, "DESIGN PRINCIPLES, AUDITED  ·  EFFECT SIZES", "The same rules as numbers: how far each lever moves the RE-TM coupling from the Fe baseline", false);
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/principles_effects.png", x: M, y: 1.55, w: 7.5, h: 4.6 });
card(s, 8.45, 1.55, 4.15, 4.6, PANEL);
s.addText("Reading the chart", { x: 8.7, y: 1.7, w: 3.7, h: 0.26, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12.5, bold: true, color: INK });
s.addText("Median J_eff of the compounds carrying a lever, divided by the median of all 123 Fe-only hosts; bars are bootstrap 95 % intervals. Blue = strengthens coupling, red = weakens, grey = not resolved.",
  { x: 8.7, y: 2.0, w: 3.7, h: 0.95, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.3, color: MUTE });
const ePts = [
  ["×1.48  partial Co", "the only lever with a large, resolved positive effect"],
  ["×1.12  all-Co", "modest; Co also lowers Ms, so partial Co is the useful form"],
  ["×0.97  early TM", "Duc's effect is not visible across different hosts; it needs a series on one lattice"],
  ["×0.86  distance > 3.15 Å", "open cages weaken coupling, consistent with the 5d picture"],
  ["×0.10  H interstitial", "one compound, under re-check; if real, the strongest lever of all - in the wrong direction"],
];
ePts.forEach(([h, d], i) => {
  const y = 3.05 + i * 0.6;
  s.addText(h, { x: 8.7, y, w: 3.7, h: 0.22, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.8, bold: true, color: i < 2 ? RE : (i === 2 ? MUTE : FE) });
  s.addText(d, { x: 8.7, y: y + 0.21, w: 3.75, h: 0.4, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.4, color: MUTE });
});
s.addText("Learnt: of the levers the field uses, only partial Co and short RE-TM bonds measurably raise the RE-TM coupling in this dataset. Metalloids are neutral on average; their harm is specific to sitting in the RE shell. The early-TM rule is a stability lever until a concentration series says otherwise.",
  { x: M, y: 6.3, w: W, h: 0.75, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10, italic: true, color: INK });

// ================= 8e. FROM DATA TO NEW COMPOSITIONS =================
s = pres.addSlide();
titleBar(s, "HYPOTHESIS: THE LEVERS COMPOSE", "If the measured levers add, the dataset's strongest hosts become new light-RE magnets", false);
const leverFunnel = [
  ["180", "credible Gd hosts", "the labelled dataset", WHITE, INK],
  ["96", "project ≥ 1.4 T with Nd", "Fe sublattice moment + free-ion Nd, same cell", "FFF3D6", "8A6A1E"],
  ["70", "not a known prototype", "drop Nd₂Fe₁₄B, 2-17(N,C,H), Laves, Th₂Zn₁₇, the Mn family", "FFF3D6", "8A6A1E"],
  ["29", "strongest coupling, Fe-rich", "J_eff ≥ 0.5 or gap ≥ 300 meV; 1:9 family by 3 representatives", "E3F0F6", "1F5F7A"],
  ["20", "survive the hull, Nd + Sm", "MACE-MP-0 vs 394 MP competitors, same model; Nd within 12 meV/atom", NAVY2, WHITE],
];
leverFunnel.forEach(([n, label, note, fill, tcolor], i) => {
  const y = 1.6 + i * 0.98;
  card(s, M, y, 5.3, 0.86, fill);
  s.addText(n, { x: M + 0.18, y: y + 0.08, w: 1.0, h: 0.7, isTextBox: true, margin: 0,
    fontFace: HF, fontSize: 26, bold: true, color: tcolor, valign: "middle" });
  s.addText(label, { x: M + 1.25, y: y + 0.1, w: 3.95, h: 0.26, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, bold: true, color: tcolor });
  s.addText(note, { x: M + 1.25, y: y + 0.37, w: 3.95, h: 0.46, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 8.6, color: tcolor });
});
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/light_re_hull.png",
  x: 6.3, y: 1.55, w: 6.3, h: 4.4 });
card(s, 6.3, 6.0, 6.3, 0.62, NAVY2);
s.addText("Generation rule: host with gap ≥ 250 meV or J_eff ≥ 0.5  ×  Gd → {Nd, Sm}  ×  keep Co/early-TM variants  ×  no H, no metalloid in the RE shell  →  MACE/MP hull  →  one f-in-core VASP run. 29 hosts → 58 structures → 20 survivors; the rule extends to Pr, partial Co and N interstitials once this batch confirms it.",
  { x: 6.5, y: 6.0, w: 5.95, h: 0.62, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.3, color: "C6D2E4", valign: "middle" });
s.addText("First test of the hypothesis: the Nd cost is systematic (20-35 meV/atom for the larger ion), so only the densest Fe hosts stay on the hull; Sm is nearly free. Whether coupling and Ms carry over is what the 20 queued runs decide.",
  { x: M, y: 6.62, w: W, h: 0.45, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10.5, italic: true, color: INK });

// ================= 8f. THE Nd/Sm BATCH =================
s = pres.addSlide();
titleBar(s, "THE Nd / Sm BATCH - 20 RUNS QUEUED", "Each host carries a reason from the data, a stability check, and a prediction to be tested", false);
const ndRows = [
  [{ text: "Host (Gd parent)", options: { bold: true } }, { text: "Prototype", options: { bold: true } },
   { text: "J_eff", options: { bold: true } }, { text: "Ms → Nd / Sm (T)", options: { bold: true } },
   { text: "E_hull Nd / Sm (meV/at)", options: { bold: true } }, { text: "T* Sm (K)", options: { bold: true } },
   { text: "Why it is in the batch", options: { bold: true } }],
  ["Fe₅GdSi", "Immm (new)", "0.50", "1.74 / 1.56", "+1 / −6", "700", "highest Ms of any stable new host; Si outside the RE shell"],
  ["Al₂Fe₁₀Gd", "Immm (new)", "0.54", "1.68 / 1.51", "+3 / −3", "745", "same Fe framework, Al variant; tests the metalloid-shell rule"],
  ["Fe₅GdV", "Immm (new)", "0.48", "1.62 / 1.44", "+7 / +2", "715", "early-TM lever built in (Duc); 1:12-like chemistry"],
  ["Fe₁₀GdY", "Pmmm (new)", "0.52", "1.64 / 1.47", "+11 / +3", "825", "dense Fe, Y dilutes RE cost"],
  ["CoFe₆GdY", "Cm (new)", "0.97", "1.59 / 1.37", "+10 / −5", "955", "strongest coupling at Ms > 1.5 T; partial Co"],
  ["Co₂Fe₁₂GdY₃", "Cm (new)", "1.04", "1.44 / 1.33", "+1 / −8", "1005", "anisotropy-locking host; on the hull"],
  ["CoFe₁₃GdY₃", "R3m (new)", "1.03", "1.42 / 1.31", "+7 / −3", "1030", "Fe/Y family, 12-fold RE coordination at 2.97 Å"],
  ["Fe₁₄GdY₃", "R3m (new)", "1.06", "1.40 / 1.29", "+11 / −1", "1070", "Co-free control for the two above"],
  ["Fe₉GdLuZr", "R3m (new)", "0.51", "1.48 / 1.27", "+9 / −3", "810", "1:9 family representative with Zr stabiliser"],
  ["Co₉Fe₅Gd₄", "R-3m (new)", "0.69", "1.69 / 1.23", "+3 / −16", "725", "RE-rich control: high Nd moment count, lowest Tc expected"],
];
s.addTable(ndRows, {
  x: M, y: 1.55, w: W, colW: [1.55, 1.3, 0.7, 1.55, 1.75, 0.95, 4.1],
  fontFace: BF, fontSize: 8.8, color: INK, border: { type: "solid", color: "D5DDE8", pt: 0.75 },
  fill: { color: WHITE }, rowH: 0.36, valign: "middle",
});
card(s, M, 5.75, 5.8, 1.1, NAVY2);
s.addText("What each run returns", { x: M + 0.25, y: 5.85, w: 5.3, h: 0.25, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 11.5, bold: true, color: GOLD });
s.addText("One ISIF=3 relaxation per compound with f-in-core Nd_3 / Sm_3 (no 4f to flip, no +U): relaxed volume, Fe/Co moments → Ms, and h → predicted gap, T*, B_RT. Prediction on record before the run: h from each Gd parent's pair.",
  { x: M + 0.25, y: 6.1, w: 5.3, h: 0.72, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.8, color: "C6D2E4" });
card(s, 6.8, 5.75, 5.8, 1.1, "FCEDE8");
s.addText("Honest ceiling", { x: 7.05, y: 5.85, w: 5.3, h: 0.25, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 11.5, bold: true, color: FE });
s.addText("Projections are 0 K PBE without SOC and run ≈ 0.3 T high against experiment (Nd₂Fe₁₇Nₓ: 2.04 projected vs ~1.5 T). None of the 20 beats NdFe₁₂N (1.66 T, Tc 823 K) or Sm(Fe,Co)₁₂ (1.78 T). Their value is as new, hull-stable Fe-rich hosts with coupling strong enough to carry RE anisotropy - the ingredient the 2 T target has lacked.",
  { x: 7.05, y: 6.1, w: 5.3, h: 0.72, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.6, color: "7A4034" });
s.addNotes("Job 59642825, 20 nodes, 3 h, regular QOS, submitted 2026-10-10 11:58. Reader: light_re_results.py. Tc is NOT in this batch - it needs an Fe-Fe Heisenberg mapping, planned as the next step for survivors.");

// ================= 8g. NEW HYPOTHESES =================
s = pres.addSlide();
titleBar(s, "NEW HYPOTHESES", "What prior studies plus 180 labels let us state - each falsifiable with runs already queued or cheap to add", false);
const hyp = [
  ["H1", "The RE-TM gap of any host is predictable from a 4f-free calculation", "h measured in the f-in-core Nd/Sm run equals h extracted from the Gd pair of the same host, and 1574·h reproduces the Gd gap within 20 %. Falsified if the 20 queued runs scatter off the line.", RE],
  ["H2", "Usable anisotropy needs T* above Tc, and T* is a host property", "Hosts with gap < ~150 meV per Gd (H-loaded, metalloid-shell, open cages) lose RE anisotropy below Tc regardless of RE choice. Testable on the suspects batch and by SOC runs on two low-gap vs two high-gap hosts.", FE],
  ["H3", "Partial Co in Fe/Y hosts buys coupling at almost no Ms cost", "Fe+Co hosts have 50 % higher J_eff; at ≤ 15 % Co the Fe moment barely drops. Prediction: CoFe₆NdY and Co₂Fe₁₂NdY₃ show higher h than Fe₁₄NdY₃ at similar Ms. Direct comparison inside the batch.", "7B4FA3"],
  ["H4", "The compound lever is light RE + early TM + N interstitial on a dense new host", "Light RE, partial Co and N are each supported by the data; early TM is a stability lever whose coupling effect is unresolved. None has been combined on a hull-stable new prototype. Fe₅(Nd,Sm)(Si,V) Immm with N on the largest void is the first test - MACE hull, then one run.", GOLD],
  ["H5", "Interstitial choice is a coupling decision, not just a volume decision", "N and C expand the lattice and keep the gap; H in the RE shell collapses it. Hypothesis: the interstitial's site relative to the RE, not its size, decides. Test: H vs N on the same 2-17 cell, same site.", "3E7FA6"],
];
hyp.forEach(([tag, h, d, c], i) => {
  const y = 1.55 + i * 1.03;
  card(s, M, y, W, 0.92, PANEL);
  s.addShape(pres.ShapeType.roundRect, { x: M + 0.15, y: y + 0.16, w: 0.7, h: 0.6, rectRadius: 0.08, fill: { color: c } });
  s.addText(tag, { x: M + 0.15, y: y + 0.16, w: 0.7, h: 0.6, isTextBox: true, margin: 0,
    fontFace: HF, fontSize: 16, bold: true, color: WHITE, align: "center", valign: "middle" });
  s.addText(h, { x: M + 1.05, y: y + 0.1, w: W - 1.3, h: 0.28, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, bold: true, color: INK });
  s.addText(d, { x: M + 1.05, y: y + 0.4, w: W - 1.3, h: 0.5, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9, color: MUTE });
});
s.addText("Each hypothesis names its own disproof. H1 and H3 are decided by the batch now in the queue.",
  { x: M, y: 6.72, w: W, h: 0.35, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10.5, italic: true, color: INK });


s = pres.addSlide();
titleBar(s, "EXTENDING THE GD DATASET", "Using Campbell's rule to predict the rest of the series", false);

card(s, M, 1.66, 5.35, 4.6, NAVY2);
s.addText("What the Gd calculation gives you", {
  x: M + 0.32, y: 1.88, w: 4.7, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 14, bold: true, color: GOLD });
s.addText("ΔE from the fm/ferri pair is the RE-TM exchange energy itself. Because the sign is fixed by the 4f-5d-3d chain and only the 4f spin magnitude changes down the series, one Gd pair predicts all six heavy rare earths.",
  { x: M + 0.32, y: 2.26, w: 4.7, h: 1.0, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12, color: "C6D2E4" });
s.addText("coupling strength", { x: M + 0.32, y: 3.28, w: 4.7, h: 0.2, isTextBox: true,
  margin: 0, fontFace: BF, fontSize: 9.5, charSpacing: 1, color: "7A8DA8" });
s.addText("J(RE–TM)   ∝   (g_J − 1) J", {
  x: M + 0.32, y: 3.46, w: 4.7, h: 0.38, isTextBox: true, margin: 0,
  fontFace: HF, fontSize: 18, bold: true, color: WHITE });
s.addText("Tc contribution  —  de Gennes factor", { x: M + 0.32, y: 3.86, w: 4.7, h: 0.2,
  isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.5, charSpacing: 1, color: "7A8DA8" });
s.addText("G  =  (g_J − 1)² J(J + 1)", {
  x: M + 0.32, y: 4.04, w: 4.7, h: 0.36, isTextBox: true, margin: 0,
  fontFace: HF, fontSize: 17, bold: true, color: GOLD });
s.addText("Gd 15.75 · Tb 10.5 · Dy 7.08 · Ho 4.5 · Er 2.55 · Tm 1.17",
  { x: M + 0.32, y: 4.42, w: 4.7, h: 0.26, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, color: "8FA3C0" });
s.addText("net moment", { x: M + 0.32, y: 4.74, w: 4.7, h: 0.2, isTextBox: true,
  margin: 0, fontFace: BF, fontSize: 9.5, charSpacing: 1, color: "7A8DA8" });
s.addText("M_net  =  M_TM  −  n_RE × g_J·J", {
  x: M + 0.32, y: 4.92, w: 4.7, h: 0.36, isTextBox: true, margin: 0,
  fontFace: HF, fontSize: 17, bold: true, color: WHITE });
s.addText("The Fe sublattice moment carries over unchanged; only the RE terms rescale — so both Tc and net moment are predictable for Tb–Tm without new calculations.",
  { x: M + 0.32, y: 5.34, w: 4.7, h: 0.8, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, color: "C6D2E4" });

const strat = [
  ["Rank by uncompensated moment, not by FM", "For every Gd result, evaluate M_TM − n_RE·g_J·J across the series. High Fe:RE ratios (2-17, 1-12) leave a large residual; RT₄X compensates to ≈ 0. This reprioritises the whole candidate list at zero DFT cost."],
  ["Hunt where the 5d-3d chain breaks", "The antiparallel sign is mediated by RE 5d. Screen for phases where that channel weakens: semiconducting or semimetallic X, long RE-Fe distances, RE coordinated only by anions, dilute RE. These are the only plausible FM exceptions."],
  ["Use the induced 5d moment as a free diagnostic", "Every Gd run already reports the RE 5d moment. Where its sign or magnitude deviates from the usual antiparallel pattern, the mechanism is weakening — a cheap flag for which compounds deserve explicit Tb–Tm treatment."],
  ["Escalate only the outliers", "Explicit 4f Tb–Tm with occupation-matrix control is expensive and fragile. Reserve it for de Gennes outliers and predicted FM exceptions, then add Tᴄ via exchange constants for survivors."],
];
strat.forEach(([h, d], i) => {
  const y = 1.66 + i * 1.17;
  card(s, 6.4, y, 6.2, 1.05);
  numCircle(s, 6.68, y + 0.18, i + 1, i === 1 ? FE : RE);
  s.addText(h, { x: 7.28, y: y + 0.13, w: 5.1, h: 0.28, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12.5, bold: true, color: INK });
  s.addText(d, { x: 7.28, y: y + 0.42, w: 5.15, h: 0.58, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10, color: MUTE });
});
s.addNotes("Key reframing: the Gd campaign is not just a yes/no on ferromagnetism. It is a measurement of the RE-TM exchange that propagates to the whole heavy series analytically.");


// ================= 9b. CAMPBELL APPLIED =================
s = pres.addSlide();
titleBar(s, "CAMPBELL'S RULE, APPLIED", "Which results reach the target with which rare earth, against magnets on the market", false);
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/campbell_ms.png", x: M, y: 1.5, w: 8.3, h: 5.2 });
card(s, 9.25, 1.5, 3.35, 5.2, PANEL);
s.addText("How to read it", { x: 9.47, y: 1.65, w: 3.0, h: 0.26, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12, bold: true, color: INK });
s.addText("One row per host, ranked by its Nd projection. The Fe/Co sublattice moment is the computed one; each marker swaps the RE: Gd as computed (ferri), heavy Tb/Dy antiparallel, light Nd/Sm parallel. Dotted lines: measured Ms of commercial and benchmark magnets.",
  { x: 9.47, y: 1.95, w: 3.05, h: 1.45, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9, color: MUTE });
const cPts = [
  ["Heavy RE never works", "Tb/Dy pull every host below 1 T; most go negative (RE-dominated)."],
  ["Light RE recovers 1.4-2.0 T", "the known 2-14-1 and 2-17-N hosts top out at 2.0 T projected ≈ 1.6-1.7 T real; Nd₂Fe₁₄B and NdFe₁₂N are exactly that."],
  ["New hosts land at 1.7-1.9 T", "CoFe₁₃NdY₃, Co₇Fe₁₆Nd₆, Fe₅NdSi, Fe₁₁NdW - the first two are RE-rich, the last two are the queued batch."],
  ["Sm costs 0.2-0.4 T", "but carries the strongest anisotropy and sits on the hull more often."],
];
cPts.forEach(([h, d], i) => {
  const y = 3.5 + i * 0.72;
  s.addText(h, { x: 9.47, y, w: 3.0, h: 0.22, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.8, bold: true, color: i === 0 ? FE : RE });
  s.addText(d, { x: 9.47, y: y + 0.21, w: 3.05, h: 0.5, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.3, color: MUTE });
});
s.addText("Learnt: within this chemistry the rare earth sets Ms far more than the host does; the host's job is coupling strength and stability, which is why the batch was chosen on those two and not on Ms alone.",
  { x: M, y: 6.78, w: W, h: 0.45, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10, italic: true, color: INK });
s.addNotes("All projections are 0 K PBE without SOC and ~0.3 T above experiment (Nd2Fe17Nx 2.04 projected vs ~1.5 measured). Literature: Nd2Fe14B 1.61 T/585 K; Sm2Fe17N3 1.54/749; NdFe12N 1.66/823 (Hirayama 2015); Sm(Fe0.8Co0.2)12 1.78/859 (Hirayama 2017); Sm2Co17 1.25/1190.");

// ================= 10b. ANISOTROPY STEP =================
s = pres.addSlide();
titleBar(s, "AFTER THE COUPLING QUESTION", "How much Gd must be replaced to make a magnet", false);

card(s, M, 1.62, 5.5, 2.35, NAVY2);
s.addText("The gap the campaign leaves", {
  x: M + 0.3, y: 1.8, w: 4.9, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 14, bold: true, color: GOLD });
s.addText("Gd is a 4f⁷ S-state ion: L = 0, spherical charge cloud, no single-ion anisotropy by construction. That is exactly why it is a clean surrogate for exchange — and exactly why it can never be the final composition.",
  { x: M + 0.3, y: 2.16, w: 4.9, h: 1.0, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12, color: "C6D2E4" });
s.addText("κ  =  √( K₁ / μ₀Ms² )  ≥  1", {
  x: M + 0.3, y: 3.2, w: 4.9, h: 0.45, isTextBox: true, margin: 0,
  fontFace: HF, fontSize: 19, bold: true, color: WHITE });

const krows = [
  [{ text: "μ₀Ms", options: { bold: true } }, { text: "K₁ for κ = 1", options: { bold: true } },
   { text: "K₁ for κ = 1.54", options: { bold: true } }],
  ["1.5 T", "1.8 MJ/m³", "4.2 MJ/m³"],
  ["2.0 T", "3.2 MJ/m³", "7.5 MJ/m³"],
];
s.addTable(krows, { x: M, y: 4.15, w: 5.5, colW: [1.6, 1.95, 1.95],
  fontFace: BF, fontSize: 11.5, color: INK, border: { type: "solid", color: "D5DDE8", pt: 1 },
  fill: { color: WHITE }, rowH: 0.34, valign: "middle" });
s.addText("Higher Ms demands MORE anisotropy, not less — which is why a 2 T target forces a non-spherical 4f ion. (κ = 1.54 is Nd₂Fe₁₄B.)",
  { x: M, y: 5.32, w: 5.5, h: 0.6, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, italic: true, color: MUTE });

const asteps = [
  ["Inputs", "|ΔE| per Gd from the campaign sets the exchange field; Stevens α_J and ⟨r²⟩ are tabulated. Only A₂⁰, the crystal-field parameter at the RE site, must be computed separately."],
  ["Model", "K₁(x,T) from the 2nd-order crystal field with the Callen–Callen l = 2 law (K₁ ∝ m_RE³); Ms(x) from the TM sublattice and the RE moments, signed by the coupling."],
  ["Solve", "smallest x clearing κ ≥ 1 at operating temperature. Example: A₂⁰ = +300 K/a₀², 450 K → Tb at x = 0.77 gives K₁ = 5.7 MJ/m³, μ₀Ms = 2.67 T, κ = 1.0."],
  ["Keep Gd for Tc", "Gd has the largest de Gennes factor of the series (15.75 vs Tb 10.5, Dy 7.08), so it contributes most to Tc. Target the MINIMUM x that clears the bar."],
];
asteps.forEach(([h, d], i) => {
  const y = 1.62 + i * 1.28;
  card(s, 6.55, y, 6.05, 1.16);
  numCircle(s, 6.83, y + 0.2, i + 1, i === 3 ? RE : FE);
  s.addText(h, { x: 7.43, y: y + 0.15, w: 4.9, h: 0.28, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12.5, bold: true, color: INK });
  s.addText(d, { x: 7.43, y: y + 0.44, w: 4.95, h: 0.68, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10, color: MUTE });
});
s.addText("Two traps the solver enforces: only ONE Stevens sign family is easy-axis for a given A₂⁰ (Tb/Dy/Ho have α_J < 0, Er/Tm α_J > 0 — mixing them cancels), and K₁ < 0 is easy-plane, which is not a magnet at any magnitude.",
  { x: M, y: 6.42, w: W, h: 0.45, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, italic: true, color: FE });
s.addNotes("A20 sign convention must be calibrated against a known compound first. Novamag is the natural calibration source.");

// ================= 10c. EXPANDING THE POOL =================

// ---------- flowchart helpers ----------
function fbox(slide, x, y, w, h, title, sub, fill, tc, sc, fs) {
  if (typeof sc === "number") { fs = sc; sc = undefined; }
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.06, fill: { color: fill }, line: { color: fill, width: 0.5 } });
  slide.addText(title, { x: x + 0.08, y: y + 0.06, w: w - 0.16, h: 0.26, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12, bold: true, color: tc, align: "center" });
  if (sub) slide.addText(sub, { x: x + 0.08, y: y + 0.36, w: w - 0.16, h: h - 0.4, isTextBox: true, margin: 0, fontFace: BF, fontSize: fs || 8, color: sc || tc, align: "center", valign: "top" });
}
function farrow(slide, x1, y1, x2, y2, color) {
  slide.addShape(pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: x2 < x1, flipV: y2 < y1, line: { color: color || "7A8DA8", width: 1.4, endArrowType: "triangle" } });
}
const LB = "E3F0F6", LBt = "1F5F7A";   // light blue: data
const LP = "EEEDFE", LPt = "3C3489";   // purple: model
const LC = "FCEDE8", LCt = "8A3B2E";   // coral: DFT / NERSC
const LG = "EEF2F7", LGt = INK;        // grey: step



// ================= 10n-i. CONCEPTS BEHIND THE DESCRIPTORS =================
s = pres.addSlide();
titleBar(s, "THE PHYSICS BEHIND THE DESCRIPTORS", "Each descriptor and threshold in the workflow stands for a known principle; here is which, and what we measured", false);
const conc = [
  [{ text: "Principle (source)", options: { bold: true } }, { text: "What it says", options: { bold: true } }, { text: "Descriptor / rule in the workflow", options: { bold: true } }, { text: "Our evidence", options: { bold: true } }],
  ["Campbell 4f–5d–3d chain (Campbell 1972)", "RE 4f polarises its own 5d; 5d–3d coupling is antiparallel → heavy RE ferri, light RE parallel", "RE one-hot; light RE (Nd, Sm, Pr) only in the waves; sign never fitted", "180/180 Gd pairs ferrimagnetic"],
  ["Two-sublattice exchange, ΔE = 2 I₄f₋₅d S₄f S₅d (Liebs, Hummler, Fähnle 1992; Liebs & Fähnle 1993)", "the RE–TM gap is set by the 5d spin the host induces on the RE", "label h = TM-tied 5d polarisation; gap = 1574·h (the GP target)", "r = 0.89 on 180 compounds; GdFe₂ J_RT 2.97 vs 2.99 × 10⁻²² J"],
  ["5d–3d hybridisation (Brooks & Johansson)", "shorter RE–TM bonds and more 3d states at the RE raise the 5d polarisation; Co > Fe", "d_RE-TM mean/min, N_TM_nn, f_Co, 3d count", "distance r = −0.61; Fe+Co J_eff ×1.48"],
  ["de Gennes scaling (de Gennes 1962)", "RE–TM coupling ∝ (gJ−1)J; Tc contribution ∝ (gJ−1)²J(J+1)", "gap_RE = gap_Gd·(gJ−1)J/3.5 → T* threshold per RE", "Tb–Tm projected from Gd; explicit-4f check running"],
  ["Early-TM enhancement (Duc 1998)", "Ti, V on the TM site raise the RE–TM exchange and stabilise 1:12", "f_early; early-TM substitution on the far Fe site", "stability yes; coupling ×0.97, needs a series"],
  ["Slater–Pauling / magnetic valence (Williams, Malozemoff, Moruzzi 1983)", "Ms is set by Fe density and the 3d count; Co, early TM and p-elements lower the moment", "tm_density, f_Fe, d_count, x_dil → analytic Ms; Ms ≥ 1.5 T filter", "Ms ceiling 1.75 T projected; kagome capped at 1.0 T"],
  ["Interstitial modification (Coey & Sun 1990)", "N, C in the RE-adjacent void expand the lattice, raise Ms and Tc, keep the RE coupling; H does not", "n_N/C/H in the RE shell; interstitial generator on the 2b / 9e voids", "H: gap ×0.10; C passes the hull, N does not"],
  ["Metastability scale (Sun, Ceder et al. 2016)", "synthesisable phases sit within tens of meV/atom of the hull; MLIP error ≈ 30 meV", "same-model MACE/MP hull; E_hull ≤ 30 meV filter", "Nd costs 20–35 meV vs Gd; Sm ≈ free"],
  ["RE anisotropy needs a locked RE sublattice (Kuz'min; Coey)", "the 4f crystal-field anisotropy only works below the RE–TM decoupling temperature", "T* = gap_RE/2k_B ≥ Tc target → gap_RE ≥ 100 meV (Nd₂Fe₁₄B level)", "Tao hosts: T* 1100–1260 K for Sm"],
];
s.addTable(conc, { x: M, y: 1.55, w: W, colW: [2.9, 3.6, 3.2, 2.2], fontFace: BF, fontSize: 8.6, color: INK,
  border: { type: "solid", color: "D5DDE8", pt: 0.75 }, fill: { color: WHITE }, rowH: 0.5, valign: "middle" });
s.addText("None of these is new; what is new is that one dataset tests all of them at once and turns them into numbers a surrogate can use.",
  { x: M, y: 6.75, w: W, h: 0.4, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10.5, italic: true, color: INK });
s.addNotes("Refs: Campbell J. Phys. F 2, L47 (1972); Liebs, Hummler, Fahnle PRB 46, 11201 (1992); Liebs & Fahnle JMMM 128, L8 (1993); Brooks & Johansson, Handbook of Magnetic Materials 7 (1993); de Gennes J. Phys. Radium 23, 510 (1962); Duc et al. JMMM 177-181, 1107 (1998); Williams, Malozemoff, Moruzzi JAP 54, 3129 (1983); Coey & Sun JMMM 87, L251 (1990); Sun et al. Sci. Adv. 2, e1600225 (2016); Kuz'min & Tishin, Handbook of Magnetic Materials 17 (2008). Benchmarks: Hirayama et al. Scripta Mater. 95, 70 (2015) NdFe12N; Hirayama et al. Scripta Mater. 138, 62 (2017) Sm(Fe,Co)12; Korner, Krugel, Elsasser Sci. Rep. 6, 24686 (2016) HT 1:12 screening.");

// ================= 10n-ii. HOW THE WORKFLOW USES THEM =================
s = pres.addSlide();
titleBar(s, "THE PRINCIPLES AT WORK", "Five compounds from the pool, and which principle decided their fate", false);
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/trends_geometry.png", x: M, y: 1.55, w: 6.0, h: 2.88 });
s.addText("Brooks–Johansson in the data: coupling vs RE–TM distance and vs host class, 180 labels", { x: M, y: 4.45, w: 6.0, h: 0.3, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9, italic: true, color: MUTE });
const ex = [
  ["Fe₅NdSi · Immm", "short RE–TM bonds (2.97 Å, 12 TM) → GP predicts h 0.15, gap 82 meV; Fe density → 1.74 T; on the hull", "Brooks–Johansson · Slater–Pauling · hull", "in wave 1", RE],
  ["Gd₂Fe₁₇H₃", "H in the RE first shell → measured gap 28 meV; descriptor n_H_shell flags it; no H variants are generated", "Coey interstitial rule, inverted", "excluded by design", FE],
  ["Co₁₉Fe₄Gd₆", "mixed Fe+Co host → strongest coupling in the set, J_eff 1.41; on the Pareto front", "Brooks: Co strengthens 5d–3d", "Co variants generated for every host", RE],
  ["Nd(FeGe)₆ kagome", "stable (−7 meV) but TM density 3.2 per 100 Å³ → Ms 1.0 T; RE in a 3.3 Å channel → weak coupling", "Slater–Pauling density · Brooks distance", "fails Ms floor; none drawn", FE],
  ["(Pr,Nd)Fe₁₀.₅V₁.₅N", "1:12 with V stabiliser, mixed RE, N in the 2b void - the real magnet composition; N variant above the hull cut", "Duc · de Gennes · Coey · Sun metastability", "V cells in wave 1; nitride needs an exception", GOLD],
];
ex.forEach(([h, d, p, verdict, c], i) => {
  const y = 1.55 + i * 1.05;
  card(s, 7.0, y, 5.6, 0.95, PANEL);
  s.addShape(pres.ShapeType.roundRect, { x: 7.12, y: y + 0.12, w: 0.12, h: 0.7, rectRadius: 0.03, fill: { color: c } });
  s.addText(h, { x: 7.35, y: y + 0.08, w: 3.4, h: 0.24, isTextBox: true, margin: 0, fontFace: BF, fontSize: 11, bold: true, color: INK });
  s.addText(verdict, { x: 10.75, y: y + 0.08, w: 1.75, h: 0.24, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9, bold: true, color: c === GOLD ? "8A6A1E" : c, align: "right" });
  s.addText(d, { x: 7.35, y: y + 0.33, w: 5.15, h: 0.4, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.8, color: MUTE });
  s.addText(p, { x: 7.35, y: y + 0.72, w: 5.15, h: 0.2, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.4, italic: true, color: INK });
});
card(s, M, 4.95, 6.0, 1.9, NAVY2);
s.addText("What the principles cannot do, and the loop does", { x: M + 0.25, y: 5.08, w: 5.5, h: 0.28, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12, bold: true, color: GOLD });
s.addText("Each rule gives a direction, not a magnitude, and they conflict: Co raises coupling but lowers Ms; early TM stabilises 1:12 but dilutes Fe; N raises Ms but leaves the hull. The GP learns the magnitudes from the 180 labels, Thompson sampling resolves the conflicts under the thresholds, and every wave returns the measurements that correct the rules themselves.",
  { x: M + 0.25, y: 5.4, w: 5.5, h: 1.4, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10, color: "C6D2E4" });
s.addNotes("Fe5NdSi numbers from wave_1.csv; Gd2Fe17H3 from results.json (suspects batch re-running it); Co19Fe4Gd6 from exchange_features.csv; kagome from pool.csv; mixed 1:12 from generate_mixed_1_12.py / pool.csv.");

// ================= 10o. OVERVIEW FLOWCHART (standard notation) =================
s = pres.addSlide();
titleBar(s, "THE WHOLE LOOP ON ONE PAGE", "Standard flowchart: data in cylinders and parallelograms, decisions in diamonds, the HPC step in red", false);
const FC = {
  term: pres.ShapeType.flowChartTerminator, proc: pres.ShapeType.flowChartProcess, dec: pres.ShapeType.flowChartDecision,
  data: pres.ShapeType.flowChartInputOutput, db: pres.ShapeType.flowChartMagneticDisk, doc: pres.ShapeType.flowChartDocument,
};
function fshape(slide, type, x, y, w, h, text, fill, tc, fs, lc) {
  slide.addShape(type, { x, y, w, h, fill: { color: fill }, line: { color: lc || tc, width: 0.75 } });
  slide.addText(text, { x: x + 0.1, y, w: w - 0.2, h, isTextBox: true, margin: 0, fontFace: BF, fontSize: fs || 10, bold: false, color: tc, align: "center", valign: "middle" });
}
function flabel(slide, x, y, t) {
  slide.addText(t, { x, y, w: 0.5, h: 0.22, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9, bold: true, color: MUTE, align: "center" });
}
// row 1 - generation and surrogate screening
const r1 = 1.75, hb = 0.95;
fshape(s, FC.term, M, r1, 1.5, hb, "START\nprototypes +\ndatabases", LG, LGt, 10);
fshape(s, FC.db, M + 1.75, r1 - 0.05, 1.55, hb + 0.1, "structure store\nGNoME · MP · OQMD\n+ generated cells", LB, LBt, 9.5);
fshape(s, FC.proc, M + 3.55, r1, 1.75, hb, "substitute\nNd/Sm · Co · early TM\nN/C interstitials", LG, LGt, 10);
fshape(s, FC.proc, M + 5.55, r1, 1.55, hb, "MACE-MP-0\nrelax cell\n(30 s)", LP, LPt, 10);
fshape(s, FC.dec, M + 7.35, r1 - 0.25, 2.0, hb + 0.5, "E_hull ≤ 30 meV\nand Ms ≥ 1.5 T ?", LC, LCt, 10);
fshape(s, FC.term, M + 9.75, r1, 1.5, hb, "archive\n(training only)", LG, MUTE, 9.5, "B4B2A9");
[[M + 1.5, M + 1.75], [M + 3.3, M + 3.55], [M + 5.3, M + 5.55], [M + 7.1, M + 7.35]].forEach(([a, b]) => farrow(s, a, r1 + hb / 2, b, r1 + hb / 2));
farrow(s, M + 9.35, r1 + hb / 2, M + 9.75, r1 + hb / 2); flabel(s, M + 9.3, r1 + 0.05, "no");
// down from decision to row 2
const r2 = 3.55;
farrow(s, M + 8.35, r1 + hb + 0.25, M + 8.35, r2); flabel(s, M + 8.4, r1 + hb + 0.35, "yes");
// row 2 - pool, GP, sampling, HPC
fshape(s, FC.data, M + 7.35, r2, 2.0, hb, "pool row\n15 geometry descriptors\n+ RE one-hot", LB, LBt, 10);
fshape(s, FC.proc, M + 5.1, r2, 1.95, hb, "GP predicts h\n(5d polarisation):\nlinear trend + GP correction", LP, LPt, 10);
fshape(s, FC.proc, M + 2.85, r2, 1.95, hb, "Thompson sampling\n→ wave of 120\n(constraints + cap)", LP, LPt, 10);
fshape(s, FC.proc, M, r2, 2.55, hb, "VASP on Perlmutter\n120 f-in-core relaxations\none packed 4 h job", "F5C4B3", "712B13", 9.5, "D85A30");
farrow(s, M + 7.35, r2 + hb / 2, M + 7.05, r2 + hb / 2); farrow(s, M + 5.1, r2 + hb / 2, M + 4.8, r2 + hb / 2); farrow(s, M + 2.85, r2 + hb / 2, M + 2.55, r2 + hb / 2);
// row 3 - results, ingest, decision, end
const r3 = 5.35;
farrow(s, M + 1.27, r2 + hb, M + 1.27, r3);
fshape(s, FC.data, M, r3, 2.55, hb, "per run: h, Fe/Co moments, V\n→ gap_RE = 1574·h·(gJ−1)J/3.5\nT* = gap_RE/2k_B, Ms = Σm/V", LB, LBt, 10);
fshape(s, FC.proc, M + 2.85, r3, 1.95, hb, "ingest: parse OUTCARs →\nlabels.csv; compare measured h\nto predicted (H1); re-fit GP", LP, LPt, 10);
fshape(s, FC.dec, M + 5.1, r3 - 0.25, 2.0, hb + 0.5, "Pareto front\nmoved? feasible\ncandidates left?", LC, LCt, 10);
fshape(s, FC.term, M + 7.35, r3, 2.0, hb, "END → candidate list\nSOC anisotropy → Tc\n→ synthesis", LG, LGt, 10);
farrow(s, M + 2.55, r3 + hb / 2, M + 2.85, r3 + hb / 2); farrow(s, M + 4.8, r3 + hb / 2, M + 5.1, r3 + hb / 2);
farrow(s, M + 7.1, r3 + hb / 2, M + 7.35, r3 + hb / 2); flabel(s, M + 7.0, r3 + 0.05, "no");
// yes-loop: from decision top up to the GP box (retrain) and to the store (expand neighbourhood)
s.addShape(pres.ShapeType.line, { x: M + 6.1, y: r2 + hb, w: 0, h: r3 - 0.25 - (r2 + hb), line: { color: "7A8DA8", width: 1.4, endArrowType: "triangle", beginArrowType: "none" }, flipV: true });
flabel(s, M + 6.15, r2 + hb + 0.08, "yes");
s.addText("retrain on new labels", { x: M + 6.2, y: r2 + hb + 0.32, w: 1.6, h: 0.2, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.5, italic: true, color: MUTE });
// dashed expansion edge: ingest -> store (neighbourhood of winners)
s.addShape(pres.ShapeType.line, { x: M + 2.5, y: r1 + hb + 0.1, w: 0, h: r3 - (r1 + hb + 0.1), line: { color: "3C3489", width: 1.2, dashType: "dash", endArrowType: "triangle" }, flipV: true });
s.addText("expand: winners × levers\n→ new cells into the store", { x: M + 2.6, y: 2.95, w: 1.75, h: 0.4, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.5, italic: true, color: "3C3489" });
// right column: two evidence images
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/gap_vs_h.png", x: 9.95, y: 2.85, w: 2.65, h: 1.84 });
s.addText("behind the GP label: gap = 1574·h on 180 Gd pairs, r = 0.89 - one f-in-core run per label", { x: 9.95, y: 4.7, w: 2.65, h: 0.4, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8, color: MUTE });
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/light_re_hull.png", x: 9.95, y: 5.15, w: 2.65, h: 1.75 });
s.addText("behind the hull decision: MACE vs MP competitors, Ms vs stability for the light-RE hosts", { x: 9.95, y: 6.9, w: 2.65, h: 0.4, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8, color: MUTE });
s.addNotes("Standard symbols: terminator = start/end, rectangle = process, diamond = decision, parallelogram = data, cylinder = stored data. Red process = the only HPC step. Solid loop = retraining; dashed loop = neighbourhood expansion of the winners feeding the structure store.");


// ================= 10p. POLYTYPES AND SUBSTITUTIONS =================
s = pres.addSlide();
titleBar(s, "GENERATING CANDIDATES", "Polytypes we decorate, and the substitutions we apply to them", false);
card(s, M, 1.6, 5.6, 5.1);
s.addText("Polytypes  (prototype → generated cells)", { x: M + 0.3, y: 1.75, w: 5.1, h: 0.3, isTextBox: true, margin: 0, fontFace: BF, fontSize: 14, bold: true, color: RE });
const poly = [
  ["CaCu₅ · RT₄X  (SmCo₅ family)", 61, "X site decorated; compensates near 0 T, kept for coupling"],
  ["ThMn₁₂ · RFe₁₁X, RFe₁₀X₂  (1:12)", 21, "stabiliser X = Ti V Cr Zr Nb Mo W Hf Ta Re"],
  ["Th₂Zn₁₇ / Th₂Ni₁₇  (2:17) + interstitials", 21, "the Sm₂Fe₁₇N₃ framework"],
  ["Nd₂Fe₁₄B / Nd₂Fe₁₄C  (2:14:1)", 20, "the reference magnet lattice"],
  ["LaCo₉Si₄  (1:9)", 21, "dense 1:9 R3m family"],
  ["Kagome RT₆X₆ · HfFe₆Ge₆-type", 30, "Fe₆, Co₆, Fe₅Co × Sn Ge Si Ga Al; + vacancy"],
  ["Nitrides / carbides of the passers", 224, "N, C in the RE-adjacent void: 2b, 9e, GNoME channels"],
  ["Mixed-RE fractional 1:12  (Nd,Pr,Sm)₂Fe₂₁V₃N₀₋₂", 9, "the real NdFe₁₂-based composition class"],
  ["GNoME frameworks  (new-R3m, R-3m, Cm, Immm …)", 369, "campaign hosts, light-RE substituted"],
];
poly.forEach(([n, k, note], i) => {
  const y = 2.15 + i * 0.48;
  s.addText(n, { x: M + 0.3, y, w: 3.9, h: 0.22, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10.5, bold: true, color: INK });
  s.addText(note, { x: M + 0.3, y: y + 0.21, w: 3.9, h: 0.22, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.6, color: MUTE });
  s.addShape(pres.ShapeType.roundRect, { x: M + 4.25, y: y + 0.05, w: Math.max(0.05, Math.min(k, 240) / 240 * 0.9), h: 0.16, rectRadius: 0.03, fill: { color: i >= 5 ? GOLD : RE } });
  s.addText(String(k), { x: M + 5.0, y: y - 0.01, w: 0.5, h: 0.24, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10.5, bold: true, color: i >= 5 ? "8A6A1E" : RE, align: "right" });
});
s.addText("gold = added this week from the data-backed levers", { x: M + 0.3, y: 6.42, w: 5.1, h: 0.22, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.6, italic: true, color: MUTE });

card(s, 6.6, 1.6, 6.0, 5.1, PANEL);
s.addText("Substitutions  (site → palette → why)", { x: 6.9, y: 1.75, w: 5.5, h: 0.3, isTextBox: true, margin: 0, fontFace: BF, fontSize: 14, bold: true, color: INK });
const subs = [
  [{ text: "Site", options: { bold: true } }, { text: "Palette", options: { bold: true } }, { text: "Reason from the data", options: { bold: true } }],
  ["RE site", "Gd → Nd, Sm; Pr in expansion; Nd/Pr/Sm pairs", "light RE adds to Ms (J = L − S); Sm couples harder (×1.46 gap)"],
  ["TM site, nearest the RE", "Fe → Co at ⅛ and ¼", "partial Co: coupling ×1.48, the only large resolved lever"],
  ["TM site, farthest from RE", "Ti V Cr Zr Nb Mo W Hf Ta Re (one atom)", "1:12 stabiliser pattern; coupling effect unresolved (×0.97)"],
  ["Prototype X site", "Al Si Ga Ge B C N P Sn Sb Zn Cu", "the classic decoration palette; metalloids neutral on average"],
  ["RE-adjacent void", "N, C - dilute and fully occupied", "Ms and Tc lever of Sm₂Fe₁₇N₃ / NdFe₁₂N; keeps the gap (unlike H)"],
  ["Channel X (kagome)", "one X removed", "the defective 1:6:6 variant seen experimentally"],
  ["Not applied", "H interstitial · Mn · Dy · U", "H kills coupling (×0.10); Mn ∥ Co, no gain; Dy via de Gennes only; U out of scope"],
];
s.addTable(subs, { x: 6.9, y: 2.15, w: 5.45, colW: [1.35, 1.9, 2.2], fontFace: BF, fontSize: 8.8, color: INK,
  border: { type: "solid", color: "D5DDE8", pt: 0.75 }, fill: { color: WHITE }, rowH: 0.46, valign: "middle" });
s.addText("Every variant → MACE relax → same-model hull → descriptors → pool. Generation is cheap (30 s per cell); the thresholds and the GP do the selecting.",
  { x: 6.9, y: 6.05, w: 5.45, h: 0.55, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.5, italic: true, color: INK });
s.addNotes("Counts: 146 original decorations (first six rows of the old slide 24, by prototype), 30 kagome, 224 interstitial cells on 60 Fe-rich passers, 9 mixed 1:12 supercells, 369 campaign host structures (180 credible + 189 unlabelled).");

// ================= 10a. CANDIDATE GENERATION =================
s = pres.addSlide();
titleBar(s, "CANDIDATE GENERATION", "Seven sources feed one pool; every structure gets the same relaxation, hull and descriptors", false);
const srcs = [
  ["Database structures", "GNoME · MP · Alexandria · OQMD\n903 formulas with a CIF\n+147 recovered this week (MP by id)", "134 in pool", LB, LBt],
  ["Campaign hosts", "180 credible Gd hosts (all, not only strong)\n+189 compounds without a credible label\n(f-in-core has no +U: they converge)", "656 in pool", LB, LBt],
  ["Prototype decoration", "CaCu₅-RT₄X, ThMn₁₂, Th₂Zn₁₇, Nd₂Fe₁₄B,\nLaCo₉Si₄ × 19-element X palette\n146 Gd cells → Nd and Sm", "252 in pool", LG, LGt],
  ["Kagome RT₆X₆", "HfFe₆Ge₆-type P6/mmm; Fe₆, Co₆, Fe₅Co\n× Sn, Ge, Si, Ga, Al; + channel vacancy\n(none passes Ms ≥ 1.5 T: Fe density 3.2)", "60 in pool", LG, LGt],
  ["Interstitial N / C", "largest RE-adjacent void of every Fe-rich\npasser (2b in 1:12, 9e in 2:17, GNoME\nchannels); dilute + full occupation", "224 cells", GOLD, "5A3E00"],
  ["Mixed-RE fractional 1:12", "2-f.u. supercells: (Nd,Pr,Sm)₂Fe₂₁V₃N₀₋₂\n= RFe₁₀.₅V₁.₅N₀₋₁, the real magnet\ncomposition class", "9 cells", GOLD, "5A3E00"],
  ["Neighbourhood expansion", "after each wave: top-25 labelled winners\n× RE swap, Co ⅛ and ¼, early TM on the\nfar Fe site, N - the data-backed levers", "wave ≥ 2", LP, LPt],
];
srcs.forEach(([h, d, n, fill, tc], i) => {
  const col = i % 4, row = Math.floor(i / 4);
  const x = M + col * 3.0, y = 1.6 + row * 1.85;
  fbox(s, x, y, 2.8, 1.65, h, d, fill, tc, tc, 11.5);
  s.addText(n, { x: x + 0.1, y: y + 1.32, w: 2.6, h: 0.28, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10, bold: true, color: tc, align: "center" });
});
fbox(s, M + 9.0, 3.45, 2.8, 1.65, "The pool today", "1,220 unique structures relaxed\nall with a same-model hull energy\n94 pass hull ≤ 30 meV and Ms ≥ 1.5 T\n→ Thompson sampling draws the wave", NAVY2, GOLD, "C6D2E4");
s.addText("Generated ≠ stable: database candidates arrive with a hull distance, generated ones do not - which is why every source goes through the MACE hull before the GP ever sees it (next slide).",
  { x: M, y: 5.45, w: W, h: 0.5, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10.5, italic: true, color: INK });
card(s, M, 6.05, W, 0.7, NAVY2);
s.addText("Learnt from building the pool: the generators that add feasible candidates are the Fe-dense ones (2:17, 1:12, 3:29 frameworks, their nitrides and Co variants); kagome and metalloid-rich cages are stable but cannot reach 1.5 T. Generation is cheap, so breadth costs nothing - the thresholds do the selecting.",
  { x: M + 0.25, y: 6.05, w: W - 0.5, h: 0.7, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.8, color: "C6D2E4", valign: "middle" });
s.addNotes("Counts from analysis/pool/pool.csv at the time of the wave-1 redraw. Dedupe is on (reduced formula, space group); the same host can appear from several sources, the lowest-hull copy is kept.");

// ================= 10b. SUBSTITUTION AND SCREENING =================
s = pres.addSlide();
titleBar(s, "FROM PROTOTYPE TO POOL ROW", "Substitution rules, then two surrogate screens, then descriptors - no DFT until the wave", false);
const y0 = 1.7;
fbox(s, M, y0, 2.2, 1.45, "Source cell", "heavy-RE placeholder (Gd)\nor light-RE cell from a\ngenerator", LB, LBt, undefined, 10.5);
fbox(s, M + 2.55, y0, 2.6, 1.45, "Substitution rules", "Gd → Nd, Sm (Pr in expansion)\nFe → Co, ⅛ nearest the RE\nearly TM on the far Fe site\nN / C into RE-adjacent voids", LG, LGt, 10.5);
fbox(s, M + 5.5, y0, 2.0, 1.45, "Dedupe", "(reduced formula,\nspace group)\nlowest hull kept", LG, LGt, 10.5);
fbox(s, M + 7.85, y0, 2.0, 1.45, "MACE-MP-0 relax", "cell + positions\nfmax 0.1 eV/Å, ≤120 steps\n~30 s per cell on CPU", LP, LPt, 10.5);
fbox(s, M + 10.2, y0, 1.7, 1.45, "Same-model hull", "MP competitors ≤100 meV\nre-relaxed with MACE\n→ E_hull", LP, LPt, undefined, 10.5);
farrow(s, M + 2.2, y0 + 0.72, M + 2.55, y0 + 0.72); farrow(s, M + 5.15, y0 + 0.72, M + 5.5, y0 + 0.72);
farrow(s, M + 7.5, y0 + 0.72, M + 7.85, y0 + 0.72); farrow(s, M + 9.85, y0 + 0.72, M + 10.2, y0 + 0.72);
const y1 = 3.6;
fbox(s, M + 10.2, y1, 1.7, 1.45, "Descriptors", "15 geometry numbers\n+ RE one-hot\n(wave_features.py)", LP, LPt, undefined, 10.5);
fbox(s, M + 7.85, y1, 2.0, 1.45, "Analytic Ms", "Σ TM moments (campaign\nmedians) + free-ion RE\n÷ relaxed volume", LG, LGt, undefined, 10.5);
fbox(s, M + 5.5, y1, 2.0, 1.45, "pool.csv row", "cid · formula · source\nE_hull · Ms · descriptors\n→ POSCAR_mace", LB, LBt, undefined, 10.5);
fbox(s, M + 2.55, y1, 2.6, 1.45, "Hard filters", "E_hull ≤ 30 meV/atom\n(MACE noise ≈ 30)\nMs_proj ≥ 1.5 T", LC, LCt, undefined, 10.5);
fbox(s, M, y1, 2.2, 1.45, "→ GP + sampling", "feasible set\n(94 of 1,220 today)\nnext slide", LP, LPt, 10.5);
farrow(s, M + 11.05, y0 + 1.45, M + 11.05, y1);
farrow(s, M + 10.2, y1 + 0.72, M + 9.85, y1 + 0.72); farrow(s, M + 7.85, y1 + 0.72, M + 7.5, y1 + 0.72);
farrow(s, M + 5.5, y1 + 0.72, M + 5.15, y1 + 0.72); farrow(s, M + 2.55, y1 + 0.72, M + 2.2, y1 + 0.72);
const desc = ["N_TM_nn, d_RE-TM (mean, min)", "f_Fe, f_Co, 3d count, TM per RE, dilution", "TM density, volume per atom", "early-TM fraction", "metalloid / H / N / C atoms in the RE shell"];
s.addText("The 15 descriptors (all pre-DFT):  " + desc.join("  ·  "),
  { x: M, y: 5.3, w: W, h: 0.45, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.5, color: MUTE });
s.addText("Why two surrogates: MACE answers 'does this cell exist' (stability, geometry) at 30 s per structure; the GP answers 'is it worth a VASP run' (coupling) from the geometry MACE produced. Neither replaces the DFT label - they decide which 120 of the 1,220 get one.",
  { x: M, y: 5.85, w: W, h: 0.7, isTextBox: true, margin: 0, fontFace: BF, fontSize: 11, italic: true, color: INK });

// ================= 10c. THE GP AND ITS LOSS =================
s = pres.addSlide();
titleBar(s, "THE GP, WHAT IT FITS, HOW IT PICKS", "Two-stage model on the 5d polarisation h; batch Thompson sampling under the magnet constraints", false);
fbox(s, M, 1.6, 3.7, 1.55, "1 · Training rows", "179 credible Gd pairs: label h = −½[m₅d(ferri) + m₅d(fm)]\n+ every ingested f-in-core wave run: h read directly\nfeatures = 15 descriptors + RE one-hot, standardised", LB, LBt, 12);
fbox(s, M + 4.1, 1.6, 3.7, 1.55, "2 · Mean function (ridge)", "w = argmin ‖h − Xw‖² + α‖w‖²,  α = 1\nthe physics the 180 labels already fixed:\ndistance, coordination, Co fraction, dilution", LP, LPt, 12);
fbox(s, M + 8.2, 1.6, 3.7, 1.55, "3 · GP on the residual r = h − Xw", "k = σ²·Matern₅⁄₂(ℓ₁…ℓ₁₉) + σₙ²\nhyperparameters maximise the log marginal likelihood\nlog p(r|X) = −½ rᵀK⁻¹r − ½ log|K| − (n/2) log 2π\n→ posterior mean μ(x), std σ(x)", LP, LPt, 12);
farrow(s, M + 3.7, 2.37, M + 4.1, 2.37); farrow(s, M + 7.8, 2.37, M + 8.2, 2.37);
fbox(s, M, 3.5, 3.7, 1.6, "4 · Stage two (deterministic)", "gap_RE = 1574 · h · (gJ−1)J_RE / 3.5\nT* = gap_RE / 2k_B\nMs from the pool row (analytic)\nno fitted parameter beyond 1574", LG, LGt, 12);
fbox(s, M + 4.1, 3.5, 3.7, 1.6, "5 · Validation before use", "10-fold CV on the 179 Gd labels:\nr = 0.88, RMSE 0.018 μB (label sd 0.038)\n91 % of held-out labels inside ±2σ\nH1 check on every wave: measured h vs predicted", LC, LCt, 12);
fbox(s, M + 8.2, 3.5, 3.7, 1.6, "6 · Batch Thompson sampling", "per pick: one joint posterior draw h̃ over the pool\nfeasible if gap̃_RE ≥ 100 meV, Ms ≥ 1.5 T, E_hull ≤ 30\nutility U = Ms · min(1, gap̃ / 100, 11.5); take argmax\nrepeat until the wave is full; family cap by (SG, TM:RE)", GOLD, "5A3E00");
farrow(s, M + 10.05, 3.15, M + 10.05, 3.5); farrow(s, M + 1.85, 3.15, M + 1.85, 3.5); farrow(s, M + 5.95, 3.15, M + 5.95, 3.5);
s.addText("Loss, precisely: the ridge minimises squared error on h; the GP hyperparameters maximise the marginal likelihood of the residuals (not a point loss, so σ is calibrated); nothing is fitted to the acquisition. Posterior uncertainty is what makes the batch diverse - no κ to tune.",
  { x: M, y: 5.35, w: W, h: 0.6, isTextBox: true, margin: 0, fontFace: BF, fontSize: 11, italic: true, color: INK });
s.addText("Honest limits: the GP has 179 points in 19 dimensions, so it extrapolates with wide σ outside the campaign chemistry - which is exactly where Thompson sampling then spends runs. The 1574·h calibration is Gd-derived; H1 tests whether it transfers to f-in-core Nd/Sm, and the RE one-hot lets the model learn a bias if it does not.",
  { x: M, y: 6.05, w: W, h: 0.7, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10.5, color: MUTE });

// ================= 10d. WAVES AND GENERATIONS =================
s = pres.addSlide();
titleBar(s, "WAVES AND GENERATIONS", "One packed Perlmutter job per 48 h; each wave is drawn from the pool the previous one taught", false);
const gens = [
  ["Wave 1 · global", "pool = 7 sources (1,220)\nTS draws 120 under the thresholds\n→ 120 f-in-core relaxations\n60 nodes · 4 h · ~29 h queue", LB, LBt],
  ["Ingest", "mirror → h, Ms, V per run\nlabels.csv (+120 rows)\nH1: measured vs predicted h\nGP re-fit, 10-fold CV", LP, LPt],
  ["Wave 2 · local + global", "pool = remainder\n+ expand(top-25 winners)\n+ new prototypes added by hand\nTS draws 120 again", LB, LBt],
  ["Ingest", "labels.csv (+120)\nPareto front of (gap_RE, Ms, E_hull)\nhas it moved?", LP, LPt],
  ["Wave k", "same loop; pool grows by\nneighbourhoods of each\nwave's winners", LB, LBt],
  ["Stop", "feasible count → 0, or\nfront unchanged 2 waves, or\nH1 fails (r < 0.5): retrain on\nf-in-core rows only", LC, LCt],
];
gens.forEach(([h, d, fill, tc], i) => {
  const x = M + i * 2.0;
  fbox(s, x, 1.7, 1.85, 1.8, h, d, fill, tc, tc, 10.5);
  if (i < 5) farrow(s, x + 1.85, 2.6, x + 2.0, 2.6);
});
// generation detail
fbox(s, M, 3.75, 5.7, 1.6, "What 'expand' generates from a winner", "RE swap  Nd ↔ Sm ↔ Pr on the same cell\nCo  ⅛ and ¼ of Fe, the sites nearest the RE first\nearly TM  one Ti / V / Zr / Nb on the Fe site farthest from the RE\nN  into the largest RE-adjacent void (dilute and full)\neach variant → MACE relax → same-model hull → descriptors → pool", LG, LGt, 12);
fbox(s, M + 6.2, 3.75, 5.7, 1.6, "What a wave returns, per cell", "relaxed volume and pressure (did N / Nd fit?)\nFe / Co sublattice moments → Ms with the free-ion RE added\nh = RE s+p+d polarisation → gap_RE, T*, B_RT via 1574·h\nconvergence flags; everything appended as a training row\nno fm/ferri pair, no +U: one run is one label", LC, LCt, 12);
s.addText("Cadence: plan (minutes) → push → submit → queue 1-2 d → run 3 h → ingest (minutes). Scripts: wave_pool.py · wave_gp.py · wave_inputs.py · submit_batch.sh · sync_results.sh · wave_ingest.py, driven by wave_loop.sh; DEPLOY_NERSC.md puts the whole loop on a Perlmutter login node with scrontab.",
  { x: M, y: 5.55, w: W, h: 0.6, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10.5, color: MUTE });
card(s, M, 6.3, W, 0.75, NAVY2);
s.addText("Each wave answers a question, not just adds points: wave 1 - do the Gd-derived rules transfer to Nd/Sm (H1)? wave 2 - do the levers compose on the winners (H4)? later waves - where does the Pareto front of coupling, Ms and stability stop moving?",
  { x: M + 0.25, y: 6.3, w: W - 0.5, h: 0.75, isTextBox: true, margin: 0, fontFace: BF, fontSize: 11, color: "C6D2E4", valign: "middle" });


// ================= 10e. THE PARETO FRONT TODAY =================
s = pres.addSlide();
titleBar(s, "THE PARETO FRONT, DRAWN", "What 'front moved?' means: the set of hosts no other host beats on both coupling and magnetisation", false);
s.addImage({ path: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/assets/pareto_front.png", x: M, y: 1.55, w: 7.3, h: 5.07 });
card(s, 8.3, 1.55, 4.3, 5.07, PANEL);
s.addText("How to read it", { x: 8.55, y: 1.7, w: 3.9, h: 0.26, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12.5, bold: true, color: INK });
s.addText("Every credible host plotted at the coupling it would give Nd (measured Gd gap scaled by (gJ−1)J) against the Ms it would give with Nd. The red line joins the hosts that are not dominated: no other host has both a larger gap and a larger Ms. Colour, where present, is the MACE hull energy of the Nd cell.",
  { x: 8.55, y: 2.0, w: 3.95, h: 1.35, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10, color: MUTE });
s.addText("The front today", { x: 8.55, y: 3.45, w: 3.9, h: 0.26, isTextBox: true, margin: 0, fontFace: BF, fontSize: 12.5, bold: true, color: INK });
const pf = [["Fe₁₇Gd₂N₂ → Nd", "2.04 T · 82 meV", "highest Ms, below the coupling floor"], ["BFe₁₄Gd₂ → Nd", "2.03 T · 107 meV", "the Nd₂Fe₁₄B reference point"],
            ["Co₂Fe₇Gd₃ → Nd", "1.85 T · 110 meV", "RE-rich, hull +20 meV"], ["GdFe₂ → Nd", "1.81 T · 123 meV", "Laves, RE-rich"],
            ["Co₁₉Fe₄Gd₆ → Nd", "1.59 T · 130 meV", "strongest coupling at >1.5 T"], ["CFe₁₇Gd₂ → Nd", "1.35 T · 133 meV", "fm side suspect, re-running"]];
pf.forEach(([a, b, c], i) => {
  const y = 3.75 + i * 0.4;
  s.addText(a, { x: 8.55, y, w: 1.7, h: 0.22, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.5, bold: true, color: RE });
  s.addText(b, { x: 10.25, y, w: 1.2, h: 0.22, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9.5, color: INK });
  s.addText(c, { x: 8.55, y: y + 0.19, w: 3.9, h: 0.2, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.3, color: MUTE });
});
s.addText("Stop rule: a wave that adds no point to this line, after its labels are measured, has not moved the front. Two such waves in a row and the pool is exhausted for the current thresholds.",
  { x: 8.55, y: 6.15, w: 3.95, h: 0.45, isTextBox: true, margin: 0, fontFace: BF, fontSize: 9, italic: true, color: INK });
s.addText("Learnt: the front is the known magnets plus RE-rich cells; every point on it is either a reference compound or fails the hull or the coupling floor. The target region, upper right of both dashed lines, is empty - that is the space the waves are drawn to fill.",
  { x: M, y: 6.72, w: W, h: 0.5, isTextBox: true, margin: 0, fontFace: BF, fontSize: 10.5, italic: true, color: INK });

// ================= CLOSING: GP + CAUSAL + GENERATIVE =================
s = pres.addSlide();
s.background = { color: NAVY };
titleBar(s, "CLOSING THE LOOP", "Gaussian process for where to look, causal model for which lever, generative model for what to propose", true);

const nodes = [
  ["Labelled data", "180 Gd pairs → gap, h, moments, geometry\n+ 20 light-RE runs\n+ MACE hull for every cell", RE],
  ["Gaussian process", "on physics descriptors (h, Fe density,\nd_RE-TM, Z_RT, Co fraction, interstitial)\n→ gap, Ms, E_hull with uncertainty", "3E7FA6"],
  ["Causal layer", "structural causal model\nhost → S₅d → gap; interventions,\nnot correlations, rank the levers", GOLD],
  ["Generative proposal", "diffusion / MatterGen conditioned on\ndense Fe, short RE-TM, early TM;\nMACE hull as the first filter", FE],
  ["One run per cell", "f-in-core relaxation gives\nMs, h → gap, T*; results\nre-train every layer", "C6472A"],
];
nodes.forEach(([h, d, c], i) => {
  const x = M + i * 2.48;
  s.addShape(pres.ShapeType.roundRect, { x, y: 1.75, w: 2.22, h: 1.95, rectRadius: 0.08, fill: { color: c } });
  s.addText(h, { x: x + 0.12, y: 1.86, w: 1.98, h: 0.36, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12.5, bold: true, color: WHITE, align: "center" });
  s.addText(d, { x: x + 0.12, y: 2.26, w: 1.98, h: 1.38, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 8.6, color: "F0F4FA", align: "center" });
  if (i < 4) s.addText("→", { x: x + 2.2, y: 2.5, w: 0.3, h: 0.4, isTextBox: true, margin: 0,
    fontFace: "Arial", fontSize: 18, bold: true, color: "8FA3C0", align: "center" });
});
const loopR = M + 4 * 2.48 + 1.11, loopL = M + 1.11;
s.addShape(pres.ShapeType.line, { x: loopR, y: 3.7, w: 0, h: 0.5, line: { color: "8FA3C0", width: 1.5 } });
s.addShape(pres.ShapeType.line, { x: loopL, y: 4.2, w: loopR - loopL, h: 0, line: { color: "8FA3C0", width: 1.5 } });
s.addShape(pres.ShapeType.line, { x: loopL, y: 3.7, w: 0, h: 0.5, line: { color: "8FA3C0", width: 1.5, beginArrowType: "triangle" } });
s.addText("every batch is a designed experiment: it must move the GP posterior or test a causal edge, not just add points",
  { x: M + 2.0, y: 4.24, w: 8.0, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10, italic: true, color: "8FA3C0", align: "center" });

// ---- bottom row: causal DAG (left) + two short rationale cards (right)
s.addShape(pres.ShapeType.roundRect, { x: M, y: 4.7, w: 6.1, h: 2.1, rectRadius: 0.06, fill: { color: NAVY2 } });
s.addText("The causal model the data support", { x: M + 0.2, y: 4.8, w: 5.7, h: 0.28, isTextBox: true, margin: 0, fontFace: BF, fontSize: 11.5, bold: true, color: GOLD });
const dagN = {
  geom: [M + 0.25, 5.25, "RE-TM distance\ncoordination", RE],
  chem: [M + 0.25, 5.95, "Fe / Co mix\ninterstitial site", RE],
  s5d: [M + 2.35, 5.6, "S₅d on the RE\n(h)", GOLD],
  gap: [M + 4.3, 5.25, "RE-TM gap\nT*, anisotropy lock", FE],
  ms: [M + 4.3, 5.95, "Ms\n(Fe density + RE)", FE],
};
Object.values(dagN).forEach(([x, y, t, c]) => {
  s.addShape(pres.ShapeType.roundRect, { x, y, w: 1.55, h: 0.58, rectRadius: 0.08, fill: { color: c } });
  s.addText(t, { x, y, w: 1.55, h: 0.58, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8, bold: true, color: WHITE, align: "center", valign: "middle" });
});
const arrow = (x1, y1, x2, y2) => s.addShape(pres.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color: "C6D2E4", width: 1.4, endArrowType: "triangle" } });
arrow(M + 1.8, 5.54, M + 2.35, 5.78); arrow(M + 1.8, 6.24, M + 2.35, 6.0); arrow(M + 3.9, 5.78, M + 4.3, 5.56);
s.addShape(pres.ShapeType.line, { x: M + 1.8, y: 6.3, w: 2.5, h: 0, line: { color: "C6D2E4", width: 1.4, dashType: "dash", endArrowType: "triangle" } });
s.addText("mediator: every host lever acts through S₅d (r = 0.89); Ms is set separately by Fe density and the RE. Interventions on the left are what a generative model may propose; the dashed edge is the Co trade-off.",
  { x: M + 0.2, y: 6.6, w: 5.7, h: 0.2, isTextBox: true, margin: 0, fontFace: BF, fontSize: 7.6, italic: true, color: "AEBBD0" });
const lanes = [
  ["Gaussian process", "180 points, smooth physics descriptors, batch size fixed by one packed job. Mean function = 1574·h so the GP learns residuals; q-EI with a diversity penalty picks each batch. Each label is now ONE f-in-core run, so a round is 150-200 compounds per 25-node job."],
  ["Generative + causal", "The pool is exhausted above ≈ 1.75 T. A diffusion model conditioned on the causal parents - dense Fe, RE-TM < 3.0 Å, 12-fold coordination, partial Co, no H in the RE shell - proposes frameworks; MACE hull filters; the causal graph tells it which knobs are real and which are confounded."],
];
lanes.forEach(([h, d], i) => {
  const x = 7.0 + i * 2.85;
  s.addShape(pres.ShapeType.roundRect, { x, y: 4.7, w: 2.75, h: 2.1, rectRadius: 0.06, fill: { color: NAVY2 } });
  s.addText(h, { x: x + 0.18, y: 4.8, w: 2.4, h: 0.3, isTextBox: true, margin: 0, fontFace: BF, fontSize: 11.5, bold: true, color: GOLD });
  s.addText(d, { x: x + 0.18, y: 5.12, w: 2.42, h: 1.62, isTextBox: true, margin: 0, fontFace: BF, fontSize: 8.4, color: "C6D2E4" });
});
s.addText("The campaign's product is not a compound; it is a calibrated instrument for RE-TM exchange and the first dataset a learning loop can be trained on.",
  { x: M, y: 6.92, w: W, h: 0.35, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, italic: true, color: "8FA3C0" });
s.addNotes("GP: use h-based linear mean, Matern kernel on standardised descriptors; batch acquisition with diversity penalty sized to the packed job. Causal: DAG host-geometry -> S5d -> gap; Fe density -> Ms; interstitial site -> S5d. Generative: MatterGen-style conditioned on composition and target Fe density.");

pres.writeFile({ fileName: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/MAGNITO_Fe-HREE_screening.pptx" })
  .then(f => console.log("wrote", f));
