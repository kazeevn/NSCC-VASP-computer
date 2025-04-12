import gzip
import pickle
from argparse import ArgumentParser
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from matbench_discovery.data import DataFiles
from jobflow import SETTINGS


def main():
    parser = ArgumentParser()
    parser.add_argument("run_name", type=str)
    parser.add_argument("--n-jobs", type=int, default=1)
    args = parser.parse_args()

    store = SETTINGS.JOB_STORE
    store.connect()
    result = store.query(
        {"metadata.run_name": args.run_name},
        properties=[
            "metadata",
            "output.entry",
            "output.structure"])
    
    entries = [ComputedEntry.from_dict(record['output']['entry']) for record in result]
    corrected_entries = MaterialsProject2020Compatibility().process_entries(
        entries, inplace=False, n_workers=args.n_jobs)
    structures = [record['output']['structure'] for record in result]
    index = [record['metadata']['material_id'] for record in result]
    with gzip.open(DataFiles.mp_patched_phase_diagram.mp_patched_phase_diagram.path, mode="rb") as zip_file:
        ppd_mp: PatchedPhaseDiagram = pickle.load(zip_file)
    e_hull_corrected = [ppd_mp.get_e_hull(entry) for entry in corrected_entries]
    data = pd.DataFrame(
        data={"structure": structures,
              "e_hull_corrected": e_hull_corrected},
        index=index
    )
    data.to_csv(f"{run_name}.csv.gz", index_name="material_id")
    

if __name__ == "__main__":
    main()