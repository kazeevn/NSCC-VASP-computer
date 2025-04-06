from contextlib import redirect_stdout
from argparse import ArgumentParser
from pathlib import Path
import io

import pandas as pd
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.io.vasp.sets import MPRelaxSet
from pymatgen.io.cif import CifParser
from pymatgen.core import Structure

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
    path: Path | str,
    potcar_spec: bool = False,
) -> None:
    path = Path(path)
    structure = to_structure(structure)
    relax_set = MPRelaxSet(structure=structure)
    try:
        relax_set.write_input(
            output_dir=str(path.resolve()),
            make_dir_if_not_present=True,
            potcar_spec=potcar_spec,
        )
    except (TypeError, KeyError) as exp:
        print(f"{exp}")
    return None


def main():
    parser = ArgumentParser()
    parser.add_argument("structures_cif", type=Path, help="cif.csv with structures")
    parser.add_argument("output_path", type=Path, help="Path to write VASP inputs")
    args = parser.parse_args()
    structures = pd.read_csv(args.structures_cif, index_col=0).squeeze(axis="columns")    
    args.output_path.mkdir()
    write_vasp_directory(structures.iloc[2], args.output_path)


if __name__ == "__main__":
    main()