import pytest
from schema import SchemaError

from charlib.config.syntax import ConfigFile


def make_config(criterion=None):
    cell = {
        'netlist': 'inverter.spice',
        'models': [],
        'functions': ['Y=!A'],
        'data_slews': [0.1],
    }
    if criterion is not None:
        cell['charge_integration_criterion'] = criterion
    return {'settings': {}, 'cells': {'INV': cell}}


def test_charge_integration_criterion_defaults_to_average():
    config = ConfigFile.validate(make_config())
    assert config['cells']['INV']['charge_integration_criterion'] == 'average'


@pytest.mark.parametrize('criterion', ['average', 'min', 'max'])
def test_charge_integration_criterion_accepts_supported_values(criterion):
    config = ConfigFile.validate(make_config(criterion))
    assert config['cells']['INV']['charge_integration_criterion'] == criterion


def test_charge_integration_criterion_rejects_unknown_value():
    with pytest.raises(SchemaError):
        ConfigFile.validate(make_config('median'))
