from mp_api.client import MPRester
from dotenv import dotenv_values


def main():
    config = dotenv_values(".env")
    with MPRester(api_key=config["MP_API_KEY"]) as mpr:
        tasks_doc = mpr.materials.tasks.search(
                ["mp-865470"],           # task_id of this calculation
                fields=["task_id", "orig_inputs", "calcs_reversed", "output", "last_updated"]
            )

if