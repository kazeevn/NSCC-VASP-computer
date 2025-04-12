from pathlib import Path
from argparse import ArgumentParser
import pandas as pd
import numpy as np
import subprocess

from utils import load_cifs

SCRATCH_ROOT = Path.home().resolve() / "scratch" / "dft_runs"
PROJECT_ROOT = Path(__file__).resolve().parent

def main():
    parser = ArgumentParser()
    parser.add_argument("structures", type=Path,
                        help="CSV with structures")
    parser.add_argument("run_name", type=str)
    parser.add_argument("--sample-n", type=int, help="Only compute first N structures")
    parser.add_argument("--sampling-random-seed", type=int, default=42,
                        help="Random seed for sampling only")
    args = parser.parse_args()
    index = load_cifs(args.structures).index
    if args.sample_n:
        rng = np.random.default_rng(seed=args.sampling_random_seed)
        index = rng.choice(index, args.sample_n, replace=False)
    run_root = SCRATCH_ROOT / args.run_name
    run_root.mkdir(exist_ok=False)
    pbs_root = run_root.joinpath("PBS")
    pbs_root.mkdir()
    for structure_id in index:
        subprocess.run(
            ["qsub", "-v", f"SCRATCH_ROOT={SCRATCH_ROOT}, RUN_NAME={args.run_name}, "
            f"PROJECT_ROOT={PROJECT_ROOT}, STRUCTURE_ID={structure_id}, "
            f"STRUCTURES={args.structures.resolve()}",
            "-N", f"{args.run_name}-{structure_id}",
            str(PROJECT_ROOT / "atomate_vasp_single.sh")],
            cwd=pbs_root, check=True)

if __name__ == "__main__":
    main()
