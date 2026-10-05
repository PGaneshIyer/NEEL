#!/usr/bin/env python3
"""Pull in the scarce commodity: datasets that actually contain ANISOTROPY.

The five big DFT databases we screened (GNoME, MP, OQMD, Alexandria, AFLOW)
carry composition, stability and a moment. None of them carries MAE, exchange
constants or Tc at scale - which is exactly what a permanent magnet is judged
on. A handful of smaller datasets do, and they are worth more per entry than
the millions of rows we already have.

Roles, in the order they matter to this campaign:

  novamag   DFT Ms, MAE/K1, exchange constants and Tc for Fe-rich RE-lean
            candidates, built for permanent-magnet discovery. The only open
            source of systematic MAE at any scale. USE AS: the training and
            validation set for any MAE surrogate, and a direct source of
            A20-like anisotropy calibration for our Gd->Tb substitution model.
            CC-BY-4.0 on Zenodo; fetched by this script.

  magndata  ~2000 EXPERIMENTAL magnetic structures with propagation vectors and
            moment directions. USE AS: ground truth for the fm/ferri protocol.
            Every RE-TM entry is a direct test of whether we get the coupling
            sign right - a far stronger validation than GdFe2 alone.

  c2db      2D materials with systematically computed MAE and exchange. Wrong
            dimensionality for magnets, but USE AS: the benchmark set to
            establish whether an MAE surrogate generalises at all, before
            trusting one on bulk kagome candidates.

  heusler   Sanvito's ~236k Heusler high-throughput set (moments + estimated
            Tc). USE AS: a template for what a ternary screening funnel should
            report, and a large Tc-model training set. Mostly 50% TM, so it
            fails our >=60% TM criterion as candidates.

  tc        Nelson-Sanvito curated experimental Tc (~2500 ferromagnets).
            USE AS: training data for a composition-only Tc regressor, so Tc
            can be screened before computing exchange constants.

  nims      NIMS MatNavi / MDR rare-earth magnet data (ESICMM). The deepest
            experimental Nd-Fe-B and 1-12 record. Registration required, so
            this script only prints the entry point.

Not open, do not plan around: MPDS / Pauling File, Springer Materials.

Usage
  python3 external_data.py --list
  python3 external_data.py --fetch novamag --dest ../external
"""
import argparse
import json
import os
import ssl
import urllib.request

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()

SOURCES = {
    "novamag": {
        "what": "DFT Ms, MAE/K1, exchange, Tc for RE-lean permanent-magnet candidates",
        "why": "only open systematic MAE; train/validate the anisotropy surrogate",
        "open": True,
        "auto": "https://zenodo.org/api/records/3241267",
        "browse": "http://crono.ubu.es/novamag/",
        "cite": "P. Nieves et al., Comput. Mater. Sci. 168 (2019) 188-202; "
                "arXiv:1902.05241; Zenodo 10.5281/zenodo.3241267 (CC-BY-4.0)",
    },
    "magndata": {
        "what": "~2000 experimental magnetic structures (propagation vectors, moment directions)",
        "why": "ground truth for the fm/ferri coupling sign, beyond the GdFe2 control",
        "open": True,
        "auto": None,
        "browse": "https://www.cryst.ehu.es/magndata/",
        "cite": "Gallego et al., J. Appl. Cryst. 49 (2016) 1750",
    },
    "c2db": {
        "what": "2D materials with computed MAE and exchange couplings",
        "why": "benchmark an MAE surrogate before trusting it on bulk kagome",
        "open": True,
        "auto": None,
        "browse": "https://cmr.fysik.dtu.dk/c2db/c2db.html",
        "cite": "Haastrup et al., 2D Mater. 5 (2018) 042002; Gjerding et al. (2021)",
    },
    "heusler": {
        "what": "~236k Heusler compositions, high-throughput DFT moments + estimated Tc",
        "why": "Tc-model training data and a template for ternary funnel reporting",
        "open": True,
        "auto": None,
        "browse": "https://doi.org/10.1126/sciadv.1602241",
        "cite": "Sanvito et al., Sci. Adv. 3 (2017) e1602241",
    },
    "tc": {
        "what": "~2500 experimental Curie temperatures, curated",
        "why": "composition-only Tc regressor; screen Tc before computing exchange",
        "open": True,
        "auto": None,
        "browse": "https://arxiv.org/abs/1906.08534",
        "cite": "Nelson & Sanvito, Phys. Rev. Materials 3 (2019) 104405 "
                "(dataset in the paper's supplementary material)",
    },
    "nims": {
        "what": "curated experimental + computational Nd-Fe-B and 1-12 magnet data",
        "why": "best source of experimental validation targets for the 1-12 track",
        "open": False,
        "auto": None,
        "browse": "https://mdr.nims.go.jp/",
        "cite": "NIMS MatNavi / Materials Data Repository (registration required)",
    },
}


def fetch(name, dest):
    src = SOURCES[name]
    if not src["auto"]:
        print(f"{name}: no unauthenticated bulk endpoint.")
        print(f"  obtain from : {src['browse']}")
        print(f"  cite        : {src['cite']}")
        return
    os.makedirs(dest, exist_ok=True)
    req = urllib.request.Request(src["auto"], headers={"User-Agent": "magnet-screen/0.1"})
    meta = json.load(urllib.request.urlopen(req, context=CTX, timeout=90))
    for f in meta.get("files", []):
        url = f["links"]["self"]
        out = os.path.join(dest, f["key"])
        if os.path.exists(out) and os.path.getsize(out) == f["size"]:
            print(f"  have {f['key']} ({f['size']/1e6:.0f} MB)")
            continue
        print(f"  downloading {f['key']} ({f['size']/1e6:.0f} MB) ...")
        r = urllib.request.Request(url, headers={"User-Agent": "magnet-screen/0.1"})
        with urllib.request.urlopen(r, context=CTX, timeout=1800) as resp, open(out, "wb") as fh:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                fh.write(chunk)
        print(f"  wrote {out}")
    print(f"\ncite: {src['cite']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fetch", choices=list(SOURCES))
    ap.add_argument("--dest", default=os.path.join(os.path.dirname(__file__), "..", "external"))
    a = ap.parse_args()
    if a.fetch:
        fetch(a.fetch, os.path.abspath(a.dest))
        return
    print(f"{'source':<10}{'open':<7}{'auto':<7}what / why")
    for k, v in SOURCES.items():
        print(f"{k:<10}{'yes' if v['open'] else 'NO':<7}"
              f"{'yes' if v['auto'] else 'manual':<7}{v['what']}")
        print(f"{'':<24}-> {v['why']}")
    print("\nNot open, do not plan around: MPDS / Pauling File, Springer Materials.")


if __name__ == "__main__":
    main()
