import pytest

from charlib.cli.utils import find_config


@pytest.mark.parametrize('quiet', [True, False])
def test_invalid_cell_configuration_reports_schema_error(tmp_path, quiet):
    config_file = tmp_path / 'invalid.yaml'
    config_file.write_text('''cells:
  DFF:
    netlist: dff.sp
    models: []
    functions: ["Q <= D"]
    data_slews: [0.1]
    inputs: D
''')

    with pytest.raises(FileNotFoundError) as error:
        find_config(config_file, quiet=quiet)

    assert str(config_file) in str(error.value)
    assert 'inputs' in str(error.value)


def test_invalid_yaml_reports_parser_error(tmp_path):
    config_file = tmp_path / 'broken.yaml'
    config_file.write_text('cells: [unterminated')

    with pytest.raises(FileNotFoundError) as error:
        find_config(config_file)

    assert 'invalid YAML' in str(error.value)
    assert str(config_file) in str(error.value)


def test_missing_config_keeps_missing_file_message(tmp_path):
    config_file = tmp_path / 'missing.yaml'

    with pytest.raises(FileNotFoundError) as error:
        find_config(config_file)

    assert str(error.value) == f'No valid configuration found in {config_file}'
