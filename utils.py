from pathlib import Path
import pandas as pd
from pymatgen.core import Structure

def load_cifs(file: Path) -> pd.Series:
    structures_df = pd.read_csv(file)
    if "material_id" in structures_df.columns:
        structures_df.set_index("material_id", inplace=True, append=False)
    else:
        structures_df.set_index(structures_df.columns[0], inplace=True, append=False)
    return structures_df.cif

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