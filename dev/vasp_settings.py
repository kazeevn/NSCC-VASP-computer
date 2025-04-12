#!/usr/bin/env python3
import os
from ase import Atoms
from ase.calculators.vasp import Vasp
import seekpath
from pymatgen.io.vasp.inputs import Kpoints

tolerance = 1E-5 # carefully check!!!, 1E-5 is default value
pp_setups = {'base': 'recommended', 'W': '_sv'}
ldau_luj = {
    "Co": {"L": 2, "U": 3.32, "J": 0},
    "Cr": {"L": 2, "U": 3.7, "J": 0},
    "Fe": {"L": 2, "U": 5.3, "J": 0},
    "Mn": {"L": 2, "U": 3.9, "J": 0},
    "Mo": {"L": 2, "U": 4.38, "J": 0},
    "Ni": {"L": 2, "U": 6.2, "J": 0},
    "V": {"L": 2, "U": 3.25, "J": 0},
    "W": {"L": 2, "U": 6.2, "J": 0},
}
def IfSpin(strc_opt: Atoms):
    mag_max = abs(strc_opt.get_magnetic_moments()).max()
    if abs(mag_max) < 0.15: # be careful with this threshold
        tag = 1
    else:
        print(f"Info: Max absolute magnetic moment = {mag_max} uB")
        tag = 2
    return tag

def write_highsym_kpoints(strc_input: Atoms,
                          k_division: int = 30,
                          tolerance: float = 1e-5,
                          kpoints_file: str = "./KPOINTS",
                          ):
    lattice = strc_input.get_cell()
    positions = strc_input.get_scaled_positions()
    numbers = strc_input.get_atomic_numbers()

    seekpath_output = seekpath.get_path(structure=(lattice, positions, numbers),
                                        symprec=tolerance,
                                        )
    spacegroup = seekpath_output["spacegroup_international"]
    ITA_number = seekpath_output["spacegroup_number"]
    print(f"Info: Used {tolerance = : 9.6f}, {spacegroup} ({ITA_number})")

    # Generate k-point path for VASP
    kpath = seekpath_output['path']
    kpoints = seekpath_output['point_coords']
    labels = []
    kpt_list = []
    for segment in kpath:
        start_label, end_label = segment
        start_kpt = kpoints[start_label]
        end_kpt = kpoints[end_label]
        if start_label == "GAMMA":
            start_label = '\\Gamma'
        if end_label == "GAMMA":
            end_label = '\\Gamma'
        labels.extend([start_label, end_label])
        kpt_list.extend([start_kpt, end_kpt])
    comment_line = f"Line-mode high-symmetry k-path {spacegroup} ({ITA_number})"
    kpoints = Kpoints(comment=comment_line,
                      num_kpts=k_division,
                      style=Kpoints.supported_modes.Line_mode,
                      coord_type="Reciprocal",
                      kpts=kpt_list,
                      labels=labels,
                      )

    kpoints.write_file(filename=kpoints_file)

def CoarseOpt(strc_input:Atoms, wdir=".", kspacing=0.25, If2D=False):
    ## Coarse relaxation
    formula = strc_input.get_chemical_formula(mode="metal") # string of full chemical formula
    coar = Vasp(directory=wdir,
                label="opt",
                txt="vasp_run.out",
                setups=pp_setups,
                ldau_luj=ldau_luj,
                xc="pbe",
                gamma = True,
                kspacing=kspacing,
                system=formula,
                istart=0,
                icharg=2,
#                 encut=520,
                isif=3,
                ismear=0,
                sigma=0.05,
                algo="Normal",
                addgrid=True,
                npar=2,
                ncore=2,
                kpar=2,
                ediff = 1E-5,
                prec = "Accurate",
                ediffg = -0.04,
                lorbit=10,
#                 lreal= False,
                lcharg= False,
                lwave= False,
                isym=2,
                symprec=tolerance,
                nelmin=8,
                nelm=200,
                nsw=99,
                potim=0.5,
                ibrion=2
                )
    strc_input.set_calculator(coar)
    if If2D:
        with open(file=f"./{wdir}/OPTCELL", mode='w', encoding='utf-8') as f:
            f.writelines("110\n110\n000")
    strc_input.get_potential_energy()
    return strc_input

