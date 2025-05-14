import gzip
import pickle
import json
import numpy as np  # Import numpy for np.nan

from functools import partial
from argparse import ArgumentParser
import pandas
from tqdm import tqdm
from pymatgen.analysis.phase_diagram import PatchedPhaseDiagram
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from matbench_discovery.data import DataFiles
from jobflow import SETTINGS

def is_exotic(entry: ComputedEntry) -> bool:
    return "Po" in entry.composition or "Rn" in entry.composition

def main():
    parser = ArgumentParser()
    parser.add_argument("run_name", type=str)
    parser.add_argument('--skip-potcar-check', action='store_true',
                        help="Skip the POTCAR check in MaterialsProject2020Compatibility")
    parser.add_argument('--initial-structure-count', type=int, help="Total number of submissions, "
                        "used to account for failed relaxations during stability check.")
    args = parser.parse_args()

    store = SETTINGS.JOB_STORE
    store.connect()
    result = tuple(store.query({
        "metadata.run_name": args.run_name,
        "name": "MP GGA static",
        'output.state': 'successful'},
        properties=[
            "metadata",
            "output.entry",
            "output.structure"
        ]))

    all_data = []
    non_exotic_entries = []
    non_exotic_indices = []

    print("Separating exotic and non-exotic entries...")
    for record in tqdm(result):
        entry = ComputedEntry.from_dict(record['output']['entry'])
        material_id = record['metadata']['material_id']
        structure = record['output']['structure']
        data_dict = {
            "material_id": material_id,
            "e_uncorrected": entry.uncorrected_energy,
            "structure": structure,
            "entry_dict": entry.as_dict(),  # Store as dict for now
            "e_corrected": np.nan,
            "e_above_hull_corrected": np.nan
        }
        if is_exotic(entry):
            all_data.append(data_dict)
        else:
            non_exotic_entries.append(entry)
            non_exotic_indices.append(len(all_data))  # Store index to update later
            all_data.append(data_dict)  # Add placeholder

    print(f"Processing {len(non_exotic_entries)} non-exotic entries...")
    if non_exotic_entries:
        MaterialsProject2020Compatibility(check_potcar=not args.skip_potcar_check).process_entries(
            non_exotic_entries, inplace=True, on_error="raise", verbose=True)

        with gzip.open(DataFiles.mp_patched_phase_diagram.path, mode="rb") as zip_file:
            ppd_mp: PatchedPhaseDiagram = pickle.load(zip_file)

        print("Computing e_above_hull for non-exotic entries...")
        get_e_hull = partial(ppd_mp.get_e_above_hull, allow_negative=True, check_stable=False)
        e_hull_corrected = list(map(get_e_hull, tqdm(non_exotic_entries)))

        print("Updating non-exotic entry data...")
        for i, entry_idx in enumerate(tqdm(non_exotic_indices)):
            entry = non_exotic_entries[i]
            all_data[entry_idx]["e_corrected"] = entry.energy
            all_data[entry_idx]["e_above_hull_corrected"] = e_hull_corrected[i]
            all_data[entry_idx]["entry_dict"] = entry.as_dict()  # Update with corrected entry

    print("Constructing final DataFrame...")
    # Convert entry dicts back to JSON strings for CSV storage
    for data_dict in all_data:
        data_dict["entry"] = json.dumps(data_dict.pop("entry_dict"))

    data = pandas.DataFrame(all_data)
    data = data.set_index("material_id")  # Set index after creation

    # Reorder columns if desired
    data = data[[
        "e_above_hull_corrected",
        "e_uncorrected",
        "e_corrected",
        "structure",
        "entry"
    ]]
    duplicates = data.index.duplicated(keep=False)
    if duplicates.any():
        print("Warning: Duplicate material IDs found. To preserve fairness, will keep the first occurrence.")
        for material_id in data.index[duplicates].unique():
            print(f"Duplicate material ID: {material_id}")
            print(data.loc[material_id, ["e_above_hull_corrected", "e_uncorrected"]])
        keep_first_duplicates = data.index.duplicated(keep="first")
        data = data[~keep_first_duplicates]
    print(f"Saving data to {args.run_name}.csv.gz")
    data.to_csv(f"{args.run_name}.csv.gz", index_label="material_id")
    print("Done.")
    if args.initial_structure_count is not None:        
        initial_structure_count = args.initial_structure_count
        print(f"Initial structure count: {initial_structure_count}")
        print(f"Final structure count: {len(data)}")
        print(f"Missing relaxations, considered as unsatable: {initial_structure_count - len(data)}")
    else:
        initial_structure_count = len(data)

    print("Warning: stability check consider exotic entries as unstable.")
    print(f"Stable {(data.e_above_hull_corrected < 0).sum() / initial_structure_count * 100:.2f}%")
    print(f"Metastable (0.1 eV) {(data.e_above_hull_corrected < 0.1).sum() / initial_structure_count * 100:.2f}%")

if __name__ == "__main__":
    main()