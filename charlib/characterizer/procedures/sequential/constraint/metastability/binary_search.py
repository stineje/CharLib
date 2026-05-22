import PySpice

from charlib.characterizer import utils
from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.liberty import liberty
from charlib.liberty.library import LookupTable

@register('data_slews', 'clock_slews', 'metastability_constraint_load')
def metastability_binary_search_worst_case(cell, config, settings):
    """Find the minimum setup & hold time such that the cell can still register data."""
    for variation in config.variations('data_slews', 'clock_slews', 'metastability_constraint_load'):
        for path in cell.paths():
            yield (worst_case_setup_hold_constraint, cell, config, settings, variation, path)

def worst_case_setup_hold_constraint(cell, config, settings, variation, path):
    """Given a particular path through the cell, find the worst-case minimum setup & hold time.

    This method tests all nonmasking conditions which produce the state transition indicated in
    the `path` tuple with the given slew rate and capacitive load, then returns data for the
    worst-case (i.e. largest) setup & hold times.

    :param cell: A Cell object to test.
    :param config: A CellTestConfig object containing cell-specific test configuration details.
    :param settings: A CharacterizationSettings object containing library-wide configuration
                     details.
    :param variation: A dict containing test parameters for this configuration variation, such
                      as slew rates, loads, and constraint search bounds.
    :param path: A list in the format [input_port, input_transition, output_port,
                 output_transtition] describing the path under test in the cell.
    """
    [input_port, input_transition, output_port, output_transition] = path
    data_slew = variation['data_slews'] * settings.units.time
    clock_slew = variation['clock_slews'] * settings.units.time
    load = variation['metastability_constraint_load'] * settings.units.capacitance
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # Compute minimum setup & hold constraint for all nonmasking conditions
    # TODO: implement binary search for minimum setup/hold

    return cell.liberty # TODO
