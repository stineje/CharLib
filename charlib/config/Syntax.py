"""This module contains YAML file syntax parsing"""

import sys

from schema import Schema, And, Or, Use, Optional, Literal, SchemaError
import json
from enum import Enum
from schema import Regex

class ConfigFile:
    """
    This class contains a YAML Configuration file related functionality.
    """

    number_syntax = Schema(
        Or(float, int)
    )

    # TODO: Figure out a better way how to display this in manual, so that
    #       it is not copied to all units, but only referenced
    SI_PREFIX = """^((yocto|y)|""" \
                  """(zepto|z)|""" \
                   """(atto|a)|""" \
                  """(femto|f)|""" \
                   """(pico|p)|""" \
                   """(nano|n)|""" \
                  """(micro|u)|""" \
                  """(milli|m)|""" \
                      """()|""" \
                   """(kilo|k)|""" \
                   """(mega|M)|""" \
                   """(giga|G)|""" \
                   """(tera|T)|""" \
                   """(peta|P)|""" \
                    """(exa|E)|""" \
                  """(zetta|Z)|""" \
                  """(yotta|Y))"""

    voltage_syntax = Schema(Regex(SI_PREFIX + """(v|V|volts|Volts)"""))
    current_syntax = Schema(Regex(SI_PREFIX + """(a|A|amp|amps|Amp|Amps)"""))
    time_syntax = Schema(Regex(SI_PREFIX + """(s|seconds|Seconds)"""))
    capacitance_syntax = Schema(Regex(SI_PREFIX + """(f|F|farads|Farads)"""))
    resistance_syntax = Schema(Regex(SI_PREFIX + """(Ω|ohm|ohms|Ohm|Ohms)"""))
    power_syntax = Schema(Regex(SI_PREFIX + """(w|W|watts|Watts)"""))
    energy_syntax = Schema(Regex(SI_PREFIX + """(j|J|joules|Joules)"""))

    cell_syntax = Schema({
        Literal(
            "netlist",
            description="The path to the spice file containing the netlist for this cell."
        ) : str,

        Literal(
            "models",
            description="A list of paths to the spice models for transistors used in this \
                            cell's netlist. If omitted, CharLib assumes each cell has no \
                            dependencies. \n \
                            * Using the syntax ``path/to/file`` will result in \
                            ``.include path/to/file`` in SPICE simulations. \n \
                            * Using the syntax ``path/to/dir`` will allow CharLib to search \
                              the directory for subcircuits used in a particular cell and \
                              include them using ``.include path/to/dir/file``.\n \
                            * Using the syntax ``path/to/file section`` will result in \
                              ``.lib path/to/file section`` in SPICE simulations."
        ) : [str],

        Optional(
            Literal(
                "inputs",
                description="A list of input pin names as they appear in the cell netlist."
            )
        ) : [str],

        Optional(
            Literal(
                "outputs",
                description="A list of output pin names as they appear in the cell netlist."
            )
        ) : [str],


        Literal(
            "functions",
            description="A list of verilog functions describing each output as logical function"
                        + " of inputs."
        ) : [str],

        Literal(
                "data_slews",
                description="A list of input pin slew rates to characterize."
                            + " Unit is specified by ``settings.units.time``."
        ) : [Or(float, int)],

        Literal(
            "loads",
            description="A list of output capacitive loads to characterize."
                         + " Unit is specified by ``settings.units.capacitive_load``."
        ) : [number_syntax],

        Optional(
            Literal(
                "simulation_timestep",
                description="The simulation timestep. The unit is specified by"
                            + " ``settings.units.time``."
            ),
            default=0
        ) : number_syntax,

        Optional(
            Literal(
                "area",
                description="The physical area occupied by the cell layout, specified in ``um^2``."
            ),
            default=0
        ) : number_syntax,

        Optional(
            Literal(
                "footprint",
                description="Footprint of the cell as placed into the liberty file."
            )
        ) : str,

        Optional(
            Literal(
                "clock",
                description="The clock pin name and edge direction. The format is:"
                            + " ``<edge_direction> <clock_pin_name>``, where ``edge_direction``"
                            + " can be one of: ``posedge`` or ``negedge``"
                            + " (e.g. ``posedge CLK`` or ``negedge CKB``)."
            )
        ) : Regex("^(posedge|negedge) [a-zA-Z0-9_]+"),

        Optional(
            Literal(
                "flops",
                description="""A list of storage element names. """
                            """These are the names of flip-flops that Charlib puts under \
                               ``ff`` keyword in the generated liberty file"""
            )
        ) : [str],

        Optional(
            Literal(
                "setup_time_range",
                description="A list of margins to be used when characterizing setup time."
            )
        ) : [number_syntax],

        Optional(
            Literal(
                "hold_time_range",
                description="A list of margins to be used when characterizing hold time."
            )
        ) : [number_syntax],

        Optional(
            Literal(
                "set",
                description="""The asynchronous set pin name, and edge direction. """
                            """For sequential cells only. If omitted, CharLib assumes the cell """
                            """does not have a set pin. """
                            """The format is ``<edge_direction> <pin_name>``, where """
                            """``edge_direction`` can be one of: ``posedge`` or ``negedge``. """
                            """E.g. ``negedge AS`` defines active low set pin."""
            )
        ) : Regex("^(posedge|negedge) [a-zA-Z0-9_]+"),

        Optional(
            Literal(
                "reset",
                description="""The asynchronous reset pin name, and edge direction. """
                            """For sequential cells only. If omitted, CharLib assumes the cell """
                            """does not have a reset pin. """
                            """The format is ``<edge_direction> <pin_name>``. Where """
                            """``edge_direction`` can be one of: ``posedge`` or ``negedge``. """
                            """E.g. ``posedge AR`` defines active high reset pin."""
            )
        ) : Regex("^(posedge|negedge) [a-zA-Z0-9_]+"),

        Optional(
            Literal(
                "clock_skew",
                description="The slew rate to use for the clock signal in simulation. \
                             For sequential cells only. \
                             Unit is specified by ``settings.units.time``."
            )
        ) : number_syntax,

        Optional(
            Literal(
                "plots",
                description="A string, or list of strings specifying which plots to show \
                             for this cell."
            )
        ) : Or("all","none",[Or("io", "delay", "energy")])

    }, description="""Any of keys under ``cells`` can be omitted from cell entries by instead """
                   """specifying them in the ``settings.cell_defaults``. CharLib automatically """
                   """merges any key-value pairs from ``settings.cell_defaults`` to each cell """
                   """entry when characterizing the cell.\n If a key appears in a cell's entry, """
                   """and in ``cell_defaults``, the value in the cell entry overrides the value """
                   """from ``cell_defaults``. """)

    settings_syntax = Schema({
        Optional(
            Literal(
                "lib_name",
                description="The library name to put to the exported liberty file."
            ),
            default="unnamed_lib"):
            str,

        Optional(
            Literal(
                "units",
                description="Specifies physical units to use for input and output values."
            )
        ):
            {
                Optional(
                    Literal(
                        "time",
                        description="The unit of time."
                    ),
                    default="ns") : time_syntax,

                Optional(
                    Literal(
                        "voltage",
                        description="The unit of electrical voltage."
                    ),
                    default="V") : voltage_syntax,

                Optional(
                    Literal(
                        "current",
                        description="The unit of electrical current"
                    ),
                    default="uA") : current_syntax,

                Optional(
                    Literal(
                        "capacitive_load",
                        description="The unit of capacitance"
                    ),
                    default="pF") : capacitance_syntax,

                Optional(
                    Literal(
                        "pulling_resistance",
                        description="The unit of resistance"
                    ),
                    default="Ohm") : resistance_syntax,

                Optional(
                    Literal(
                        "leakage_power",
                        description="The unit of power"
                    ),
                    default="nW"): power_syntax,

                Optional(
                    Literal(
                        "energy",
                        description="The unit of energy",
                    ),
                    default="fJ"): energy_syntax
            },

        Optional("named_nodes") : {
            Optional(
                Literal(
                    "primary_power",
                    description="Device power supply node name"
                )
            ) : {
                Optional("name", default="VDD"): str,
                Optional("voltage", default=3.3): number_syntax
            },

            Optional(
                Literal(
                    "primary_ground",
                    description="Device ground node name"
                )
            ) : {
                Optional("name", default="VSS"): str,
                Optional("voltage", default=0): number_syntax
            },

            Optional(
                Literal(
                    "pwell",
                    description="Device p-type biasing node name"
                )
            ) : {
                Optional("name", default="VPW"): str,
                Optional("voltage", default=0): number_syntax
            },

            Optional(
                Literal(
                    "nwell",
                    description="Devices n-type biasing node name"
                )
            ) : {
                Optional("name", default="VNW"): str,
                Optional("voltage", default=3.3): number_syntax
            }
        },

        Optional(
            Literal(
                "simulator",
                description="Specifies which PySpice backend to use"
            ),
            default="ngspice-shared"
        ) : Or("ngspice-shared", "ngspice-subprocess", "xyce-serial", "xyce-parallel"),

        Optional(
            Literal(
                "logic_thresholds",
                description="Voltage thresholds to recognize signals as logical 0 or 1. \
                             Values are relative to voltage given by ``named_nodes.vdd``"
            )
        ) : {
            Optional(
                Literal(
                    "low",
                    description="The maximum fraction supply voltage recognized as a logical 0."
                ),
                default=0.2
            ) : number_syntax,

            Optional(
                Literal(
                    "high",
                    description="The minimum fraction of supply voltage recognized as a logical 1."
                ),
                default=0.8
            ) : number_syntax,

            Optional(
                Literal(
                    "high_to_low",
                    description="The threshold which must be crossed before CharLib considers \
                                 a signal falling from one to zero."
                ),
                default=0.5
            ) : number_syntax,

            Optional(
                Literal(
                    "low_to_high",
                    description="The threshold which must be crossed before Charlib considers \
                                 a signal rising from zero to one."
                ),
                default=0.5
            ) : number_syntax
        },

        Optional(
            Literal(
                "process",
                description="The process condition to set in the exported liberty file."
            ),
            default="typ"
        ) : str,

        Optional(
            Literal(
                "temperature",
                description="The temperature to use during spice simulations."
            ),
            default=25
        ) : number_syntax,

        Optional(
            Literal(
                "operating_conditions",
                description="The operating conditions to set in the exported liberty file."
            ),
        ) : str,

        Optional(
            Literal(
                "multithreaded",
                description="Run simulations in parallel, using as many threads as possible."
            ),
            default=True
        ) : bool,

        Optional(
            Literal(
                "results_dir",
                description="The directory where Charlib exports characterization results.\
                             If omitted, CharLib creates a ``results`` directory in the \
                             current folder."
            ),
            default="results"
        ) : str,

        Optional(
            Literal(
                "debug",
                description="Display debug messages, and store simulation SPICE files."
            ),
            default=False
        ) : bool,

        Optional(
            Literal(
                "debug_dir",
                description="The directory where simulation SPICE files are stored if ``debug`` \
                             keyword is set to ``True``"
            ),
            default="debug"
        ) : str,

        Optional(
            Literal(
                "quiet",
                description="Minimize the number of messages and data Charlib displays to the \
                             console."
            ),
            default=False
        ) : bool,

        Optional(
            Literal(
                "omit_on_failure",
                description="Specifies whether to terminate if a cell fails to characterize \
                             (``False``), or continue with next cells (``True``)."
            ),
            default=False
        ) : bool,

        Optional(
            Literal(
                "cell_defaults",
                description="Default values to use for all cells. \
                             See ``cells`` keyword for more information. \
                            May contain any key-value pair valid for a :ref:`04_syntax_reference_cell.json#/` entry."
            )
        # Do not pass cell_syntax here to:
        #   - avoid duplicity in documentation
        #   - have the "required" cell fields easily controllable by schema
        # "None" can't be placed here since the field does not propagate to
        # documentation
        ) : {}
    },
    description="All keywords under ``settings`` are optional. \
                 If a keyword is not present, CharLib uses default value.")

    config_file_syntax = Schema({
        Optional("settings") : settings_syntax,
        Optional("cells") : {
            Optional(str) : cell_syntax
        }
    })

    @classmethod
    def validate(cls, config):
        """
        Validates YAML config file syntax and fills the default values.
        """

        # print("Checking configuration syntax")

        # TODO: need following additional checks above schema:
        #       - check that if either of "clock", "flops", "setup_time_range" or "hold_time_range" is present,
        #         then all are

        # Fill "settings" and "cells" if not existent
        if "settings" not in config or config["settings"] == None:
            config["settings"] = {}

        if "cells" not in config or config["cells"] == None:
            config["cells"] = {}

        # Fill default keys under "settings"
        # that have other sub-keys, and no default value in cell_syntax
        keys = [{"units" : {}}    ,
                {"logic_thresholds" : {}},
                {"named_nodes" : {"primary_power": {}, "primary_ground": {}, "pwell": {}, "nwell": {}}},
                {"logic_thresholds" : {}},
                {"cell_defaults" : {}}]

        for key in keys:
            k = list(key)[0]
            v = key[k]
            if k not in config["settings"]:
                config["settings"][k] = v

        # Merge "cell_defaults" to all cells
        cells = config["cells"]
        cell_defs = config["settings"]["cell_defaults"]

        if len(cells) > 0 and len(cell_defs) > 0:
            for cell_name, cell_val in cells.items():
                c = config["cells"][cell_name]
                for k,v in cell_defs.items():
                    if k not in c:
                        c[k] = v

        # Erase the "cell_defaults"
        #   - not needed anymore -> was already merged
        #   - Schema validate should not complain
        config["settings"].pop("cell_defaults")

        #v = json.dumps(config, indent=4)
        #print(v)

        # Validate the schema
        try:
            return cls.config_file_syntax.validate(config)
        except SchemaError as e:
            print("Configuration file syntax error:")
            print(e)

            sys.exit(1)

    class SchemaKind(Enum):
        CELL_SCHEMA     = 0,
        SETTINGS_SCHEMA = 1

    @classmethod
    def dump_json_schema(cls, kind, path):
        """
        Converts "settings" or "cells" syntax to JSON schema
        """
        # Convert to JSON
        syntax = cls.settings_syntax if (kind == cls.SchemaKind.SETTINGS_SCHEMA) else cls.cell_syntax
        j = syntax.json_schema("Charlib YAML configuration file syntax")

        # Filter for better readability
        def traverse_json(j):
            poplist = []
            add_float_or_int = False

            for key, value in j.items():

                if isinstance(value, dict):
                    traverse_json(value)

                # Remove object types -> useless
                if key == "type" and value == "object":
                    poplist.append(key)

                # Remove $id
                if key == "$id":
                    poplist.append(key)

                # Remove empty required keywords
                if key == "required" and value == []:
                    poplist.append(key)

                if key == "anyOf":
                    if len(value) == 2:
                        if value[0].get("type") == "number" and value[1].get("type") == "integer":
                           poplist.append(key)
                           add_float_or_int = True

            for p in poplist:
                j.pop(p)

            if add_float_or_int:
                j["type"] = "float or int"

        traverse_json(j)
        json_schema = json.dumps(j, indent=4)

        with open(path, 'w') as f:
            f.write(json_schema)
