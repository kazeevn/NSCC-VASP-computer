from typing import List
from enum import Enum
from pathlib import Path
import re
from time import sleep
from itertools import chain
from argparse import ArgumentParser
import pandas as pd
import numpy as np
import subprocess
from jobflow import SETTINGS
from utils import load_cifs

SCRATCH_ROOT = Path.home().resolve() / "scratch" / "dft_runs"
PROJECT_ROOT = Path(__file__).resolve().parent

def get_jobs(run_name: str, include_recently_finished: bool) -> List[str]:
    args = ['qstat']
    if include_recently_finished:
        args.append("-x")
    recent_jobs = subprocess.run(
        args,
        capture_output=True,
        check=True
    )
    structure_id_re = re.compile(fr"{run_name}-(\w+)")
    return structure_id_re.findall(recent_jobs.stdout.decode("utf-8"))

def get_jobs_in_folder(run_name: str, run_pbs_folder: Path) -> List[str]:
    structure_id_re = re.compile(fr"{run_name}-(\w+)")
    all_files = run_pbs_folder.glob(fr'**/{run_name}-*')
    return (structure_id_re.match(file.stem).groups(0)[0] for file in all_files)


class Exclusion(Enum):
    db = "db"
    files = "files"
    running_jobs = "running_jobs"
    recent_jobs = "recent_jobs"

    def __str__(self):
        return self.value


def main():
    parser = ArgumentParser()
    parser.add_argument("structures", type=Path,
                        help="CSV with structures")
    parser.add_argument("run_name", type=str)
    parser.add_argument("--sample-n", type=int, help="Only compute N randomly sampled structures")
    parser.add_argument("--sampling-random-seed", type=int, default=42,
                        help="Random seed for sampling only")
    parser.add_argument("--resume", action="store_true",
                        help="Resume submitting an existing run")
    parser.add_argument("--retry-minutes", type=float,
                        help="Retry submitting every X minutes")
    parser.add_argument("-e", "--exclude", nargs="+", type=Exclusion,
                        choices=tuple(Exclusion),
                        help="Don't resubmit structures that have jobs in those sources")
    parser.add_argument("-l", type=str, default="select=1:ncpus=64:mem=128gb:mpiprocs=64:ompthreads=1",
                        dest="resource_list",
                        help="qsub resource list aka -l")
    args = parser.parse_args()
    if Exclusion.running_jobs in args.exclude and Exclusion.recent_jobs in args.exclude:
        print(f"Specifying both {Exclusion.running_jobs} and {Exclusion.recent_jobs} has no effect"
               "as the latter includes the former.")
    index = load_cifs(args.structures).index
    if args.sample_n:
        rng = np.random.default_rng(seed=args.sampling_random_seed)
        index = rng.choice(index, args.sample_n, replace=False)
    run_root = SCRATCH_ROOT / args.run_name
    pbs_root = run_root.joinpath("PBS")

    if not args.resume:
        run_root.mkdir(exist_ok=False)
        pbs_root.mkdir(exist_ok=False)
    
    def get_excluded_structures():
        exclusions = []
        if Exclusion.db in args.exclude:
            store = SETTINGS.JOB_STORE
            store.connect()
            db_jobs = frozenset(map(
                lambda record: index.dtype.type(record['metadata']['material_id']),
                store.query({
                    "metadata.run_name": args.run_name,
                    "name": "MP GGA static",
                    "output.state": "successful"},
                    properties=["metadata.material_id"])))
            if len(db_jobs) == 0:
                raise RuntimeError("No jobs in DB, check connection")
            exclusions.append(db_jobs)
        if Exclusion.running_jobs in args.exclude or Exclusion.recent_jobs in args.exclude:
            exclusions.append(get_jobs(args.run_name, include_recently_finished=Exclusion.recent_jobs in args.exclude))
        if Exclusion.files in args.exclude:
            exclusions.append(get_jobs_in_folder(args.run_name, pbs_root))
        return frozenset(map(index.dtype.type, chain(*exclusions)))
        
    def submit_structure(structure_id):
        return subprocess.run(
            ["qsub", "-v", f"SCRATCH_ROOT={SCRATCH_ROOT}, RUN_NAME={args.run_name}, "
            f"PROJECT_ROOT={PROJECT_ROOT}, STRUCTURE_ID={structure_id}, "
            f"STRUCTURES={args.structures.resolve()}",
            "-l", args.resource_list,
            "-N", f"{args.run_name}-{structure_id}",
            str(PROJECT_ROOT / "atomate_vasp_single.sh")],
            cwd=pbs_root, check=True)

    def submit_missing(present_jobs):
        for structure_id in index:
            if structure_id in present_jobs:
                continue
            submit_structure(structure_id)

    all_jobs = get_excluded_structures()
    if args.retry_minutes:
        while len(all_jobs) < len(index):
            try:
                submit_missing(all_jobs)
            except subprocess.CalledProcessError as e:
                print("qusub error:")
                print(e)
                print(f"Will retry in {args.retry_minutes} minutes")
            sleep(60 * args.retry_minutes)
            all_jobs = get_excluded_structures()
    else:
        submit_missing(all_jobs)


if __name__ == "__main__":
    main()
