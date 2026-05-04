import gzip
import pickle
import json
import numpy as np  # Import numpy for np.nan
from warnings import warn
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

def process_run(run_name, result, args, ppd_mp=None):
    all_data = []
    non_exotic_entries = []
    non_exotic_indices = []
    has_exotic_entries = False

    print("Separating exotic and non-exotic entries...")
    for record in tqdm(result):
        entry = ComputedEntry.from_dict(record['output']['entry'])
        material_id = record['metadata']['material_id']
        structure = record['output']['structure']
        data_dict = {
            "material_id": material_id,
            "e_uncorrected": entry.uncorrected_energy,
            "structure": json.dumps(structure),
            "entry_dict": entry.as_dict(),
            "e_corrected": np.nan,
            "e_above_hull_corrected": np.nan
        }
        if is_exotic(entry):
            has_exotic_entries = True
        else:
            non_exotic_entries.append(entry)
            non_exotic_indices.append(len(all_data))  # Store index to update later
        all_data.append(data_dict)

    print(f"Processing {len(non_exotic_entries)} non-exotic entries...")
    if non_exotic_entries:
        MaterialsProject2020Compatibility(check_potcar=not args.skip_potcar_check).process_entries(
            non_exotic_entries, inplace=True, on_error="raise", verbose=True)

        if not args.skip_ehull:
            print("Computing e_above_hull for non-exotic entries...")
            get_e_hull = partial(ppd_mp.get_e_above_hull, allow_negative=True, check_stable=False)
            e_hull_corrected = list(map(get_e_hull, tqdm(non_exotic_entries)))
        else:
            e_hull_corrected = [np.nan] * len(non_exotic_entries)

        print("Updating non-exotic entry data...")
        for i, entry_idx in enumerate(tqdm(non_exotic_indices)):
            entry = non_exotic_entries[i]
            all_data[entry_idx]["e_corrected"] = entry.energy
            all_data[entry_idx]["e_above_hull_corrected"] = e_hull_corrected[i]
            all_data[entry_idx]["entry_dict"] = entry.as_dict()

    print("Constructing the final DataFrame...")
    # Convert entry dicts back to JSON strings for CSV storage
    for data_dict in all_data:
        data_dict["entry"] = json.dumps(data_dict.pop("entry_dict"))

    data = pandas.DataFrame(all_data)
    data.set_index("material_id", inplace=True)
    if data.index.map(type).nunique() > 1:
        warn("Index has multiple types, check DB!")

    data = data[[
        "e_above_hull_corrected",
        "e_uncorrected",
        "e_corrected",
        "structure",
        "entry"
    ]]
    duplicates = data.index.duplicated(keep=False)
    if duplicates.any():
        warn("Duplicate material IDs found. To preserve fairness, will keep the first occurrence.")
        for material_id in data.index[duplicates].unique():
            print(f"Duplicate material ID: {material_id}")
            print(data.loc[material_id, ["e_above_hull_corrected", "e_uncorrected"]])
        keep_first_duplicates = data.index.duplicated(keep="first")
        data = data.loc[~keep_first_duplicates]
    file_name = f"{run_name}-{args.atomate_job_name}.csv.gz"
    print(f"Saving {len(data)} entries to {file_name}")
    data.to_csv(file_name, index_label="material_id")
    print("Done")
    if args.initial_structure_count is not None:
        initial_structure_count = args.initial_structure_count
        print(f"Initial structure count: {initial_structure_count}")
        print(f"Final structure count: {len(data)}")
        print(f"Missing relaxations, considered as unsatable: {initial_structure_count - len(data)}")
    else:
        initial_structure_count = len(data)

    if not args.skip_ehull:
        if has_exotic_entries:
            warn("Stability check considers exotic entries as unstable.")
        print(f"Stable {(data.e_above_hull_corrected < 0).sum() / initial_structure_count * 100:.2f}%")
        print(f"Metastable ({args.metastable_threshold}) "
              f"{(data.e_above_hull_corrected < args.metastable_threshold).sum() / initial_structure_count * 100:.2f}%")


def main():
    parser = ArgumentParser()
    parser.add_argument("--run-names", nargs="*", default=None,
                        help="Run name(s) to process. If not specified, all runs are processed.")
    parser.add_argument('--skip-potcar-check', action='store_true',
                        help="Skip the POTCAR check in MaterialsProject2020Compatibility")
    parser.add_argument('--skip-ehull', action='store_true',
                        help="Skip computing e_above_hull (e.g. for faster exports without stability info)")
    parser.add_argument('--initial-structure-count', type=int, help="Total number of submissions, "
                        "used to account for failed relaxations during stability check.")
    parser.add_argument('--metastable-threshold', type=float, default=0.1,
                        help="Threshold for metastability in eV.")
    parser.add_argument("--atomate-job-name", type=str, default="MP GGA static",
                        help="Job name in atomate2. For MP-compatiable relaxations, they are "
                        "'MP GGA relax 1', 'MP GGA relax 2', and 'MP GGA static'")
    args = parser.parse_args()

    print(f'Getting data for job name="{args.atomate_job_name}"')
    store = SETTINGS.JOB_STORE
    store.connect()

    if args.run_names is None:
        print("No run names specified, discovering all runs...")
        run_names = sorted(store.docs_store.distinct(
            "metadata.run_name",
            {"name": args.atomate_job_name, "output.state": "successful"},
        ))
        print(f"Found {len(run_names)} run(s): {run_names}")
    else:
        run_names = args.run_names

    if args.skip_ehull:
        ppd_mp = None
    else:
        print("Loading phase diagram...")
        with gzip.open(DataFiles.mp_patched_phase_diagram.path, mode="rb") as zip_file:
            ppd_mp: PatchedPhaseDiagram = pickle.load(zip_file)

    for run_name in run_names:
        print(f"\n=== Processing run: {run_name} ===")
        result = tuple(store.query({
            "metadata.run_name": run_name,
            "name": args.atomate_job_name,
            "output.state": "successful"},
            properties=[
                "metadata",
                "output.entry",
                "output.structure"
            ]))
        process_run(run_name, result, args, ppd_mp)

if __name__ == "__main__":
    main()