from atomate2.vasp.jobs.core import RelaxMaker
from jobflow import run_locally
from pymatgen.core import Structure
from pymatgen.io.vasp.sets import MPRelaxSet

# construct an FCC silicon structure
si_structure = Structure(
    lattice=[[0, 2.73, 2.73], [2.73, 0, 2.73], [2.73, 2.73, 0]],
    species=["Si", "Si"],
    coords=[[0, 0, 0], [0.25, 0.25, 0.25]],
)

# make a relax job to optimise the structure
relax_job = RelaxMaker(input_set_generator=MPRelaxSet()).make(si_structure)

# run the job
run_locally(relax_job, create_folders=True)