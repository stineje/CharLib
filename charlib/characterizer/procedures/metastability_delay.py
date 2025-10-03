import PySpice

from charlib.characterizer import utils
from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.liberty import liberty
from charlib.liberty.library import LookupTable

@register
def metastability_binary_search_worst_case(cell, config, settings):
    """Find the minimum setup & hold time such that the cell can still register data."""
    for variation in config.variations('data_slews', 'loads', ''):
        for path in cell.paths():
            yield (worst_case_setup_hold_constraint, cell, config, settings, variation, path)

def worst_case_setup_hold_constraint(cell, config, settings, variation, path):
    """Given a particular path through the cell, find the worst-case minimum setup & hold time.

    This method tests all nonmasking conditions which produce the state transition indicated in
    the `path` tuple with the given slew rate and capacitive load, then returns data for the
    worst-case (i.e. largest) setup & hold times. Much like combinational_worst_case, this gives an
    overly pessimistic estimate of the constraint.

    :param cell: A Cell object to test.
    :param config: A CellTestConfig object containing cell-specific test configuration details.
    :param settings: A CharacterizationSettings object containing library-wide configuration
                     details.
    :param variation: A dict containing test parameters for this configuration variation, such
                      as slew rates, loads, and constraint search bounds.
    :param path: A list in the format [input_port, input_transition, output_port,
                 output_transtition] describing the path under test in the cell.
    """
    [input_port, _, output_port, _] = path
    data_slew = variation['data_slew'] * settings.units.time
    load = variation['load'] * settings.units.capacitance
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # Compute minimum setup & hold constraint for all nonmasking conditions
    analyses = []
    measurement_names = set()
    for state_map in cell.nonmasking_conditions_for_path(*path):
        # Build the test circuit
        circuit = utils.init_circuit('seq_setup_hold_search', cell.netlist, config.models)
        circuit.V('dd', 'vdd', circuit.gnd, vdd)
        circuit.V('ss', 'vss', circuit.gnd, vss)

        # Initialize device under test and wire up ports
        # TODO:
        # Clear any existing state
        # Trigger the desired state change

    return cell.liberty # TODO
