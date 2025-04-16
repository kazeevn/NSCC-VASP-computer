from typing import List
from pathlib import Path
import re
from time import sleep
from itertools import chain
from argparse import ArgumentParser
import pandas as pd
import numpy as np
import subprocess

from utils import load_cifs

SCRATCH_ROOT = Path.home().resolve() / "scratch" / "dft_runs"
PROJECT_ROOT = Path(__file__).resolve().parent

def get_submitted_jobs(run_name: str) -> List[str]:
    recent_jobs = subprocess.run(
        ['qstat', '-x'],
        capture_output=True,
        check=True
    )
    structure_id_re = re.compile(fr"{run_name}-(\w+)")
    return structure_id_re.findall(recent_jobs.stdout.decode("utf-8"))

def get_jobs_in_folder(run_name: str, run_folder: Path) -> List[str]:
    structure_id_re = re.compile(fr"{run_name}-(\w+)")
    all_files = run_folder.glob(fr'**/{run_name}-*')
    return (structure_id_re.match(file.stem).groups(0)[0] for file in all_files)


def main():
    parser = ArgumentParser()
    parser.add_argument("structures", type=Path,
                        help="CSV with structures")
    parser.add_argument("run_name", type=str)
    parser.add_argument("--sample-n", type=int, help="Only compute N randomly sampled structures")
    parser.add_argument("--sampling-random-seed", type=int, default=42,
                        help="Random seed for sampling only")
    parser.add_argument("--resume", action="store_true",
                        help="Submit the structures that have no jobs")
    parser.add_argument("--retry-minutes", type=int,
                        help="Retry submitting every X minutes")
    args = parser.parse_args()
    index = load_cifs(args.structures).index
    if args.sample_n:
        rng = np.random.default_rng(seed=args.sampling_random_seed)
        index = rng.choice(index, args.sample_n, replace=False)
    run_root = SCRATCH_ROOT / args.run_name
    pbs_root = run_root.joinpath("PBS")

    if not args.resume:
        run_root.mkdir(exist_ok=False)
        pbs_root.mkdir(exist_ok=False)
    
    def get_all_jobs():
        pbs_jobs = get_submitted_jobs(args.run_name)
        folder_jobs = get_jobs_in_folder(args.run_name, run_root)
        return frozenset(map(index.dtype.type, chain(pbs_jobs, folder_jobs)))
    
    if args.resume:
        all_jobs = get_all_jobs()
    else:
        all_jobs = frozenset()
    
    def submit_structure(structure_id):
        return subprocess.run(
            ["qsub", "-v", f"SCRATCH_ROOT={SCRATCH_ROOT}, RUN_NAME={args.run_name}, "
            f"PROJECT_ROOT={PROJECT_ROOT}, STRUCTURE_ID={structure_id}, "
            f"STRUCTURES={args.structures.resolve()}",
            "-N", f"{args.run_name}-{structure_id}",
            str(PROJECT_ROOT / "atomate_vasp_single.sh")],
            cwd=pbs_root, check=True)

    def submit_missing(present_jobs):
        for structure_id in index:
            if structure_id in present_jobs:
                continue
            submit_structure(structure_id)

    if args.retry_minutes:
        while len(all_jobs) < len(index):
            all_jobs = get_all_jobs()
            try:
                submit_missing(all_jobs)
            except subprocess.CalledProcessError as e:
                print("qusub error:")
                print(e)
                print("Will retry")
            sleep(60*args.retry_minutes)
    else:
        submit_missing(all_jobs)
        

if __name__ == "__main__":
    main()
