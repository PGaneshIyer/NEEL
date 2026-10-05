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
s.addText("706 paired DFT calculations staged  ·  352 compounds  ·  5 databases screened", {
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
  ["1", "survives every remaining check", "3 of those 4 carried implausible multi-eV exchange energies - an LDA+U multi-minima artefact, not real coupling", NAVY2, WHITE],
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

// ================= 8. RESULTS =================
s = pres.addSlide();
titleBar(s, "CAMPAIGN RESULTS", "One candidate survives every validity check", false);

card(s, M, 1.6, 5.55, 2.3);
s.addText("353 compounds analysed  ->  1 credible ferromagnet", {
  x: M + 0.28, y: 1.76, w: 5.0, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 12.5, bold: true, color: INK });
const why = [
  ["Implausible exchange energy", "3-5.5 eV/Gd, 10-15x any real value - LDA+U landing in a different state, not physical coupling"],
  ["Untracked sublattice collapse", "a spectator element (Os, Y, Lu, Ru, Ce...) shifting between fm/ferri, invisible if only Fe/Co are watched"],
  ["TM sublattice itself collapsed", "the Fe or Co moment changed between runs - the failure the constrained rerun was built to fix"],
];
why.forEach(([h, d], i) => {
  const y = 2.12 + i * 0.58;
  numCircle(s, M + 0.28, y, i + 1, FE);
  s.addText(h, { x: M + 0.85, y: y - 0.03, w: 4.55, h: 0.22, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10.5, bold: true, color: INK });
  s.addText(d, { x: M + 0.85, y: y + 0.18, w: 4.6, h: 0.36, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 8.5, color: MUTE });
});

card(s, 6.45, 1.6, 5.15, 2.3, NAVY2);
s.addText("Co16Gd2Mn  ·  new-R3m", {
  x: 6.73, y: 1.76, w: 4.6, h: 0.28, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13.5, bold: true, color: GOLD });
s.addText("Co-rich 2-17-like lattice, Mn on one Co site", {
  x: 6.73, y: 2.04, w: 4.6, h: 0.24, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 9.5, italic: true, color: "AEBBD0" });
const stats = [["dE (ferri - fm)", "+114.5 meV/Gd"], ["ground state", "ferromagnetic"], ["u0Ms", "1.95 T"]];
stats.forEach(([k, v], i) => {
  const y = 2.34 + i * 0.3;
  s.addText(k, { x: 6.73, y, w: 2.5, h: 0.26, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10, color: "8FA3C0" });
  s.addText(v, { x: 9.3, y, w: 2.15, h: 0.26, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, bold: true, color: WHITE, align: "right" });
});
s.addText("Mn couples ferromagnetically to Gd while Co keeps its usual antiparallel preference - flipping the net RE-TM sign for the compound.",
  { x: 6.73, y: 3.3, w: 4.6, h: 0.55, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 8.5, color: "C6D2E4" });

card(s, M, 4.05, W, 0.48, PANEL);
s.addText("Validated: stable Co sublattice, stable Mn magnitude, normal exchange-energy scale, clean EDIFF convergence on both configs (47 / 29 SCF steps of 400).",
  { x: M + 0.25, y: 4.05, w: W - 0.5, h: 0.48, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10, italic: true, color: RE, valign: "middle" });

s.addText("Projected magnetisation for the real target compositions", {
  x: M, y: 4.66, w: 7.5, h: 0.26, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 12.5, bold: true, color: INK });
s.addText("Three of five heavy-RE analogues clear the 2 T program target.",
  { x: 8.6, y: 4.68, w: 4.0, h: 0.24, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9.5, italic: true, color: FE, align: "right" });
const prows2 = [
  [{ text: "Parent compound", options: { bold: true } }, { text: "Heavy RE", options: { bold: true } },
   { text: "Projected u0Ms", options: { bold: true } }],
  ["Co16Dy2Mn", "Dy", "2.26 T"],
  ["Co16Ho2Mn", "Ho", "2.26 T"],
  ["Co16MnTb2", "Tb", "2.17 T"],
  ["Co16Er2Mn", "Er", "2.17 T"],
  ["Co16MnTm2", "Tm", "1.98 T"],
];
s.addTable(prows2, {
  x: M, y: 5.0, w: W, colW: [W * 0.34, W * 0.33, W * 0.33],
  fontFace: BF, fontSize: 11, color: INK, border: { type: "solid", color: "D5DDE8", pt: 1 },
  fill: { color: WHITE }, rowH: 0.27, valign: "middle",
});

// ================= 8a. RELATIONSHIP TO Sm2Co17 =================
s = pres.addSlide();
titleBar(s, "STRUCTURAL LINEAGE", "A one-atom variant of a magnet already on the market", false);

const cardW = 3.75, imgW = cardW - 0.5, imgH = 2.75, cardH = 4.35, cardY = 1.6;
card(s, M, cardY, cardW, cardH, PANEL);
s.addImage({ path: "assets/tb2mnco16.png", x: M + 0.25, y: cardY + 0.2, w: imgW, h: imgH, sizing: { type: "contain", w: imgW, h: imgH } });
s.addText("Tb2MnCo16  -  parent (GNoME)", { x: M + 0.25, y: cardY + 2.97, w: imgW, h: 0.26, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 10.5, bold: true, color: INK, align: "center" });
s.addText("Th2Zn17 prototype, R-3m (#166) - independently DFT-relaxed by GNoME, Tb in the RE site, one of 17 TM sites occupied by Mn.",
  { x: M + 0.25, y: cardY + 3.25, w: imgW, h: 1.0, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9, color: MUTE, align: "center" });

const col2X = M + cardW + 0.3;
card(s, col2X, cardY, cardW, cardH, NAVY2);
s.addImage({ path: "assets/co16gd2mn_sub.png", x: col2X + 0.25, y: cardY + 0.2, w: imgW, h: imgH, sizing: { type: "contain", w: imgW, h: imgH } });
s.addText("Co16Gd2Mn_sub  -  FM candidate", { x: col2X + 0.25, y: cardY + 2.97, w: imgW, h: 0.26, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 10.5, bold: true, color: GOLD, align: "center" });
s.addText("Identical lattice - Gd stands in for Tb (explicit 4f, S-state surrogate). Same Mn-for-Co site. Only the RE identity changes.",
  { x: col2X + 0.25, y: cardY + 3.25, w: imgW, h: 1.0, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9, color: "C6D2E4", align: "center" });

const col3X = col2X + cardW + 0.3, col3W = W - (col3X - M);
card(s, col3X, cardY, col3W, cardH, "FCEDE8");
s.addText("The real magnet this descends from", { x: col3X + 0.28, y: cardY + 0.2, w: col3W - 0.56, h: 0.5, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13.5, bold: true, color: FE });
const lineage = [
  ["Sm2Co17", "commercial 2:17 SmCo permanent magnet - one of only two SmCo classes ever commercialised (with SmCo5, the 1:5 type)"],
  ["RE2Co17", "the general Th2Zn17-type family - Y, Ce, Pr, Nd, Sm, Gd, Tb... all form this same rhombohedral structure"],
  ["RE2MnCo16", "one of the 17 transition-metal sites replaced by Mn - the single change this campaign is built around"],
];
lineage.forEach(([h, d], i) => {
  const y = cardY + 0.85 + i * 0.98;
  numCircle(s, col3X + 0.28, y, i + 1, i === 2 ? FE : RE);
  s.addText(h, { x: col3X + 0.86, y: y - 0.03, w: col3W - 1.2, h: 0.26, isTextBox: true, margin: 0,
    fontFace: HF, fontSize: 13, bold: true, color: "8A3B2E" });
  s.addText(d, { x: col3X + 0.86, y: y + 0.24, w: col3W - 1.2, h: 0.62, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9.3, color: "7A4034" });
});

card(s, M, cardY + cardH + 0.2, W, 7.1 - (cardY + cardH + 0.2), NAVY2);
s.addText("Every candidate in this campaign is a controlled chemical edit of an already-magnetic parent - swap the light RE for a heavy one, then perturb one transition-metal site. Co16Gd2Mn_sub is the one edit, out of 353, where that perturbation flips the whole compound's magnetic order rather than just its Curie temperature or anisotropy.",
  { x: M + 0.3, y: cardY + cardH + 0.2, w: W - 0.6, h: 7.1 - (cardY + cardH + 0.2), isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, italic: true, color: "C6D2E4", valign: "middle" });

// ================= 8b. WHY MN, AND TIER-2 VERIFICATION =================
s = pres.addSlide();
titleBar(s, "WHY MN, AND WHAT'S BEING VERIFIED", "A one-atom coupling lever, now being checked without the Gd stand-in", false);

card(s, M, 1.6, 5.9, 3.55, NAVY2);
s.addText("Why a magnetic Mn site flips the sign", {
  x: M + 0.3, y: 1.82, w: 5.3, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 14, bold: true, color: GOLD });
const mnLogic = [
  "Heavy-RE-TM magnets are ferrimagnetic by default: the 4f moment polarises the RE's own 5d shell parallel (intra-atomic), and that 5d hybridises antiparallel with neighbouring Fe/Co 3d (Campbell's rule). Net result: RE and TM sublattices oppose.",
  "Mn is the known exception to that rule. Its 3d filling differs enough from Fe/Co that RE-Mn coupling is frequently parallel (ferromagnetic) rather than antiparallel, in contrast to the near-universal RE-Co antiparallel preference.",
  "Every DFT run in this campaign confirms it directly: in Co16Gd2Mn_sub and every native-RE compound checked so far, the Mn site's own moment aligns WITH the RE 4f moment, while all 16 Co sites align against it - a completely consistent sign pattern, not a coincidence.",
  "One Mn atom against sixteen Co atoms cannot flip the lattice by weight of numbers - but it only has to tip the net energy balance, not the head count. That single competing bond is apparently enough: fm sits 114.5 meV/Gd below ferri for this compound.",
];
mnLogic.forEach((t, i) => {
  const y = 2.2 + i * 0.72;
  numCircle(s, M + 0.3, y, i + 1, i === 2 ? FE : RE);
  s.addText(t, { x: M + 0.88, y: y - 0.04, w: 4.85, h: 0.68, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9.8, color: "C6D2E4" });
});

card(s, 6.5, 1.6, W - 5.8, 3.55, PANEL);
s.addText("Tier-2: checking the mechanism without the Gd stand-in", {
  x: 6.8, y: 1.82, w: W - 6.4, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13, bold: true, color: INK });
s.addText("Everything above used Gd as a computational surrogate for Tb/Dy/Ho/Er/Tm (explicit 4f, S-state, tractable). potpaw_PBE.64 ships an explicit-4f potential for all five real heavy REs too, so the natural next check is direct: relax each real RE on its own native lattice, no surrogate, no de Gennes projection.",
  { x: 6.8, y: 2.14, w: W - 6.4, h: 0.62, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9.5, color: MUTE });
const t2rows = [
  [{ text: "Compound", options: { bold: true } }, { text: "fm", options: { bold: true } },
   { text: "ferri", options: { bold: true } }, { text: "Status", options: { bold: true } }],
  ["Co16Tb2Mn", "not converged", "clean", "in progress"],
  ["Co16Dy2Mn", "clean", "symmetry-broken", "in progress"],
  ["Co16Ho2Mn", "killed (walltime)", "symmetry-broken", "in progress"],
  ["Co16Er2Mn", "collapsed to ferri-like", "inhomogeneous", "in progress"],
  ["Co16Tm2Mn", "killed (walltime)", "killed (walltime)", "in progress"],
];
s.addTable(t2rows, {
  x: 6.8, y: 2.86, w: W - 6.4, colW: [(W - 6.4) * 0.28, (W - 6.4) * 0.24, (W - 6.4) * 0.28, (W - 6.4) * 0.2],
  fontFace: BF, fontSize: 8.3, color: INK, border: { type: "solid", color: "D5DDE8", pt: 1 },
  fill: { color: WHITE }, rowH: 0.25, valign: "middle",
});
s.addText("No compound yet has both configs converged to a coherent, symmetric state - no fm-vs-ferri energy is trustworthy yet. Unconstrained relaxation let the two equivalent RE sites break symmetry, and Mn's moment collapsed when they did. Next: rerun with the total moment locked, then release to an unconstrained static.",
  { x: 6.8, y: 4.44, w: W - 6.4, h: 0.68, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 8.3, italic: true, color: FE });

card(s, M, 5.35, W, 0.5, NAVY2);
s.addText("The only validated, promising result to date remains Co16Gd2Mn_sub (Gd surrogate, Tb's native lattice): dE = +114.5 meV/Gd, ferromagnetic ground state, u0Ms = 1.95 T. Tier-2 exists to confirm this holds for the real heavy REs - it has not yet confirmed or refuted it.",
  { x: M + 0.28, y: 5.35, w: W - 0.56, h: 0.5, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10.5, italic: true, color: GOLD, valign: "middle" });

// ================= 8c. PER-ATOM MOMENTS =================
s = pres.addSlide();
titleBar(s, "PER-ATOM MOMENTS, DIRECTLY MEASURED", "Mn always sides with Gd - never with Co - in both configurations", false);

const siteCard = (x, w, label, gd, mn, coRange, coAvg, total, dark) => {
  card(s, x, 1.66, w, 4.55, dark ? NAVY2 : PANEL);
  const tc = dark ? WHITE : INK, mc = dark ? "AEBBD0" : MUTE, ac = dark ? GOLD : RE;
  s.addText(label, { x: x + 0.32, y: 1.86, w: w - 0.64, h: 0.34, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 15, bold: true, color: ac });
  const rows = [
    ["Gd  (sites 1, 2)", gd, FE],
    ["Mn  (site 3)", mn, GOLD],
    [`Co  (16 sites, ${coRange})`, coAvg, dark ? "8FA3C0" : MUTE],
  ];
  rows.forEach(([k, v, vc], i) => {
    const y = 2.4 + i * 0.86;
    card(s, x + 0.32, y, w - 0.64, 0.7, dark ? "24345C" : WHITE);
    s.addText(k, { x: x + 0.55, y: y + 0.1, w: w - 1.1, h: 0.26, isTextBox: true, margin: 0,
      fontFace: BF, fontSize: 11, color: mc });
    s.addText(v, { x: x + 0.55, y: y + 0.36, w: w - 1.1, h: 0.3, isTextBox: true, margin: 0,
      fontFace: HF, fontSize: 15, bold: true, color: vc });
  });
  s.addText("total moment", { x: x + 0.32, y: 4.98, w: w * 0.5, h: 0.22, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9.5, charSpacing: 1, color: mc });
  s.addText(total, { x: x + 0.32, y: 5.2, w: w - 0.64, h: 0.34, isTextBox: true, margin: 0,
    fontFace: HF, fontSize: 18, bold: true, color: tc });
};

siteCard(M, 5.9, "FM  -  all three sublattices aligned",
  "+6.74, +6.75 uB", "+3.13 uB", "+1.49 to +1.59 uB", "avg +1.53 uB", "41.1 uB", true);
siteCard(M + 6.15, W - 6.15, "FERRI  -  Gd and Mn flip together, Co doesn't",
  "-7.06, -7.04 uB", "-3.38 uB", "+1.37 to +1.53 uB", "avg +1.47 uB", "6.15 uB", false);

card(s, M, 6.35, W, 0.55, "FCEDE8");
s.addText("Mn's moment matches Gd's sign in every configuration checked - fm or ferri, this compound or any native-RE compound in the Tier-2 batch. Co never once follows it. That is the direct measurement behind the Campbell's-rule exception this campaign is built on.",
  { x: M + 0.28, y: 6.35, w: W - 0.56, h: 0.55, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 10.5, italic: true, color: "8A3B2E", valign: "middle" });
s.addNotes("Source: OUTCAR_04 for Co16Gd2Mn_sub (runs/ternary/Tb/new-R3m/Co16Gd2Mn_sub), the validated release-stage static - the same result behind dE=114.5 meV/Gd. Per-site magnetization(x) table, LORBIT=11 atomic-sphere projection.");

// ================= 9. CAMPBELL -> OTHER HREE =================
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
s = pres.addSlide();
titleBar(s, "BEYOND WHAT THE DATABASES HOLD", "Generating candidates: decoration, then symmetry", false);

card(s, M, 1.66, 6.0, 3.35);
s.addText("Prototype decoration  —  run this", {
  x: M + 0.32, y: 1.86, w: 5.4, h: 0.32, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 15, bold: true, color: RE });
s.addText("Substitute the X site of each named magnet prototype through a magnet-relevant palette (Al, Si, Ga, Ge, B, C, N, P, Sn, Sb, Ti, V, Cr, Zr, Nb, Mo, W, Hf, Ta), plus an Fe↔Co swap. Chemically conservative, and historically how most real magnets were found.",
  { x: M + 0.32, y: 2.24, w: 5.4, h: 1.0, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, color: MUTE });
const gen = [["CaCu₅-RT₄X", 61], ["ThMn₁₂-stabilized", 21], ["Th₂Zn₁₇-interstitial", 21],
             ["LaCo₉Si₄", 21], ["Nd₂Fe₁₄B", 20], ["RT₃ / Th₂Zn₁₇", 2]];
gen.forEach(([n, k], i) => {
  const y = 3.20 + i * 0.24;
  s.addText(n, { x: M + 0.32, y, w: 3.4, h: 0.22, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, color: INK });
  s.addShape(pres.ShapeType.roundRect, { x: M + 3.75, y: y + 0.04, w: k / 61 * 1.5, h: 0.16,
    rectRadius: 0.03, fill: { color: RE } });
  s.addText(String(k), { x: M + 5.35, y, w: 0.5, h: 0.24, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, bold: true, color: RE });
});
s.addText("146 new candidates — including GdFe₁₁Si / GdAlFe₁₁ / GdFe₁₁N, the real 1-12 magnet chemistry",
  { x: M + 0.32, y: 4.58, w: 5.4, h: 0.4, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11, bold: true, color: RE });

card(s, 7.0, 1.66, 5.6, 3.35, PANEL);
s.addText("Wyckoff generation  —  second priority", {
  x: 7.32, y: 1.86, w: 5.0, h: 0.32, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 15, bold: true, color: MUTE });
s.addText("Place the stoichiometry on the symmetry orbits of a target space group. Reaches genuinely new frameworks rather than re-decorating known ones — but the structures come out unrelaxed, the hit rate is low, and the volume (10⁴–10⁵) only makes sense behind a machine-learned potential.",
  { x: 7.32, y: 2.24, w: 5.0, h: 1.15, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, color: MUTE });
s.addText("Neither generator produces a hull distance — which is the whole point of the ≤ 0.2 eV/atom criterion.",
  { x: 7.32, y: 3.5, w: 5.0, h: 0.55, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, bold: true, color: INK });
s.addText("MLIP-relax (MACE / CHGNet) → E_hull against MP + Alexandria → keep ≤ 0.2 eV/atom → only then DFT.",
  { x: 7.32, y: 4.05, w: 5.0, h: 0.6, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, color: FE });

card(s, M, 5.2, W, 1.1, NAVY2);
s.addText("Generated ≠ stable", { x: M + 0.32, y: 5.35, w: 3, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 13.5, bold: true, color: GOLD });
s.addText("Database candidates arrive with a hull distance; generated ones do not. For 146 decorations the MLIP filter costs minutes — for a Wyckoff sweep it is the only thing that makes DFT affordable at all.",
  { x: M + 0.32, y: 5.68, w: W - 0.7, h: 0.5, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, color: "C6D2E4" });

// ================= 10. ACTIVE LEARNING WORKFLOW =================
s = pres.addSlide();
s.background = { color: NAVY };
titleBar(s, "CLOSING THE LOOP", "Steering the next DFT batch with active learning", true);

const nodes = [
  ["706 labelled\nfm / ferri pairs", "ΔE, site moments,\nhull distance", RE],
  ["Surrogate model", "GNN or GP on structure\n→ ΔE, Mₙₑₜ, Eₕᵤₗₗ", "3E7FA6"],
  ["Acquisition\n+ batch select", "q-EI / UCB on Mₙₑₜ,\ndiversity-penalised", GOLD],
  ["Generative proposal", "diffusion model conditioned\non high Mₙₑₜ, low Eₕᵤₗₗ", FE],
  ["Next DFT batch", "~60 packed nodes,\none job, ~6 h", "C6472A"],
];
nodes.forEach(([h, d, c], i) => {
  const x = M + i * 2.48;
  s.addShape(pres.ShapeType.roundRect, { x, y: 2.0, w: 2.22, h: 1.72, rectRadius: 0.08, fill: { color: c } });
  s.addText(h, { x: x + 0.14, y: 2.16, w: 1.94, h: 0.66, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12.5, bold: true, color: WHITE, align: "center" });
  s.addText(d, { x: x + 0.14, y: 2.86, w: 1.94, h: 0.72, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9.5, color: "F0F4FA", align: "center" });
  if (i < 4) s.addText("→", { x: x + 2.2, y: 2.62, w: 0.3, h: 0.4, isTextBox: true, margin: 0,
    fontFace: "Arial", fontSize: 18, bold: true, color: "8FA3C0", align: "center" });
});
// return loop: drops out of the LAST node, runs right-to-left, arrows up into the FIRST
const loopR = M + 4 * 2.48 + 1.11, loopL = M + 1.11;
s.addShape(pres.ShapeType.line, { x: loopR, y: 3.72, w: 0, h: 0.66, line: { color: "8FA3C0", width: 1.5 } });
s.addShape(pres.ShapeType.line, { x: loopL, y: 4.38, w: loopR - loopL, h: 0, line: { color: "8FA3C0", width: 1.5 } });
s.addShape(pres.ShapeType.line, { x: loopL, y: 3.72, w: 0, h: 0.66, line: { color: "8FA3C0", width: 1.5, beginArrowType: "triangle" } });
s.addText("results re-train the surrogate each round", {
  x: M + 3.6, y: 4.42, w: 5.0, h: 0.3, isTextBox: true, margin: 0,
  fontFace: BF, fontSize: 10.5, italic: true, color: "8FA3C0", align: "center" });

const lanes = [
  ["Bayesian optimisation", "Cheapest to stand up. Fits the problem: a scalar objective (net moment, or ΔE > 0) over a fixed 1,152-compound pool, batched to match one packed Perlmutter job."],
  ["Reinforcement learning", "Treats substitution as sequential decisions — which site, which element. Useful once the pool is exhausted and the search must generate rather than select."],
  ["Diffusion / generative", "MatterGen-style, conditioned on high uncompensated moment. Proposes new decorations of the 2-17 and 1-12 frameworks instead of re-ranking known ones."],
  ["MLIP pre-filter", "Fine-tune MACE on this campaign's spin-polarised data, then relax and pre-rank thousands of proposals before any DFT is spent."],
];
lanes.forEach(([h, d], i) => {
  const x = M + i * 3.11;
  s.addShape(pres.ShapeType.roundRect, { x, y: 4.95, w: 2.85, h: 1.65, rectRadius: 0.06, fill: { color: NAVY2 } });
  s.addText(h, { x: x + 0.2, y: 5.1, w: 2.5, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 12, bold: true, color: GOLD });
  s.addText(d, { x: x + 0.2, y: 5.42, w: 2.5, h: 1.1, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 9.5, color: "C6D2E4" });
});
s.addText("The 706 runs are the seed dataset: the first systematically computed RE-TM exchange labels for this chemistry.",
  { x: M, y: 6.75, w: W, h: 0.35, isTextBox: true, margin: 0,
    fontFace: BF, fontSize: 11.5, italic: true, color: "8FA3C0" });
s.addNotes("The point of the loop: each DFT batch is expensive and queue-bound, so batch composition matters more than per-run speed. BO with a diversity penalty matches the packed-job batch size.");

pres.writeFile({ fileName: "/Users/g5q/Documents/GitHub/gnome-fe-hree-magnets/MAGNITO_Fe-HREE_screening.pptx" })
  .then(f => console.log("wrote", f));
