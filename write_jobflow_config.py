import os
from pathlib import Path
import yaml
from urllib.parse import quote_plus
from argparse import ArgumentParser

def update_host_port(dict_):
    if "host" in dict_:
        dict_["host"] = "mongodb://" + quote_plus(os.getenv("SOCKET"))
    if "port" in dict_:
        del dict_['port']
    for key, value in dict_.items():
        if isinstance(value, dict):
            dict_[key] = update_host_port(value)
    return dict_

def main():
    parser = ArgumentParser()
    parser.add_argument("output_file", type=Path)
    args = parser.parse_args()
    with open(os.getenv("JOBFLOW_CONFIG_FILE"), "rt") as default_config_file:
        our_config = yaml.safe_load(default_config_file)
    our_config = update_host_port(our_config)
    with open(args.output_file, "wt") as output_file:
        output_file.write(yaml.dump(our_config))


if __name__ == "__main__":
    main()