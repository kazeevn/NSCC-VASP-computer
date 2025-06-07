from pathlib import Path
from argparse import ArgumentParser
from atomate2.vasp.flows.mp import MPGGADoubleRelaxStaticMaker, MPGGADoubleRelaxMaker
from atomate2.vasp.jobs.mp import MPGGARelaxMaker, MPGGAStaticMaker
from jobflow.managers.fireworks import flow_to_workflow
from fireworks import LaunchPad
from fireworks.fw_config import QUEUEADAPTER_LOC
from fireworks.utilities.fw_serializers import load_object_from_file
from utils import load_structures

SCRATCH_ROOT = Path.home().resolve() / "scratch" / "dft_runs"
PROJECT_ROOT = Path(__file__).resolve().parent

def main():
    parser = ArgumentParser()
    parser.add_argument("structures", type=Path,
                        help="CSV with structures")
    parser.add_argument("--format", type=str, default="cif",
                        help="structure format passed to Structure.from_str; "
                        "also serves as the column name in the CSV")
    parser.add_argument("run_name", type=str)
    parser.add_argument("--sample-n", type=int, help="Only compute N randomly sampled structures")
    parser.add_argument("--sampling-random-seed", type=int, default=42,
                        help="Random seed for sampling only")
    
    args = parser.parse_args()
    structures = load_structures(args.structures, args.format)
    if args.sample_n:
        structures = structures.sample(
            args.sample_n, random_state=args.sampling_random_seed)
    
    lpad = LaunchPad.auto_load()
    walltime_str = load_object_from_file(QUEUEADAPTER_LOC).get("walltime")
    print("Assuming that the current default FireWorks config will be used "
          f"to execute the job; setting walltime to {walltime_str}")
    h, m, s = map(int, walltime_str.split(":"))
    walltime_seconds = h * 3600 + m * 60 + s
    run_vasp_kwargs={"wall_time": walltime_seconds, "vasp_job_kwargs": {"auto_continue": True}}

    default_MPGGADoubleRelaxMaker = MPGGADoubleRelaxMaker()
    double_realax_maker = MPGGADoubleRelaxMaker(
        relax_maker1 = MPGGARelaxMaker(run_vasp_kwargs=run_vasp_kwargs),
        relax_maker2 = MPGGARelaxMaker(run_vasp_kwargs=run_vasp_kwargs, 
            copy_vasp_kwargs=default_MPGGADoubleRelaxMaker.relax_maker2.copy_vasp_kwargs))

    default_MPGGADoubleRelaxStaticMaker = MPGGADoubleRelaxStaticMaker()
    double_maker = MPGGADoubleRelaxStaticMaker(
        relax_maker=double_realax_maker,
        static_maker=MPGGAStaticMaker(run_vasp_kwargs=run_vasp_kwargs, 
            copy_vasp_kwargs=default_MPGGADoubleRelaxStaticMaker.static_maker.copy_vasp_kwargs))

    for structure_id, structure in structures.items():
        flow = double_maker.make(structure=structure)
        flow.update_metadata({
            "material_id": structure_id,
            "run_name": args.run_name,
            "structure_source": args.structures})
        lpad.add_wf(flow_to_workflow(flow))


if __name__ == "__main__":
    main()
