from argparse import ArgumentParser
from pathlib import Path
import logging

from pymatgen.core import Structure

from atomate2.vasp.flows.mp import MPGGADoubleRelaxStaticMaker
from jobflow import run_locally

from utils import load_cifs

logger = logging.getLogger(__file__)

# https://github.com/facebookresearch/flowmm/blob/6a96aec3b6eba89f6fa07436f0c8837979abb285/src/flowmm/pymatgen_.py#L68
def to_structure(structure: Structure | dict | str) -> Structure:
    # CIF parser likes to print warnings
    if isinstance(structure, dict):
        return Structure.from_dict(structure)
    elif isinstance(structure, str):
        return Structure.from_str(structure, fmt="cif")
    elif isinstance(structure, Structure):
        return structure
    else:
        raise ValueError("Unknown structure format!")


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