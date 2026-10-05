#!/usr/bin/env python3
"""How much Gd must be replaced by an anisotropic rare earth to make a magnet?

The Gd campaign answers the EXCHANGE question (sign and strength of RE-TM
coupling) but is silent on anisotropy: Gd is a 4f7 S-state ion, L = 0, so it
contributes no single-ion anisotropy by construction. A real magnet needs a
non-spherical 4f ion (Tb, Dy, Ho on one side; Er, Tm on the other) on that site.

This turns the campaign output into the substitution fraction x:

  1. exchange field on the RE, taken from the campaign's own dE per Gd
  2. K1(x, T) from second-order crystal field + Stevens coefficients,
     with the Callen-Callen l=2 temperature law
  3. Ms(x) from the Fe sublattice moment and the RE moments
  4. the smallest x meeting Coey's hardness criterion kappa >= 1

kappa = sqrt(K1 / (mu0 Ms^2)) >= 1 is what separates a permanent magnet from a
merely magnetic material: it is the condition for coercivity to reach Ms/2 and
so for the full energy product to be attainable.

The only input NOT already produced by the campaign is A20, the second-order
crystal-field parameter at the RE site (K/a0^2). See README for how to get it.

Usage
  python3 anisotropy.py --scan --a20 -300            # all RE, one structure
  python3 anisotropy.py --re Tb --a20 -300 --de 277 --m-fe 14.06 \
                        --volume 90.1 --n-re 1 --temp 450
"""
import argparse
import math

KB = 1.380649e-23          # J/K
MU0 = 4 * math.pi * 1e-7   # H/m
MUB = 9.2740100783e-24     # J/T

# J, g_J, Stevens alpha_J, <r^2> in a0^2, de Gennes (g_J-1)^2 J(J+1)
# alpha_J from Hutchings; <r^2> from Freeman-Desclaux.
RE = {
    #        J      g_J      alpha_J      <r^2>   deGennes  4f^n
    "Nd": (4.5,  8 / 11,  -0.0064280,    1.001,    1.84,   3),
    "Sm": (2.5,  2 / 7,   +0.0412700,    0.883,    4.46,   5),
    "Gd": (3.5,  2.0,      0.0000000,    0.785,   15.75,   7),
    "Tb": (6.0,  1.5,     -0.0101010,    0.756,   10.50,   8),
    "Dy": (7.5,  4 / 3,   -0.0063492,    0.726,    7.08,   9),
    "Ho": (8.0,  1.25,    -0.0022222,    0.696,    4.50,  10),
    "Er": (7.5,  1.2,     +0.0025397,    0.666,    2.55,  11),
    "Tm": (6.0,  7 / 6,   +0.0101010,    0.640,    1.17,  12),
}
HEAVY = ["Gd", "Tb", "Dy", "Ho", "Er", "Tm"]
LIGHT = ["Nd", "Sm"]          # J = |L - S|: total moment parallel to the TM


def spin_projection(el):
    """(g_J - 1) J  -- the spin part of J, which is what the exchange couples to."""
    J, gJ = RE[el][0], RE[el][1]
    return (gJ - 1) * J


def moment(el):
    """g_J J, the free-ion total moment in mu_B."""
    J, gJ = RE[el][0], RE[el][1]
    return gJ * J


def brillouin(J, x):
    if x <= 1e-9:
        return 0.0
    a = (2 * J + 1) / (2 * J)
    b = 1 / (2 * J)
    return a / math.tanh(a * x) - b / math.tanh(b * x)


def k1_re_zeroT(el, a20, n_re_per_m3):
    """Second-order single-ion anisotropy at T = 0, in J/m^3.

    K1 = -(3/2) n alpha_J <r^2> A20 J(J - 1/2),  with A20 in K/a0^2 so the
    bracket is an energy in kelvin per ion.
    """
    J, _, alpha, r2, _, _ = RE[el]
    per_ion_K = -1.5 * alpha * r2 * a20 * J * (J - 0.5)
    return per_ion_K * KB * n_re_per_m3


def re_sublattice_m(el, de_meV_per_gd, T):
    """Reduced RE sublattice magnetisation in the TM exchange field.

    The campaign's |dE| per Gd is the energy to flip the Gd moment, i.e. twice
    the exchange energy of one Gd ion. Rescale to another RE by the spin
    projection (g_J - 1)J, then evaluate the Brillouin function.
    """
    e_ex_gd = abs(de_meV_per_gd) * 1.602176634e-22 / 2.0        # J per Gd ion
    # (g_J - 1)J is NEGATIVE for the light RE, because their total moment opposes
    # the spin. That sign says which way the moment points, not how strong the
    # coupling is - the exchange ENERGY scales with its magnitude. Using the
    # signed value drives the Brillouin argument negative and silently zeroes the
    # light-RE sublattice, which would erase exactly the anisotropy Sm is for.
    e_ex = e_ex_gd * abs(spin_projection(el)) / abs(spin_projection("Gd"))
    if T <= 0:
        return 1.0
    return brillouin(RE[el][0], e_ex / (KB * T))


