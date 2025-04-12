#!/usr/bin/env python3
import pandas as pd
import sys
import os
import glob
import vasp_settings
from ase import Atoms
from ase.io import read
from ase.calculators.vasp import Vasp
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.core import Structure
from pymatgen.io.vasp.sets import MPRelaxSet, MPStaticSet, MPNonSCFSet, VaspInputSet
import warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=UserWarning)

def sequential_run_vasp(strc_in: Atoms):
    jobs = ["1.coarse", "2.normal", "3.spin", "4.precise", "5.fixcell"] #, "6.dfpt"]
    exit_codes = {}
    calculators = [vasp_settings.CoarseOpt,
                   vasp_settings.NormalOpt,
                   vasp_settings.SpinOpt,
                   vasp_settings.PrecOpt,
                   vasp_settings.FixcellOpt,
                #    vasp_settings.DFPT,
                   ]
    strcs_opt = {}
    energies = {}
    for i in [0, 1, 2, 3, 4]: # exclude 6.dfpt
        job, calculator = jobs[i], calculators[i]
        os.system(f"mkdir {job}")
        if i < 5:
            try:
                if i > 0:
                    files_mv = "CHGCAR"
                    os.system("mv %s/%s %s/" % (jobs[i-1], files_mv, job))
                strc_opt = calculator(strc_input=strc_in, wdir=job)
                energy = strc_opt.get_potential_energy()
                print(f"Info: {job} energy = {energy} eV")
                strcs_opt[job] = strc_opt
                energies[job] = energy
                strc_in = strc_opt
                exit_codes[job] = 0
            except:
                print(f"Error: {job} job encountered error. Return a old calculation retrieved.")
                old_cal = Vasp(restart=True, directory=job)
                strc_in = old_cal.get_atoms()
                strc_old = old_cal.get_atoms()
                energy_old = strc_old.get_potential_energy()
                strcs_opt[job] = strc_old
                energies[job] = energy_old
                # Codes here to be optimized
                exit_codes[job] = 1
        else:
            try:
                files_link = "{CHGCAR,WAVECAR}"
                os.system("ln -s ../%s/%s %s/" % (jobs[i-1], files_link, job))
                omega_real, omega_imaginary = calculator(strc_input=strc_in, wdir=job)
                n_real, n_imaginary = len(omega_real), len(omega_imaginary)
                print(f"Info: Harmonic phonon frequencies at Gamma point include" +
                      f"{n_real} real and {n_imaginary} imaginary modes.")
                line = f"Frequencies at Gamma (meV)\nReal ({n_real}): {omega_real}\nImag ({n_imaginary}): {omega_imaginary}"
                if n_imaginary <= 3:
                    with open(file="Success.Stable", mode='w', encoding='utf-8') as f:
                        f.writelines(line)
                else:
                    with open(file="Failed.Unstable", mode='w', encoding='utf-8') as f:
                        f.writelines(line)
            except:
                print(f"Error: {job} job encountered error. Return a old calculation retrieved.")
                # Codes here to be optimized
    # Store the results for relaxation jobs only
    results = pd.DataFrame({
        "job": list(energies.keys()),
        "strc_opt": list(strcs_opt.values()),
        "energy": list(energies.values())
    })
    return exit_codes, results


# only used for MPRelaxSet that ivoke by pymatgen not ase
NP = 64 #int(sys.argv[1]) # carefully define
vasprun_stdout = "vasp_run.out"
VASP_COMMAND = f"mpirun -np {NP} vasp_std > {vasprun_stdout}"

