from pathlib import Path
from argparse import ArgumentParser
from atomate2.vasp.flows.mp import MPGGADoubleRelaxStaticMaker
from jobflow.managers.fireworks import flow_to_workflow
from fireworks import LaunchPad
from utils import load_cifs, to_structure

SCRATCH_ROOT = Path.home().resolve() / "scratch" / "dft_runs"
PROJECT_ROOT = Path(__file__).resolve().parent

def main():
    parser = ArgumentParser()
    parser.add_argument("structures", type=Path,
                        help="CSV with structures")
    parser.add_argument("run_name", type=str)
    parser.add_argument("--sample-n", type=int, help="Only compute N randomly sampled structures")
    parser.add_argument("--sampling-random-seed", type=int, default=42,
                        help="Random seed for sampling only")
    
    args = parser.parse_args()
    structures_str = load_cifs(args.structures)
    if args.sample_n:
        structures_str = structures_str.sample(
            args.sample_n, random_state=args.sampling_random_seed)
    
    lpad = LaunchPad.auto_load()

    def submit_structure(structure_id):
        structure = to_structure(structures_str[structure_id])
        flow = MPGGADoubleRelaxStaticMaker().make(structure=structure)
        flow.update_metadata({
            "material_id": structure_id,
            "run_name": args.run_name,
            "structure_source": args.structures})
        wf = flow_to_workflow(flow)
        lpad.add_wf(wf)

    for structure_id in structures_str.index:
        submit_structure(structure_id)


if __name__ == "__main__":
    main()
