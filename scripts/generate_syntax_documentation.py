#!/usr/bin/env python3
#
# Helper script to convert Charlib YAML config file syntax to RST documentation.
#
# Operates like so:
#   Python Schema -> JSON Schema -> RST

from charlib.config.syntax import ConfigFile

import os

if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.abspath(__file__))
    res_dir = os.path.join(this_file_dir, "..", "docs/manual/source/chapters")

    schemas = [
        [ConfigFile.SchemaKind.CELL_SCHEMA,       "05_cell_yaml_syntax"],
        [ConfigFile.SchemaKind.SETTINGS_SCHEMA,   "05_settings_yaml_syntax"]
    ]

    # Generate JSONs
    for sch in schemas:
        sch_kind = sch[0]
        sch_path = sch[1]
        ConfigFile.dump_json_schema(sch_kind, os.path.join(res_dir, sch_path+".json"))

    # Convert to RST
    os.system(f"jsonschema2rst {res_dir} {res_dir}")

    # Post-processing
    for sch in schemas:
        sch_kind = sch[0]
        sch_path = sch[1]

        # Rename keywords
        os.system(f""" sed -i 's/:Required:/:Required keywords:/g' {res_dir}/{sch_path}.rst""")
        os.system(f""" sed -i 's/\*\*Properties:\*\*/:Allowed keywords:/g' {res_dir}/{sch_path}.rst""")

        # Make type look nicer
        os.system(f""" sed -i 's/:type: ``float or int``/:type: ``float`` or ``int``/g' {res_dir}/{sch_path}.rst""")

    os.system(f""" sed -i '5s/05_settings_yaml_syntax/settings/' {res_dir}/05_settings_yaml_syntax.rst""")
    os.system(f""" sed -i '5s/05_cell_yaml_syntax/cell/' {res_dir}/05_cell_yaml_syntax.rst""")

    os.system(f"rm -rf {res_dir}/index.rst")
    os.system(f"rm -rf {res_dir}/*.json")