def mpset_cal(strc: Structure):
    user_potcar_setting = {"W": "W_sv"}
    user_incar_setting = {
        "NPAR": 2,
        "NCORE": 2,
        "KPAR": 2,
        "ISMEAR": 0,  # this is NOT consistent with MPRelaxSet
        "SIGMA": 0.01,# not consistent, but to avoid the error from tetrahedron method
    }
    # vaspsets = [MPRelaxSet, MPStaticSet, MPNonSCFSet, MPNonSCFSet]
    jobs = ["mp-relax", "mp-scf", "mp-dos", "mp-bands"]

    for index in [0, 1]:
        job = jobs[index]
        if not os.path.exists(job):
            os.makedirs(job)
        if index == 0:
            vaspinputset = MPRelaxSet(structure=strc,
                                      user_incar_settings=user_incar_setting,
                                      user_potcar_settings=user_potcar_setting,
                                      )
        if index == 1:
            vaspinputset = MPStaticSet(structure=Structure.from_file(f"mp-relax/CONTCAR"),
                                       user_incar_settings=user_incar_setting,
                                       user_potcar_settings=user_potcar_setting,
                                       )
        if index == 2:
            vaspinputset = MPNonSCFSet.from_prev_calc(prev_calc_dir="mp-scf/",
                                                      mode="uniform",
                                                      copy_chgcar = True,
                                                      user_incar_settings=user_incar_setting,
                                                      user_potcar_settings=user_potcar_setting,
                                                      )
        if index == 3:
            # The high-symmetry k-path differs with those from SeekPath (name and direction)
            vaspinputset = MPNonSCFSet.from_prev_calc(prev_calc_dir="mp-scf/",
                                                      mode="line",
                                                      copy_chgcar = True,
                                                      user_incar_settings=user_incar_setting,
                                                      user_potcar_settings=user_potcar_setting,
                                                      )
        vaspinputset.write_input(job)
        command = f"cd {job}; {VASP_COMMAND}; cd ../"
        os.system(command=command)
    return 0

def get_bandgap():
    from pymatgen.io.vasp import Vasprun
    
    # Parse the vasprun.xml file to get the band structure
    vasprun = Vasprun("./mp-bands/vasprun.xml")
    band_structure = vasprun.get_band_structure(kpoints_filename="./mp-bands/KPOINTS", line_mode=True)
    band_gap_info = band_structure.get_band_gap()
    band_gap = band_gap_info['energy']
    print(f"Info: band gap = {band_gap:.4f} eV")
    if band_gap > 0:
        with open(file=f"./Info.Semiconductor", mode='w', encoding='utf-8') as f:
            f.writelines(f"Eg: {band_gap}\n" +
                         f"Direct: {band_gap_info['direct']}\n" +
                         f"Transition: {band_gap_info['transition']}\n"
                         )

def get_ita_spg(strc_in:Atoms):
    pmgstrc = AseAtomsAdaptor.get_structure(strc_in)
    spg_no = SpacegroupAnalyzer(pmgstrc).get_space_group_number()
    spg_sym= SpacegroupAnalyzer(pmgstrc).get_space_group_symbol()
    return spg_sym, spg_no

def get_primitive(strc_file: str, symprec=1E-2):
    strc = Structure.from_file(strc_file)
    full_formula = strc.composition.to_pretty_string()
    reduced_formula = strc.composition.reduced_composition.to_pretty_string()
    sga = SpacegroupAnalyzer(structure=strc, symprec=symprec) # default symprec=0.01 in SpaceGroupAnalyzer
    ITA_number = sga.get_space_group_number()
    # strc_prim = sga.get_primitive_standard_structure()
    strc_prim = sga.find_primitive()
    _ = strc_prim.to(f"{reduced_formula}_{full_formula}_{ITA_number}_primitive.CIF", fmt="cif")
    _ = strc_prim.to(f"POSCAR_{reduced_formula}_{full_formula}_{ITA_number}_primitive.vasp", fmt="poscar")

if __name__ == "__main__":
    tolerance = 1E-5
    index = sys.argv[1] # not yet be used
    cif = glob.glob("generated_*.cif")[0]
    get_primitive(cif)
    # to get the primitive cell
    poscar = glob.glob("POSCAR_*.vasp")[0]
    strc_in = read(poscar)
    
    print(f"The initial symmetry: %s (%s) , with symprec (pymatgen) = {tolerance:5.1E}" % get_ita_spg(strc_in))
    exit_codes, df_vaspout = sequential_run_vasp(strc_in=strc_in)
    print(f"Run status: {exit_codes}")
    # df_vaspout["index"] = index
    # df_vaspout.to_pickle(f"./vaspout_{index}.pkl")
    final_structure = df_vaspout.loc[df_vaspout["job"] == "5.fixcell", "strc_opt"].values[0]
    print(f"The final symmetry: %s (%s) , with symprec (pymatgen) = {tolerance:5.1E}" % get_ita_spg(final_structure))
    
    # MPRelaxSet calculations
    old_cal = Vasp(restart=True, directory="5.fixcell")
    strc_in = old_cal.get_atoms()
    strc_pmg = AseAtomsAdaptor.get_structure(strc_in)
    os.makedirs("10.mpsets", exist_ok=True)
    os.chdir("10.mpsets")
    exit_code = mpset_cal(strc=strc_pmg)
    # get_bandgap()
    os.chdir("../")
    
