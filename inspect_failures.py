from pathlib import Path
import re
import warnings
from argparse import ArgumentParser
from itertools import chain
from fireworks import LaunchPad
from pymatgen.io.vasp.sets import BadInputSetWarning


def main():
    warnings.filterwarnings("ignore", message="No Pauling electronegativity for", category=UserWarning,
                        module="pymatgen")
    # Good to keep in mind, but the reference sets we intend to use in 2026 are old and have Yb_2
    warnings.filterwarnings("ignore", message=r"The structure contains Ytterbium \(Yb\) and this InputSet uses the Yb_2 PSP",
                        category=BadInputSetWarning, module="pymatgen.io.vasp.sets")
    parser = ArgumentParser(description="Investigate the FIZZLED Fireworks")
    parser.add_argument("--rerun", action="store_true",
        help="Re-run fizzled fireworks with more memory")
    parser.add_argument("--mem", type=str, default='256gb',
            help="Amount of memory to use for reruns")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--logfile", type=Path, help="Write failed FWs and launch dirs to a file")
    args = parser.parse_args()
    failure_reasons = (
        "custodian.custodian.MaxCorrectionsPerJobError", # Probably doesn't include OOM, but who knows
        "custodian.custodian.NonRecoverableError",   # Includes OOM
        "custodian.custodian.ValidationError",       # Potentially includes OOM
        r"FileNotFoundError: \[Errno 2\] No such file or directory: '.*OUTCAR", # Potentially includes OOM
        "IndexError: list index out of range",
        "PermissionError",
        "xml.etree.ElementTree.ParseError: no element found",
        r"KeyError: 'Rn'",
        "RuntimeError: Job was not successful"
    )
    lp = LaunchPad.auto_load()
    failed_id_by_reason = {}
    for reason in failure_reasons:
        failed_id_by_reason[reason] = frozenset(lp.get_fw_ids(
            query={"$and": [{"state": "FIZZLED"}, {"action.stored_data._exception._stacktrace": {"$regex": reason}}]},
            launches_mode=True))
    # The order is important - if some fireworks fizzle while the script is running, they won't trigger the validator
    all_fizzled = frozenset(lp.get_fw_ids(query={"state": "FIZZLED"}))
    for reason, failed_ids in failed_id_by_reason.items():
        if not failed_id_by_reason[reason].issubset(all_fizzled):
            raise ValueError(f"Some fireworks supposedly failed with {reason} are not marked as fizzled")
        if failed_ids:
            print(f"{len(failed_ids)} FIZZLED with trace {reason}")
    
    if args.logfile:
        with open(args.logfile, "wt") as logfile:
            for fw_id in all_fizzled:
                firework = lp.get_fw_by_id(fw_id)
                if launches := firework.launches:
                    logfile.write(f"{fw_id} {launches[0].launch_dir}\n")
                else:
                    raise ValueError(f"FW {fw_id} FIZZLED with no launches")

    fizzled_for_other_reasons = all_fizzled.difference(chain(*failed_id_by_reason.values()))
    print(f"{len(fizzled_for_other_reasons)} FIZZLED with other/no traces")

    lost_launch_ids, lost_fw_ids, inconsistent_fw_ids = lp.detect_lostruns(fizzle=bool(args.rerun))
    print(f"{len(lost_fw_ids)} Fireworks are lost")
    print("\nInvestigating\n")
    timed_out_launches = dict()
    oomed_fws = set()
    all_failed = frozenset(chain(all_fizzled, lost_fw_ids))
    walltime_kill_message = re.compile(r"=>> PBS: job killed: walltime \d+ exceeded limit \d+")
    for fw_id in all_failed:
        fw = lp.get_fw_by_id(fw_id)
        stopcar_present = False
        pbs_walltime_kill_present = False
        custodian_walltime_message = False
        for launch in fw.launches:
            if launch.launch_dir and Path(launch.launch_dir, "STOPCAR").is_file():
                stopcar_present = True
            try:
                with open(Path(launch.launch_dir, "FW_job.error"), "r") as pbs_error_log:
                    for line in pbs_error_log:
                        if walltime_kill_message.match(line.strip()):
                            pbs_walltime_kill_present = True
                        if r"ERROR:custodian.custodian:WalltimeHandler" in line:
                            custodian_walltime_message = True
                        if r"cgroup/OOM: Killed because of memory limit" in line:
                            print("OOM", fw_id, launch.launch_dir)
                            oomed_fws.add(fw_id)
            except (PermissionError, FileNotFoundError):
                pass
            if stopcar_present or pbs_walltime_kill_present or custodian_walltime_message:
                print(f"FW {fw_id} potentially timed-out in {launch.launch_dir}")
                print("STOPCAR status", stopcar_present)
                print("PBS walltime message", pbs_walltime_kill_present)
                print("Custodian walltime message", custodian_walltime_message)
                timed_out_launches[fw_id] = launch
                break

    print(f"Among them, {len(timed_out_launches)} hit the walltime")

    if args.verbose and fizzled_for_other_reasons:
        print("Other traces:")
        for fw_id in fizzled_for_other_reasons:
            fw = lp.get_fw_by_id(fw_id)
            for launch in fw.launches:
                if launch.action:
                    stacktrace = launch.action.stored_data.get("_exception", {}).get("_stacktrace")
                    if stacktrace:
                        print(f"\n--- fw_id={fw_id} ---")
                        print(stacktrace)
                        break
    if args.rerun:        
        if timed_out_launches:
            n_continued = 0
            n_fresh = 0
            for fw_id, launch in timed_out_launches.items():
                launch_dir = Path(launch.launch_dir)
                contcar = launch_dir / "CONTCAR"
                has_contcar = contcar.is_file() and contcar.stat().st_size > 0
                if has_contcar:
                    # Clean up files that block recovery in shared-user directories:
                    # - .orig files from previous custodian backup
                    # - .gz input files: copy_vasp_outputs raises PermissionError on copystat
                    #   when owned by another user
                    # - unzipped input files: gunzip_files raises FileExistsError if the
                    #   unzipped file exists alongside its .gz counterpart
                    # - STOPCAR: VaspJob.setup() never removes it; VASP exits immediately
                    #   if it is present at startup
                    for name in (
                        "INCAR.orig", "KPOINTS.orig", "POSCAR.orig", "POTCAR.orig",
                        "INCAR", "INCAR.gz",
                        "KPOINTS", "KPOINTS.gz",
                        "POSCAR", "POSCAR.gz",
                        "POTCAR", "POTCAR.gz",
                        "WAVECAR.gz", "OUTCAR",
                        "STOPCAR",
                        # They might belong to another user
                        "FW_job.error", 
                        "FW_job.out"
                    ):
                        launch_dir.joinpath(name).unlink(missing_ok=True)
                    lp.rerun_fw(fw_id, recover_launch=launch.launch_id, recover_mode='prev_dir')
                    n_continued += 1
                else:
                    # No ionic progress to recover: continue.json would overwrite the
                    # fresh POSCAR from copy_vasp_outputs with a 0-byte file.
                    print(f"WARNING: fw_id={fw_id} timed out with empty CONTCAR — rerunning fresh")
                    lp.update_spec([fw_id], {'$unset': {'spec._launch_dir': ''}}, mongo=True)
                    lp.rerun_fw(fw_id)
                    n_fresh += 1
            print(f"Requeued {n_continued} timed-out fireworks with prev_dir recovery, "
                  f"{n_fresh} restarted fresh (empty CONTCAR)")

        if oomed_fws:
            print(f"Re-running {len(other_failed)} FIZZLED fireworks with mem={args.mem}")
            lp.update_spec(list(oomed_fws), {'$set': {'spec._queueadapter.mem': args.mem}, '$unset': {'spec._launch_dir': ''}}, mongo=True)
            for fw_id in oomed_fws:
                lp.rerun_fw(fw_id)
            print(f"Requeued {len(oomed_fws)} fireworks with mem={args.mem}")
        
        if failed_id_by_reason["PermissionError"]:
            lp.update_spec(list(failed_id_by_reason["PermissionError"]), {'$unset': {'spec._launch_dir': ''}}, mongo=True)
            for fw_id in failed_id_by_reason["PermissionError"]:
                lp.rerun_fw(fw_id)
            print(f"Requeued {len(failed_id_by_reason["PermissionError"])} PermissionError'ed FWs (botchered previous recovery)")


if __name__ == "__main__":
    main()
