
import yaml
import os

from charlib.config.syntax import ConfigFile

def test_settings_default():
    """
    Tests default values of keywords under "settings"
    """

    config = None

    config_file = os.path.join(os.path.dirname(__file__), "test_settings_default.yml")
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    config = ConfigFile.validate(config)
    settings = config["settings"]

    assert settings["lib_name"] == "unnamed_lib"

    units = settings["units"]
    assert units["time"] == "ns"
    assert units["voltage"] == "V"
    assert units["current"] == "uA"
    assert units["pulling_resistance"] == "Ohm"
    assert units["leakage_power"] == "nW"
    assert units["capacitive_load"] == "pF"
    assert units["energy"] == "fJ"

    nodes = settings["named_nodes"]
    assert nodes["primary_power"]["name"] == "VDD"
    assert nodes["primary_power"]["voltage"] == 3.3
    assert nodes["primary_ground"]["name"] == "VSS"
    assert nodes["primary_ground"]["voltage"] == 0
    assert nodes["pwell"]["name"] == "VPW"
    assert nodes["pwell"]["voltage"] == 0
    assert nodes["nwell"]["name"] == "VNW"
    assert nodes["nwell"]["voltage"] == 3.3

    assert settings["logic_thresholds"]["low"] == 20
    assert settings["logic_thresholds"]["high"] == 80
    assert settings["logic_thresholds"]["rising"] == 50
    assert settings["logic_thresholds"]["falling"] == 50

    assert settings["multithreaded"] == True
    assert settings["results_dir"] == "results"
    assert settings["debug"] == False
    assert settings["debug_dir"] == "debug"
    assert settings["omit_on_failure"] == False

