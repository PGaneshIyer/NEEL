#!/usr/bin/env python3
"""Draw the GP wave loop as a PNG (and SVG) for the README / deck.
Writes ../docs/gp_wave_loop.png and .svg"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(os.path.dirname(HERE), "docs")
os.makedirs(DOCS, exist_ok=True)
INK, MUTE = "#1A2233", "#5A6478"
COL = {"data": ("#E1F5EE", "#0F6E56"), "model": ("#EEEDFE", "#3C3489"), "nersc": ("#FAECE7", "#993C1D"), "step": ("#F1EFE8", "#444441")}

fig, ax = plt.subplots(figsize=(13, 7.6), dpi=200)
ax.set_xlim(0, 13); ax.set_ylim(0, 7.6); ax.axis("off")

def lane(y0, y1, label):
    ax.add_patch(FancyBboxPatch((0.3, y0), 12.4, y1 - y0, boxstyle="round,pad=0.02,rounding_size=0.1", fc="none", ec="#B4B2A9", ls="--", lw=0.8))
    ax.text(0.45, y1 - 0.22, label, fontsize=10, color=MUTE, va="top")

def box(x, y, w, h, title, sub, kind, script=None):
    fc, tc = COL[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=tc, lw=1.0))
    ax.text(x + w / 2, y + h - 0.22, title, ha="center", va="top", fontsize=11, color=tc, fontweight="bold")
    ax.text(x + w / 2, y + h - 0.46, sub, ha="center", va="top", fontsize=8.6, color=tc, linespacing=1.3)
    if script:
        ax.text(x + w / 2, y + 0.08, script, ha="center", va="bottom", fontsize=7.8, color=tc, family="monospace")

def arrow(p, q, style="-|>", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=14, lw=1.2, color=MUTE, ls=ls, connectionstyle=f"arc3,rad={rad}"))

# lanes
lane(5.05, 7.5, "LAPTOP or NERSC LOGIN  ·  analysis and GP  (minutes)")
lane(2.95, 4.95, "PERLMUTTER LOGIN  ·  inputs and submission  (existing NEEL scripts)")
lane(1.55, 2.85, "PERLMUTTER COMPUTE  ·  one packed wave  (queue 1-2 d, run 3 h)")
lane(0.05, 1.45, "LAPTOP or NERSC LOGIN  ·  pull, label, decide")

# row 1
box(0.6, 5.3, 2.9, 1.6, "Seed labels", "180 Gd fm/ferri pairs → h, gap\n+ every ingested wave run", "data", "results.json · labels.csv")
box(3.9, 5.3, 3.3, 1.6, "GP with physics mean", "mean = ridge(geometry) → h\nMatern GP on residuals\n10-fold CV r = 0.88", "model", "wave_gp.py")
box(7.6, 5.3, 3.3, 1.6, "Acquire one wave", "P(gap_RE ≥ 150 meV) · [Ms ≥ 1.5 T]\n· [E_hull ≤ 30 meV] + κ·σ\nprototype cap, kriging-believer", "model", "wave_gp.py --wave k")
# row 2
box(9.6, 3.05, 3.0, 1.4, "Candidate pool", "recovered DB structures, generated\ndecorations, strong hosts × {Nd,Sm,+Co}\nMACE relax · same-model MP hull", "data", "wave_pool.py")
box(6.0, 3.05, 3.2, 1.4, "Make inputs, push", "one f-in-core ISIF=3 relax\nper cell, from the MACE cell", "step", "wave_inputs.py · push_new_runs.sh")
box(2.4, 3.05, 3.2, 1.4, "Submit packed job", "size from live queue data\n32-63 node band, 3 h", "step", "pick_nodes.py · submit_batch.sh")
# row 3
box(2.4, 1.62, 3.2, 0.75, "Wave runs", "VASP · no fm/ferri pair · no +U", "nersc", "")
# row 4
box(2.4, 0.12, 3.2, 0.85, "Mirror and label", "h, Ms, V from OUTCAR → labels.csv", "data", "sync_results.sh · wave_ingest.py")
box(6.0, 0.12, 3.2, 0.85, "Decide", "H1 check · GP CV · Pareto front · stop when EI → 0", "model", "gp_report.txt")

# arrows
arrow((3.5, 6.1), (3.9, 6.1)); arrow((7.2, 6.1), (7.6, 6.1))
ax.plot([11.1, 11.1], [4.45, 6.1], color=MUTE, lw=1.2); arrow((11.1, 6.1), (10.9, 6.1))          # pool -> acquisition
arrow((9.6, 3.75), (9.2, 3.75))                                                                  # pool cells -> inputs
arrow((9.25, 5.3), (9.25, 4.45))                                                                 # wave -> inputs
arrow((6.0, 3.75), (5.6, 3.75))
arrow((4.0, 3.05), (4.0, 2.37)); arrow((4.0, 1.62), (4.0, 0.97))
arrow((5.6, 0.55), (6.0, 0.55))
ax.plot([2.4, 1.6, 1.6], [0.55, 0.55, 5.3], color=MUTE, lw=1.2); arrow((1.6, 5.1), (1.6, 5.3))
ax.text(0.45, 3.5, "labels grow\nthe training set", fontsize=8.6, color=MUTE, va="center")
ax.set_title("NEEL · GP-driven wave loop: every DFT label is one f-in-core run, every wave is a designed experiment", fontsize=12, color=INK, pad=6)
fig.tight_layout()
fig.savefig(os.path.join(DOCS, "gp_wave_loop.png")); fig.savefig(os.path.join(DOCS, "gp_wave_loop.svg"))
print("wrote docs/gp_wave_loop.png / .svg")
