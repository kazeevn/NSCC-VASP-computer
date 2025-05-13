from argparse import ArgumentParser
from pathlib import Path
import logging

from atomate2.vasp.flows.mp import MPGGADoubleRelaxStaticMaker
from jobflow import run_locally

from utils import load_cifs, to_structure

logger = logging.getLogger(__file__)


def main():
    parser = ArgumentParser()
    parser.add_argument("structures_cif", type=Path, help="cif.csv with structures")
    parser.add_argument("--structure-id", type=str, required=True,
                        help="Structure ID (index in the csv) to run on")
    parser.add_argument("--job-folder", type=Path, required=True,
                        help="Folder where to store job outputs")
    parser.add_argument("--run-name", type=str, default="",
                        help="Name of the run to be propagated into jobs")
    args = parser.parse_args()
    cifs = load_cifs(args.structures_cif)
    target_structure = to_structure(cifs.at[cifs.index.dtype.type(args.structure_id)])
    print(f"Will relax structure {args.structure_id}")
    flow = MPGGADoubleRelaxStaticMaker().make(structure=target_structure)
    flow.update_metadata({
        "material_id": args.structure_id,
        "run_name": args.run_name,
        "structure_source": args.structures_cif})
    run_locally(flow, create_folders=True, root_dir=args.job_folder)


if __name__ == "__main__":
    main()