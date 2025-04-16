import gzip
import pickle
from argparse import ArgumentParser
import pandas
from pymatgen.analysis.phase_diagram import PatchedPhaseDiagram
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from matbench_discovery.data import DataFiles
from jobflow import SETTINGS


def main():
    parser = ArgumentParser()
    parser.add_argument("run_name", type=str)
    args = parser.parse_args()

    store = SETTINGS.JOB_STORE
    store.connect()
    result = tuple(store.query(
        {"metadata.run_name": args.run_name, "name": "MP GGA static"},
        properties=[
            "metadata",
            "output.entry",
            "output.structure"]))
    entries = [ComputedEntry.from_dict(record['output']['entry']) for record in result]
    MaterialsProject2020Compatibility(check_potcar=True, check_potcar_hash=False).process_entries(
        entries, inplace=True, on_error="raise", verbose=True)
    with gzip.open(DataFiles.mp_patched_phase_diagram.path, mode="rb") as zip_file:
        ppd_mp: PatchedPhaseDiagram = pickle.load(zip_file)
    print("Computing e_above_hull")
    e_hull_corrected = (ppd_mp.get_decomp_and_e_above_hull(entry, allow_negative=True)[1] for entry in entries)
    structures = (record['output']['structure'] for record in result)
    index = (record['metadata']['material_id'] for record in result)
    data = pandas.DataFrame(
        data={"structure": structures,
              "e_above_hull_corrected": e_hull_corrected,
              "e_uncorrected": (entry.uncorrected_energy for entry in entries),
              "entries": (entry.as_dict() for entry in entries)},
        index=index
    )
    data.to_csv(f"{args.run_name}.csv.gz", index_label="material_id")


if __name__ == "__main__":
    main()