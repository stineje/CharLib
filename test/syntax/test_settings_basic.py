
import yaml
import os

from charlib.config.syntax import ConfigFile

def test_settings_basic():
    """
    Tests available keywords under "settings"
    """

    config_file = os.path.join(os.path.dirname(__file__), "test_settings_basic.yml")
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    config = ConfigFile.validate(config)
    settings = config['settings']

    assert settings["lib_name"] == "test_pdk"

    units = settings["units"]
    assert units["time"] == "fs"
    assert units["voltage"] == "mV"
    assert units["current"] == "uA"
    assert units["pulling_resistance"] == "kOhm"
    assert units["leakage_power"] == "pW"
    assert units["capacitive_load"] == "pF"
    assert units["energy"] == "aJ"

    assert settings["temperature"] == 23.4
    assert settings["logic_thresholds"]["low"] == 0.3
    assert settings["logic_thresholds"]["high"] == 0.7

    nodes = settings["named_nodes"]
    assert nodes["primary_power"]["name"] == "VCC"
    assert nodes["primary_power"]["voltage"] == 1.8
    assert nodes["primary_ground"]["name"] == "VEE"
    assert nodes["primary_ground"]["voltage"] == 0
    assert nodes["pwell"]["name"] == "VPB"
    assert nodes["pwell"]["voltage"] == 0
    assert nodes["nwell"]["name"] == "VNB"
    assert nodes["nwell"]["voltage"] == 1.8

    assert settings["simulation"]["backend"] == "ngspice-subprocess"

    lt = settings["logic_thresholds"]
    assert lt["low"] == 0.3
    assert lt["high"] == 0.7
    assert lt["rising"] == 0.55
    assert lt["falling"] == 0.45

    assert settings["multithreaded"] == False
    assert settings["results_dir"] == "test_pdk_lib"
    assert settings["debug"] == True
    assert settings["debug_dir"] == "debug"
    assert settings["omit_on_failure"] == False
