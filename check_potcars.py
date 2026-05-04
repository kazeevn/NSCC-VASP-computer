import warnings
import numpy as np
from pathlib import Path
from pymatgen.io.vasp.inputs import PotcarSingle, UnknownPotcarWarning

POTCAR_ROOT = Path("/home/project/11001786/Crys-JEPA-VASP/VASP_pseudopotentials")
STATS = ["MEAN", "ABSMEAN", "VAR", "MIN", "MAX"]
TOL = 1e-6

def get_db_entries(ps: PotcarSingle) -> list[dict]:
    """Return all DB entries matching this POTCAR's TITEL+VRHFIN."""
    titel = ps.TITEL.replace(" ", "")
    vrhfin = ps.VRHFIN.replace(" ", "")
    matches = []
    for func in ps.functional_dir:
        for titel_no_spc, subvariants in ps._potcar_summary_stats[func].items():
            if titel == titel_no_spc:
                for sv in subvariants:
                    if vrhfin == sv["VRHFIN"]:
                        matches.append({"func": func, **sv})
    return matches

def compare(ps: PotcarSingle, ref: dict) -> dict:
    """Compare a loaded POTCAR against one DB reference entry.
    Returns a dict with keyword diffs and max stat diffs per section."""
    result = {}
    for section in ("header", "data"):
        got = set(ps._summary_stats["keywords"][section])
        expected = set(ref["keywords"][section])
        result[f"kw_{section}_only_in_file"] = sorted(got - expected)
        result[f"kw_{section}_only_in_db"]   = sorted(expected - got)
        diffs = {
            stat: abs(ref["stats"][section][stat] - ps._summary_stats["stats"][section][stat])
            for stat in STATS
        }
        result[f"stats_{section}_maxdiff"] = max(diffs.values())
        result[f"stats_{section}_diffs"] = diffs
    return result

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    potcar_dir = POTCAR_ROOT / "POT_GGA_PAW_PBE"
    for f in sorted(potcar_dir.glob("POTCAR.*.gz")):
        ps = PotcarSingle.from_file(f)
        if ps.is_valid:
            continue
        entries = get_db_entries(ps)
        sym = f.name.removeprefix("POTCAR.").removesuffix(".gz")
        if not entries:
            print(f"\n{sym}: NO DB REFERENCE (TITEL={ps.TITEL.strip()!r}, VRHFIN={ps.VRHFIN.strip()!r})")
            continue

        # Pick the closest DB entry by total stat distance
        best = min(entries, key=lambda e: sum(
            abs(e["stats"][sec][stat] - ps._summary_stats["stats"][sec][stat])
            for sec in ("header", "data") for stat in STATS
        ))
        cmp = compare(ps, best)

        kw_same = (not cmp["kw_header_only_in_file"] and not cmp["kw_header_only_in_db"]
                   and not cmp["kw_data_only_in_file"] and not cmp["kw_data_only_in_db"])
        hdr_ok  = cmp["stats_header_maxdiff"] < TOL
        data_ok = cmp["stats_data_maxdiff"] < TOL

        verdict = []
        if not kw_same:    verdict.append("keyword diff")
        if not hdr_ok:     verdict.append(f"header stats diff (max {cmp['stats_header_maxdiff']:.3e})")
        if not data_ok:    verdict.append(f"DATA stats diff (max {cmp['stats_data_maxdiff']:.3e})")
        print(f"\n{sym} [best match: {best['func']}]  →  {', '.join(verdict)}")

        if not kw_same:
            for section in ("header", "data"):
                extra = cmp[f"kw_{section}_only_in_file"]
                missing = cmp[f"kw_{section}_only_in_db"]
                if extra:   print(f"  [{section}] only in file : {extra}")
                if missing: print(f"  [{section}] only in DB   : {missing}")

        if not hdr_ok or not data_ok:
            for section in ("header", "data"):
                max_d = cmp[f"stats_{section}_maxdiff"]
                if max_d >= TOL:
                    worst_stat = max(cmp[f"stats_{section}_diffs"], key=lambda s: cmp[f"stats_{section}_diffs"][s])
                    print(f"  [{section}] worst stat: {worst_stat}  diff={cmp[f'stats_{section}_diffs'][worst_stat]:.6e}")