def NormalOpt(strc_input:Atoms, wdir=".", kspacing=0.2, If2D=False):
    ## Fine relaxation of coarse relaxed structure with normal settings
    formula = strc_input.get_chemical_formula(mode="metal") # string of full chemical formula
    norm = Vasp(directory=wdir,
                label="opt",
                txt="vasp_run.out",
                setups=pp_setups,
                ldau_luj=ldau_luj,
                xc="pbe",
                gamma = True,
                kspacing=kspacing,
                system=formula,
                istart=0,
                icharg=2,
                encut=520,
                isif=3,
                ismear=0,
                sigma=0.02,
                algo="Normal",
                addgrid=True,
                npar=2,
                ncore=2,
                kpar=2,
                ediff = 1E-6,
                prec = "Accurate",
                ediffg = -1E-3,
                lorbit=10,
                lreal= False,
                lcharg= True,
                lwave= False,
                isym=2,
                symprec=tolerance,
                nelmin=8,
                nelm=200,
                nsw=500,
                potim=0.5,
                ibrion=2
                )
    strc_input.set_calculator(norm)
    if If2D:
        with open(file=f"./{wdir}/OPTCELL", mode='w', encoding='utf-8') as f:
            f.writelines("110\n110\n000")
    strc_input.get_potential_energy()
    return strc_input

def SpinOpt(strc_input:Atoms, wdir=".", kspacing=0.2, If2D=False):
    ## Fine relaxation of coarse relaxed structure with normal settings
    formula = strc_input.get_chemical_formula(mode="metal") # string of full chemical formula
    spin = Vasp(directory=wdir,
                label="opt",
                txt="vasp_run.out",
                setups=pp_setups,
                ldau_luj=ldau_luj,
                xc="pbe",
                gamma = True,
                kspacing=kspacing,
                system=formula,
                istart=1,
                icharg=1,
                encut=520,
                isif=3,
                ismear=0,
                sigma=0.02,
                algo="Normal",
                addgrid=True,
                npar=2,
                ncore=2,
                kpar=2,
                ispin=2,    # Spin-polarised test if the metal is magnetic
                ediff = 1E-6,
                prec = "Accurate",
                ediffg = -1E-3,
                lorbit=10,
                lreal= False,
                lcharg= True,
                lwave= False,
                isym=2,
                symprec=tolerance,
                nelmin=8,
                nelm=200,
                nsw=500,
                potim=0.5,
                ibrion=2
                )
    strc_input.set_calculator(spin)
    if If2D:
        with open(file=f"./{wdir}/OPTCELL", mode='w', encoding='utf-8') as f:
            f.writelines("110\n110\n000")
    strc_input.get_potential_energy()
    return strc_input

def PrecOpt(strc_input:Atoms, wdir=".", kspacing=0.15, If2D=False):
    ## Precise relaxation
    formula = strc_input.get_chemical_formula(mode="metal") # string of full chemical formula
    ispin = IfSpin(strc_input)
    prec = Vasp(directory=wdir,
                label="opt",
                txt="vasp_run.out",
                setups=pp_setups,
                ldau_luj=ldau_luj,
                xc="pbe",
                gamma = True,
                kspacing=kspacing,
                system=formula,
                istart=1,
                icharg=1,
                encut=520,
                isif=3,
                ismear=0,
                sigma=0.01,
                algo="Normal",
                addgrid=True,
                npar=2,
                ncore=2,
                kpar=2,
                ispin=ispin,
                ediff = 1E-8,
                prec = "Accurate",
                ediffg = -1E-4,
                lorbit=10,
                lreal= False, # Write WAVECAR
                lcharg= True, # Write CHGCAR
                lwave= False,
                isym=2,
                symprec=tolerance,
                nelmin=8,
                nelm=200,
                nsw=500,
                potim=0.5,
                ibrion=2
                )
    strc_input.set_calculator(prec)
    if If2D:
        with open(file=f"./{wdir}/OPTCELL", mode='w', encoding='utf-8') as f:
            f.writelines("110\n110\n000")
    strc_input.get_potential_energy()  # Note: this line evokes the vasp calculation by ASE_VASP_COMMAND
    return strc_input

