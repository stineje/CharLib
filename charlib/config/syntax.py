"""This module contains a schema used for configuration files and tools for parsing them."""

import json

from schema import Schema, And, Or, Use, Optional, Literal, Regex
from enum import Enum

class ConfigFile:
    """Configuration file related functionality."""

    # TODO: Figure out a better way how to display this in manual, so that
    #       it is not copied to all units, but only referenced

    TRIGGER_FORMAT = '``<trigger> <name>``. For edge-sensitive devices, ``trigger`` should be ' \
                     '``posedge`` or ``negedge``. For level-sensitive devices, ``trigger`` may ' \
                     'be ``not`` or omitted altogether.'
    SI_PREFIX = '^((yocto|y)|(zepto|z)|(atto|a)|(femto|f)|(pico|p)|(nano|n)|(micro|u)|(milli|m)|' \
                '()|(kilo|k)|(mega|M)|(giga|G)|(tera|T)|(peta|P)(exa|E)|(zetta|Z)|(yotta|Y))'
    si_prefixed_syntax = lambda base_unit, SI_PREFIX=SI_PREFIX: Schema(Regex(SI_PREFIX + base_unit))

    cell_syntax = Schema({
        Literal(
            'netlist',
            description='The path to the spice file containing the netlist for this cell.'
        ) : str,
        Literal(
            'models',
            description='A list of paths to the spice models for transistors used in this cell\'s ' \
                        'netlist. If omitted, CharLib assumes each cell has no dependencies.\n'\
                        '* Using the syntax ``path/to/file`` will result in ' \
                        '``.include path/to/file`` in SPICE simulations.\n' \
                        '* Using the syntax ``path/to/dir`` will allow CharLib to search the ' \
                        'directory for subcircuits used in a particular cell and include them using '\
                        '``.include path/to/dir/file``.\n' \
                        '* Using the syntax ``path/to/file section`` will result in ' \
                        '``.lib path/to/file section`` in SPICE simulations.'
        ) : [str],
        Optional(
            Literal(
                'inputs',
                description='A list of input pin names as they appear in the cell netlist. If ' \
                            'present, used to verify function inputs.'
            )
        ) : [str],
        Optional(
            Literal(
                'outputs',
                description='A list of output pin names as they appear in the cell netlist. If ' \
                            'present, used to verify function outputs.'
            )
        ) : [str],
        Literal(
            'functions',
            description='A list of verilog functions describing each output as logical function ' \
                        'of inputs. Input and output names must match ports names in the spice ' \
                        'subcircuit.'
        ) : [str],
        Literal(
            'data_slews',
            description='A list of input pin slew rates to characterize. Unit is specified by ' \
                        '``settings.units.time``.'
        ) : [Or(float, int)],
        Literal(
            'loads',
            description='A list of output capacitive loads to characterize. Unit is specified ' \
                        'by ``settings.units.capacitive_load``.'
        ) : [Or(float, int)],
        Optional(
            Literal(
                'area',
                description='The physical core area occupied by the cell layout. Often given in ' \
                            'square microns or gate equivalents. See Section 5.1.2 of the ' \
                            'Liberty User Guide, Vol. 1 for details and examples.'
            ), default=0.0
        ) : Or(float, int),
        Optional(
            Literal(
                'clock',
                description='The clock pin name and trigger type, in the format ' \
                            f'{TRIGGER_FORMAT} (For example: ``posedge CLK`` or ``negedge CKB``)'
            )
        ) : Regex('^(posedge|negedge)[ ]*[a-zA-Z0-9_]+'),
        Optional(
            Literal(
                'enable',
                description='The enable pin name and trigger type, in the format ' \
                            f'{TRIGGER_FORMAT} (For example: ``not CLK`` or ``GE``)'
            )
        ) : Regex('^(not |())[ ]*[a-zA-Z0-9_]+'),
        Optional(
            Literal(
                'set',
                description='The name and trigger type of the cell\'s set pin, in  the format ' \
                            f'{TRIGGER_FORMAT} (for example: ``not SN`` defines an active-low ' \
                            'synchronous set pin).'
            )
        ) : Regex('^(posedge|negedge|not|!|())[ ]*[a-zA-Z0-9_]+'),
        Optional(
            Literal(
                'reset',
                description='The name and trigger type of the cell\'s reset pin, in the format ' \
                            '{TRIGGER_FORMAT} (for example: ``negedge RN`` defines an active-low ' \
                            'asynchronous reset pin).'
            )
        ) : Regex('^(posedge|negedge|not|!|())[ ]*[a-zA-Z0-9_]+'),
        Optional(
            Literal(
                'state',
                description='A list of feedback paths which encode state in a sequential cell. ' \
                            'Paths should be specified as ``<internal node> = <output pin>``.'
            )
        ) : [str],
        Optional(
            Literal(
                'pairs',
                description='A list of pairs of pins to treat as differential pairs. Pairs must ' \
                            'be listed in the format ``<noninverting_pin> <inverting_pin>``.'
            )
        ) : [str],
        Optional(
            Literal(
                'setup_time_range',
                description='A list containing the upper and lower bound to be used when ' \
                            'characterizing setup time.'
            )
        ) : [Or(float, int)],
        Optional(
            Literal(
                'hold_time_range',
                description='A list containing the upper and lower bound to be used when ' \
                            'characterizing hold time.'
            )
        ) : [Or(float, int)],
        Optional(
            Literal(
                'clock_slews',
                description='A list of clock slew rates to characterize. The cell must have a ' \
                            'clock pin in order to use this parameter. Unit is specified by ' \
                            '``settings.units.time``.'
            )
        ) : [Or(float, int)],
        Optional(
            Literal(
                'plots',
                description='A string (or list of strings) specifying which plot(s) to show ' \
                            'for this cell.'
            )
        ) : Or('all', 'none', 'io', 'delay', [str])
    }, description='Keys under a ``cell`` entry may be omitted by instead specifying them in ' \
                   'under ``settings.cell_defaults``. CharLib automatically merges any ' \
                   'key-value pairs from ``settings.cell_defaults`` into each cell entry prior ' \
                   'to characterization.\n' \
                   'If any key appears under both ``settings.cell_defaults`` and under a cell ' \
                   'entry, the value in the cell entry overrides the default.')

    settings_syntax = Schema({
        Optional(
            Literal(
                'lib_name',
                description='The library name for the liberty file. If the filename is not ' \
                            'specified on the command line with the ``--output`` option, this ' \
                            'is also used as the filename.'
            ), default='unnamed_lib'
        ) : str,

        Optional(
            Literal(
                'simulation',
                description='Specifies which simulation backend to use and which procedures to ' \
                            'apply for acquiring various types of measurements.'
            )
        ) : {
            Optional(
                Literal(
                    'backend',
                    description='Which PySpice simulator backend to use. For available options, ' \
                                'see https://pyspice.fabrice-salvaire.fr/releases/v1.4/faq.html#' \
                                'how-to-set-the-simulator'
                ), default='ngspice-shared'
            ) : Or('ngspice-shared', 'ngspice-subprocess', 'xyce-serial', 'xyce-parallel'),
            Optional(
                Literal(
                    'input_capacitance_procedure',
                    description='The name of a procedure used to measure the capacitance of ' \
                                'each input pin for each cell.' # TODO: Refer to docs for procedures
                ), default='ac_sweep'
            ) : str,
            Optional(
                Literal(
                    'combinational_delay_procedure',
                    description='The name of a procedure used to measure delays associated with ' \
                                'a combinational cell.' # TODO: Refer to docs for procedures
                ), default='combinational_worst_case'
            ) : str
        },

        Optional(
            Literal(
                'units',
                description='Specifies physical units to use for input and output values.'
            )
        ) : {
            Optional(
                Literal(
                    'time',
                    description='The unit of time.'
                ), default='ns'
            ) : si_prefixed_syntax('(s|seconds|Seconds)'),
            Optional(
                Literal(
                    'voltage',
                    description='The unit of electrical voltage.'
                ), default='V'
            ) : si_prefixed_syntax('(v|V|volts|Volts)'),
            Optional(
                Literal(
                    'current',
                    description='The unit of electrical current'
                ), default='uA'
            ) : si_prefixed_syntax('(a|A|amp|amps|Amp|Amps)'),
            Optional(
                Literal(
                    'capacitive_load',
                    description='The unit of capacitance'
                ), default='pF'
            ) : si_prefixed_syntax('(f|F|farads|Farads)'),
            Optional(
                Literal(
                    'pulling_resistance',
                    description='The unit of resistance'
                ), default='Ohm'
            ) : si_prefixed_syntax('(Ω|ohm|ohms|Ohm|Ohms)'),
            Optional(
                Literal(
                    'leakage_power',
                    description='The unit of power'
                ), default='nW'
            ): si_prefixed_syntax('(w|W|watts|Watts)'),
            Optional(
                Literal(
                    'energy',
                    description='The unit of energy',
                ), default='fJ'
            ): si_prefixed_syntax('(j|J|joules|Joules)')
        },

        Optional(
            'named_nodes',
            description='Important nodes which share the same name and function across all ' \
                        'cells in the cell library. Use named nodes to specify supply and ' \
                        'biasing node names and voltages, which produce pg_pin groups in the ' \
                        'resulting liberty file. See Section 10.1.4 and Table 10-2 in the ' \
                        'the Liberty User Guide, Vol 1 for more information.'
        ) : {
            Optional(
                Literal(
                    'primary_power',
                    description='Library-wide primary power supply node name & voltage.'
                )
            ) : {
                Optional('name', default='VDD'): str,
                Optional('voltage', default=3.3): Or(float, int)
            },
            Optional(
                Literal(
                    'primary_ground',
                    description='Library-wide primary ground node name & voltage.'
                )
            ) : {
                Optional('name', default='VSS'): str,
                Optional('voltage', default=0): Or(float, int)
            },
            Optional(
                Literal(
                    'pwell',
                    description='Library-wide p-type biasing node name & voltage'
                )
            ) : {
                Optional('name', default='VPW'): str,
                Optional('voltage', default=0): Or(float, int)
            },
            Optional(
                Literal(
                    'nwell',
                    description='Library-wide n-type biasing node name & voltage'
                )
            ) : {
                Optional('name', default='VNW'): str,
                Optional('voltage', default=3.3): Or(float, int)
            }
        },
        Optional(
            Literal(
                'logic_thresholds',
                description='Voltage thresholds for tuning edge timing. Values are specified as ' \
                            'percentages of VDD. See section 2.3 in the Liberty User Guide, ' \
                            'Vol. 1 for more information.'
            )
        ) : {
            Optional(
                Literal(
                    'low',
                    description='The percentage of the supply voltage at which a signal is ' \
                                'considered logic 0 for timing measurements. See figure 2-2 and ' \
                                'sections 2.3.6-7 in the Liberty User Guide, Vol. 1.'
                ), default=20.0
            ) : Or(float, int),
            Optional(
                Literal(
                    'high',
                    description='The percentage of the supply voltage at which a signal is ' \
                                'considered logic 1 for timing measurements. See figure 2-2 and ' \
                                'sections 2.3.8-9 in the Liberty User Guide, Vol. 1.'
                ), default=80.0
            ) : Or(float, int),
            Optional(
                Literal(
                    'falling',
                    description='The percentage of the supply voltage at which a signal is ' \
                                'considered falling for timing measurements. See figure 2-1 and ' \
                                'sections 2.3.1 & 2.3.3 in the Liberty User Guide, Vol. 1.'
                ), default=50.0
            ) : Or(float, int),
            Optional(
                Literal(
                    'rising',
                    description='The percentage of the supply voltage at which a signal is ' \
                                'considered rising for timing measurements. See figure 2-1 and ' \
                                'sections 2.3.2 & 2.3.4 in the Liberty User Guide, Vol. 1.'
                ), default=50.0
            ) : Or(float, int)
        },
        Optional(
            Literal(
                'temperature',
                description='The temperature to use during spice simulations.'
            ), default=25
        ) : Or(float, int),
        Optional(
            Literal(
                'multithreaded',
                description='Run simulations in parallel, using as many threads as possible. ' \
                            'Using the ``--jobs`` flag on the command line overrides this value.'
            ), default=True
        ) : bool,
        Optional(
            Literal(
                'results_dir',
                description='The directory where Charlib exports characterization results. If ' \
                            'omitted, CharLib creates a ``results`` directory in the current ' \
                            'folder.'
            ), default='results'
        ) : str,
        Optional(
            Literal(
                'debug',
                description='Display debug messages, and store simulation SPICE files.'
            ), default=False
        ) : bool,
        Optional(
            Literal(
                'debug_dir',
                description='The directory where simulation SPICE files are stored if ``debug`` ' \
                            'keyword is set to ``True``'
            ), default='debug'
        ) : str,
        Optional(
            Literal(
                'omit_on_failure',
                description='Specifies whether to terminate if a cell fails to characterize ' \
                            '(``False``), or continue with the remaining cells (``True``).'
            ), default=False
        ) : bool,
        Optional(
            Literal(
                'cell_defaults',
                description='Default values to use for all cells. See the ``cells`` keyword ' \
                            'for more information. May contain any key-value pair valid for a ' \
                            ':ref:`04_syntax_reference_cell.json#/` entry.'
            )
            # Do not pass cell_syntax here to:
            #   - avoid duplication in documentation
            #   - have the "required" cell fields easily controllable by schema
            # "None" can't be placed here since the field does not propagate to documentation
        ) : {}
    }, description='All keywords under ``settings`` are optional. If a keyword is not present, ' \
                   ' CharLib uses the default value.')

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

        # Fill "settings" and "cells" if not existent
        if "settings" not in config or config["settings"] == None:
            config["settings"] = {}

        if "cells" not in config or config["cells"] == None:
            config["cells"] = {}

        # Fill default keys under "settings"
        # that have other sub-keys, and no default value in cell_syntax
        keys = {"units" : {},
                "named_nodes" : {"primary_power": {}, "primary_ground": {}, "pwell": {}, "nwell": {}},
                "logic_thresholds" : {},
                "cell_defaults" : {}}
        for k, v in keys.items():
            if k not in config['settings']:
                config['settings'][k] = v

        # Merge "cell_defaults" to all cells
        for name, cell in config['cells'].items():
            for k, v in config['settings']['cell_defaults'].items():
                if k not in cell:
                    config['cells'][name][k] = v
        config['settings'].pop('cell_defaults')

        # Validate the schema
        return cls.config_file_syntax.validate(config)


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
        j = syntax.json_schema("Charlib configuration file syntax")

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
                elif key == "$id":
                    poplist.append(key)
                # Remove empty required keywords
                elif key == "required" and value == []:
                    poplist.append(key)
                elif key == "anyOf":
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
