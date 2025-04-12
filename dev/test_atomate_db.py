from jobflow import SETTINGS

store = SETTINGS.JOB_STORE

# connect to the job store
store.connect()

# query the job store
result = store.query_one(
    {"output.formula_pretty": "Si"}, properties=["output.output.energy_per_atom"]
)
print(result)