def FixcellOpt(strc_input:Atoms, wdir=".", kspacing=0.15):
    ## Precise relaxation
    formula = strc_input.get_chemical_formula(mode="metal") # string of full chemical formula
    ispin = IfSpin(strc_input)
    prec = Vasp(directory=wdir,
                label="opt",
                txt="vasp_run.out",
                setups=pp_setups,
                ldau_luj=ldau_luj,
                xc="pbe",
                gamma = True,
                kspacing=kspacing,
                system=formula,
                istart=1,
                icharg=1,
                encut=520,
                isif=2, # Note: Fix cell, only atomic positions are relaxed
                ismear=0,
                sigma=0.01,
                algo="Normal",
                addgrid=True,
                npar=2,
                ncore=2,
                kpar=2,
                ispin=ispin,
                ediff = 1E-8,
                prec = "Accurate",
                ediffg = -1E-4,
                lorbit=11,
                lreal= False,
                lcharg= True, # Write CHGCAR
                lwave= True, # Write WAVECAR
                isym=2,
                symprec=tolerance,
                nelmin=8,
                nelm=200,
                nsw=500,
                potim=0.5,
                ibrion=2
                )
    strc_input.set_calculator(prec)
    strc_input.get_potential_energy()  # Note: this line evokes the vasp calculation by ASE_VASP_COMMAND
    return strc_input

def DFPT(strc_input:Atoms, wdir=".", kspacing=0.15):
    ## Harmonic frequencies calculation
    formula = strc_input.get_chemical_formula(mode="metal") # string of full chemical formula
    ispin = IfSpin(strc_input)
    dfpt = Vasp(directory=wdir,
                label="dfpt",
                txt="vasp_run_dfpt.out",
                setups=pp_setups,
                ldau_luj=ldau_luj,
                xc="pbe",
                gamma = True,
                kspacing=kspacing,
                system=formula,
                istart=1,
                icharg=1,
                encut=520,
                isif=2,
                ismear=0,
                sigma=0.02,
                algo="Normal",
                nelmin=8,
                addgrid=True,
                ispin=ispin,
                ediff = 1E-8,
                prec = "Accurate",
                ediffg = -1E-4,
                lorbit=11,
                lreal= False,
                lcharg= False,
                lwave= False,
                isym=2,
                symprec=tolerance,
                nelm=200,
                nsw=1,
                # potim=0.5,
                ibrion=8  # symmetric DFPT
                )
    strc_input.set_calculator(dfpt)
    strc_input.get_potential_energy()  # Note: this line evokes the vasp calculation by ASE_VASP_COMMAND
    return dfpt.read_vib_freq() # Directly read the OUTCAR

def SCF(strc_input:Atoms, wdir=".", kspacing=0.10, ispin=1):
    ## Precise SCF calculation
    formula = strc_input.get_chemical_formula(mode="metal") # string of full chemical formula
    ispin = IfSpin(strc_input)
    scf  = Vasp(directory=wdir,
                label="scf",
                txt="vasp_run.out",
                setups=pp_setups,
                ldau_luj=ldau_luj,
                xc="pbe",
                gamma = True,
                kspacing=kspacing,
                system=formula,
                istart=1,
                icharg=1,
                encut=520,
                isif=2,
                ismear=-5,
                # sigma=0.02,
                algo="Normal",
                addgrid=True,
                npar=2,
                ncore=2,
                kpar=2,
                ispin=ispin,
                ediff = 1E-8,
                prec = "Accurate",
                # ediffg = -1E-4,
                lorbit=11,
                lreal= False,
                lcharg= True, # Write CHGCAR
                lwave= True, # Write WAVECAR
                isym=2,
                symprec=tolerance,
                nelmin=8,
                nelm=200,
                nsw=0,
                potim=0.5,
                ibrion=-1
                )
    strc_input.set_calculator(scf)
    strc_input.get_potential_energy() # scf.calculate()  # Note: this line evokes the vasp calculation by ASE_VASP_COMMAND
    return scf

