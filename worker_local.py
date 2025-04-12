from argparse import ArgumentParser
from pathlib import Path
import logging
import os

import pandas as pd
from pymatgen.core import Structure

from atomate2.vasp.jobs.core import StaticMaker, RelaxMaker
from atomate2.vasp.flows.mp import MPGGADoubleRelaxStaticMaker
from atomate2.vasp.powerups import update_user_potcar_settings, update_user_potcar_functional
from jobflow import run_locally, Flow

from utils import load_cifs

logger = logging.getLogger(__file__)

# https://github.com/facebookresearch/flowmm/blob/6a96aec3b6eba89f6fa07436f0c8837979abb285/src/flowmm/pymatgen_.py#L68
def to_structure(structure: Structure | dict | str) -> Structure:
    # CIF parser likes to print warnings
    if isinstance(structure, dict):
        return Structure.from_dict(structure)
    elif isinstance(structure, str):
        return Structure.from_str(structure, fmt="cif")
    return structure


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
    target_structure = to_structure(cifs.at[args.structure_id])
    print(f"Will relax structure {args.structure_id}")
    flow = update_user_potcar_functional(
        MPGGADoubleRelaxStaticMaker().make(structure=target_structure),
        potcar_functional="PBE_54")
    flow.update_metadata({
        "material_id": args.structure_id,
        "run_name": args.run_name,
        "structure_source": args.structures_cif})
    run_locally(flow, create_folders=True, root_dir=args.job_folder)


if __name__ == "__main__":
    main()