def evaluate(el, x, a20, de, m_fe, volume_A3, n_re, T, fm_coupled):
    """Return (K1, mu0Ms, kappa) for substitution fraction x at temperature T."""
    vol_m3 = volume_A3 * 1e-30
    n_site = n_re / vol_m3                       # RE sites per m^3

    # anisotropy: only the substituted fraction contributes (Gd contributes 0)
    m_re = re_sublattice_m(el, de, T)
    k1 = x * k1_re_zeroT(el, a20, n_site) * m_re ** 3

    # magnetisation: Fe sublattice plus RE, sign set by the coupling
    m_gd = moment("Gd") * re_sublattice_m("Gd", de, T)
    m_sub = moment(el) * m_re
    re_total = n_re * ((1 - x) * m_gd + x * m_sub)
    net_muB = m_fe + re_total if fm_coupled else m_fe - re_total
    Ms = abs(net_muB) * MUB / vol_m3             # A/m
    mu0Ms = MU0 * Ms
    kappa = math.sqrt(abs(k1) / (MU0 * Ms ** 2)) if Ms > 0 else float("inf")
    return k1, mu0Ms, kappa


def min_x(el, **kw):
    """Smallest x reaching the target kappa WITH easy-axis anisotropy.

    K1 < 0 is easy-plane: the moments lie in a plane and there is no stable
    uniaxial direction to pin a domain wall against, so it cannot make a
    permanent magnet no matter how large |K1| is. Requiring K1 > 0 here is what
    keeps the wrong Stevens-sign family from looking like a solution.
    """
    target = kw.pop("target_kappa")
    for i in range(1, 1001):
        x = i / 1000
        k1, mu0Ms, kappa = evaluate(el, x, **kw)
        if k1 > 0 and kappa >= target:
            return x, k1, mu0Ms, kappa
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--re", default="Tb", choices=list(RE), help="substituent")
    p.add_argument("--a20", type=float, required=True,
                   help="2nd-order crystal-field parameter at the RE site, K/a0^2")
    p.add_argument("--de", type=float, default=277.0,
                   help="|dE| per Gd from the campaign, meV (sets the exchange field)")
    p.add_argument("--m-fe", type=float, default=14.06,
                   help="TM sublattice moment per cell, mu_B")
    p.add_argument("--volume", type=float, default=90.1, help="cell volume, A^3")
    p.add_argument("--n-re", type=int, default=1, help="RE sites per cell")
    p.add_argument("--temp", type=float, default=450.0, help="operating temperature, K")
    p.add_argument("--target-kappa", type=float, default=1.0)
    p.add_argument("--ferri", action="store_true",
                   help="host is ferrimagnetic (default assumes the FM-coupled case)")
    p.add_argument("--scan", action="store_true", help="compare every heavy RE")
    p.add_argument("--light", action="store_true",
                   help="include the light RE (Nd, Sm), whose moment ADDS to the TM")
    a = p.parse_args()

    kw = dict(a20=a.a20, de=a.de, m_fe=a.m_fe, volume_A3=a.volume,
              n_re=a.n_re, T=a.temp, fm_coupled=not a.ferri)

    print(f"# host: {'FM-coupled' if not a.ferri else 'ferrimagnetic'}   "
          f"|dE|/Gd = {a.de:.0f} meV   M_TM = {a.m_fe:.2f} muB   "
          f"V = {a.volume:.1f} A^3   n_RE = {a.n_re}")
    print(f"# A20 = {a.a20:+.0f} K/a0^2   T = {a.temp:.0f} K   "
          f"target kappa = {a.target_kappa}\n")

    # Which RE are uniaxial here? sign(K1) must be positive for easy-axis.
    sign_ref = k1_re_zeroT("Tb", a.a20, 1.0)
    print(f"{'RE':<4}{'alpha_J':>10}{'easy axis?':>12}{'m_RE(T)':>9}"
          f"{'x_min':>8}{'K1 (MJ/m3)':>12}{'mu0Ms (T)':>11}{'kappa':>8}")
    todo = (HEAVY + (LIGHT if a.light else [])) if a.scan else [a.re]
    for el in todo:
        if el == "Gd":
            print(f"{el:<4}{0.0:>10.4f}{'no (L=0)':>12}{'-':>9}{'-':>8}"
                  f"{'0.00':>12}{'-':>11}{'-':>8}")
            continue
        uni = "yes" if k1_re_zeroT(el, a.a20, 1.0) > 0 else "no (planar)"
        m_re = re_sublattice_m(el, a.de, a.temp)
        r = min_x(el, target_kappa=a.target_kappa, **kw)
        if r is None:
            k1, mu0Ms, kappa = evaluate(el, 1.0, **kw)
            why = "planar" if k1 < 0 else "none"
            print(f"{el:<4}{RE[el][2]:>+10.4f}{uni:>12}{m_re:>9.2f}"
                  f"{why:>8}{k1/1e6:>12.2f}{mu0Ms:>11.2f}{kappa:>8.2f}")
        else:
            x, k1, mu0Ms, kappa = r
            print(f"{el:<4}{RE[el][2]:>+10.4f}{uni:>12}{m_re:>9.2f}"
                  f"{x:>8.2f}{k1/1e6:>12.2f}{mu0Ms:>11.2f}{kappa:>8.2f}")

    print("\nx_min = smallest substituted fraction reaching the target kappa;"
          " 'none' = unreachable even at x = 1.")
    print("Only one Stevens sign family is easy-axis for a given A20 - mixing"
          " the two cancels the anisotropy.")
    print("Gd is kept on the remaining sites because it carries the largest de"
          " Gennes factor (15.75) and so the highest Tc contribution.")


if __name__ == "__main__":
    main()
