from contextlib import redirect_stdout
from argparse import ArgumentParser
from pathlib import Path
import io
import logging

import pandas as pd
from pymatgen.io.vasp.sets import MPRelaxSet
from pymatgen.core import Structure

logger = logging.getLogger(__name__)

# https://github.com/facebookresearch/flowmm/blob/6a96aec3b6eba89f6fa07436f0c8837979abb285/src/flowmm/pymatgen_.py#L68
def to_structure(structure: Structure | dict | str) -> Structure:
    with redirect_stdout(io.StringIO()):
        # CIF parser likes to print warnings
        if isinstance(structure, dict):
            return Structure.from_dict(structure)
        elif isinstance(structure, str):
            return Structure.from_str(structure, fmt="cif")
        return structure

# https://github.com/facebookresearch/flowmm/blob/6a96aec3b6eba89f6fa07436f0c8837979abb285/scripts_analysis/dft_create_inputs.py#L36
def write_vasp_directory(
    structure: Structure | dict | str,
    path: Path | str
) -> None:
    path = Path(path)
    structure = to_structure(structure)
    relax_set = MPRelaxSet(structure=structure)
    relax_set["INCAR"]["NCORE"] = 2
    relax_set.write_input(
        output_dir=str(path.resolve()),
        make_dir_if_not_present=True
    )


def main():
    parser = ArgumentParser()
    parser.add_argument("structures_cif", type=Path, help="cif.csv with structures")
    parser.add_argument("--mp-20", action="store_true", help="Use MP20 input format")
    parser.add_argument("output_path", type=Path, help="Path to write VASP inputs")
    args = parser.parse_args()
    if args.mp_20:
        structures = pd.read_csv(args.structures_cif, index_col="material_id", usecols=["material_id", "cif"])
    else:
        structures = pd.read_csv(args.structures_cif, index_col=0)
    structures = structures.squeeze("columns")
    args.output_path.mkdir()
    for index, structure in structures.items():
        try:
            write_vasp_directory(structure, args.output_path / str(index))
        except FileNotFoundError as e:
            logger.warning("Failed to write VASP input for %s: %s", index, e)


if __name__ == "__main__":
    main()