def DOS(strc_input:Atoms, wdir=".", kspacing=0.08, ispin=1):
    ## Density of States calculation
    formula = strc_input.get_chemical_formula(mode="metal") # string of full chemical formula
    ispin = IfSpin(strc_input)
    dos  = Vasp(directory=wdir,
                label="dos",
                txt="vasp_run.out",
                setups=pp_setups,
                ldau_luj=ldau_luj,
                xc="pbe",
## ----------------------------------------------------------------------##
                gamma = True,
                kspacing=kspacing,
                system=formula,
                istart=0, # Do NOT read in the WAVECAR
                icharg=11, # Non-SCF calculation
                encut=520,
                isif=2,
                ismear=-5,
                # sigma=0.02,
                algo="Normal",
                addgrid=True,
                npar=2,
                ncore=2,
                kpar=2,
                ispin=ispin,
                ediff = 1E-8,
                prec = "Accurate",
                # ediffg = -1E-4,
                lorbit=11,
                lreal= False,
                lcharg= False,
                lwave= True,
                isym=2,
                symprec=tolerance,
                nelmin=8,
                nelm=200,
                nsw=0,
                potim=0.5,
                ibrion=-1
                )
    strc_input.set_calculator(dos)
    strc_input.get_potential_energy() # dos.calculate()  # Note: this line evokes the vasp calculation by ASE_VASP_COMMAND
    return dos

#tetragonal
# band_path = {
#     "path": "GXMGZRAZXR,MA",
#     "npoints": 302
# }
def Bands(strc_input:Atoms, wdir=".", kpts=None, ispin=1):
    ## Bands strcuture calculation
    formula = strc_input.get_chemical_formula(mode="metal") # string of full chemical formula
    ispin = IfSpin(strc_input)
    bands = Vasp(directory=wdir,
                label="bands",
                txt="vasp_run.out",
                setups=pp_setups,
                ldau_luj=ldau_luj,
                xc="pbe",
#                kpts={'path': f"{wdir}/KPOINTS"}, # k-points to KPOINTS file
## ----------------------------------------------------------------------##
                system=formula,
                istart=0, # Do NOT read in the WAVECAR
                icharg=11, # Non-SCF calculation
                encut=520,
                isif=2,
                ismear=0,
                sigma=0.01,
                algo="Normal",
                addgrid=True,
                npar=2,
                ncore=2,
                kpar=2,
                ispin=ispin,
                ediff = 1E-8,
                prec = "Accurate",
                # ediffg = -1E-4,
                lorbit=11,
                lreal= False,
                lcharg= False,
                lwave= False,
                isym=2,
                symprec=tolerance,
                nelmin=8,
                nelm=200,
                nsw=0,
                potim=0.5,
                ibrion=-1
                )
    strc_input.set_calculator(bands)
    bands.write_input(strc_input)
    write_highsym_kpoints(strc_input=strc_input, k_division=80,
                          tolerance=tolerance, kpoints_file=f"{wdir}/KPOINTS")
    #strc_input.get_potential_energy() # bands.calculate()  # Note: this line evokes the vasp calculation by ASE_VASP_COMMAND
#    os.system("cd 9.bands.primitive; mpirun -np 64 vasp_std > vasp_run.out ; cd ../")
    return 0


