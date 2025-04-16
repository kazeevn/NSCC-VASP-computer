from pathlib import Path
import pandas as pd

def load_cifs(file: Path) -> pd.Series:
    structures_df = pd.read_csv(file)
    if "material_id" in structures_df.columns:
        structures_df.set_index("material_id", inplace=True, append=False)
    else:
        structures_df.set_index(structures_df.columns[0], inplace=True, append=False)
    return structures_df.cif