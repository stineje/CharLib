
import yaml
import os

from charlib.config.syntax import ConfigFile

def test_settings_default():
    """
    Tests default values of keywords under "settings"
    """

    cfg = None

    cfg_file = os.path.join(os.path.dirname(__file__), "test_settings_default.yml")
    with open(cfg_file, 'r') as f:
        cfg = yaml.safe_load(f)

    cfg = ConfigFile.validate(cfg)

    assert cfg["settings"]["lib_name"] == "unnamed_lib"

    un = cfg["settings"]["units"]
    assert un["time"] == "ns"
    assert un["voltage"] == "V"
    assert un["current"] == "uA"
    assert un["pulling_resistance"] == "Ohm"
    assert un["leakage_power"] == "nW"
    assert un["capacitive_load"] == "pF"
    assert un["energy"] == "fJ"

    nn = cfg["settings"]["named_nodes"]
    assert nn["vdd"]["name"] == "VDD"
    assert nn["vdd"]["voltage"] == 3.3
    assert nn["vss"]["name"] == "GND"
    assert nn["vss"]["voltage"] == 0
    assert nn["pwell"]["name"] == "VPW"
    assert nn["pwell"]["voltage"] == 0
    assert nn["nwell"]["name"] == "VNW"
    assert nn["nwell"]["voltage"] == 3.3

    assert cfg["settings"]["logic_thresholds"]["low"] == 0.2
    assert cfg["settings"]["logic_thresholds"]["high"] == 0.8
    assert cfg["settings"]["logic_thresholds"]["low_to_high"] == 0.5
    assert cfg["settings"]["logic_thresholds"]["high_to_low"] == 0.5

    assert cfg["settings"]["process"] == "typ"
    assert cfg["settings"]["temperature"] == 25

    # Operating conditions have no default
    # assert cfg["settings"]["operating_conditions"] == ""

    assert cfg["settings"]["multithreaded"] == True
    assert cfg["settings"]["results_dir"] == "results"
    assert cfg["settings"]["debug"] == False
    assert cfg["settings"]["debug_dir"] == "debug"
    assert cfg["settings"]["quiet"] == False
    assert cfg["settings"]["omit_on_failure"] == False

    assert cfg["settings"]["simulator"] == "ngspice-shared"

