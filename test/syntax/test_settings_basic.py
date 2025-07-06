
import yaml
import os

from charlib.config.Syntax import ConfigFile

def test_settings1():

    cfg = None

    cfg_file = os.path.join(os.path.dirname(__file__), "test_settings_basic.yml")
    with open(cfg_file, 'r') as f:
        cfg = yaml.safe_load(f)

    cfg = ConfigFile.validate(cfg)

    assert cfg["settings"]["lib_name"] == "test_pdk"

    un = cfg["settings"]["units"]
    assert un["time"] == "fs"
    assert un["voltage"] == "mV"
    assert un["current"] == "uA"
    assert un["pulling_resistance"] == "kOhm"
    assert un["leakage_power"] == "pW"
    assert un["capacitive_load"] == "pF"
    assert un["energy"] == "aJ"

    assert cfg["settings"]["temperature"] == 74.2

    assert cfg["settings"]["logic_thresholds"]["low"] == 0.3
    assert cfg["settings"]["logic_thresholds"]["high"] == 0.7

    nn = cfg["settings"]["named_nodes"]
    assert nn["vdd"]["name"] == "VCC"
    assert nn["vdd"]["voltage"] == 1.8
    assert nn["vss"]["name"] == "VEE"
    assert nn["vss"]["voltage"] == 0
    assert nn["pwell"]["name"] == "VEE"
    assert nn["pwell"]["voltage"] == 0
    assert nn["nwell"]["name"] == "VCC"
    assert nn["nwell"]["voltage"] == 1.8

    assert cfg["settings"]["simulator"] == "ngspice-subprocess"

    lt = cfg["settings"]["logic_thresholds"]
    assert lt["low"] == 0.3
    assert lt["high"] == 0.7
    assert lt["low_to_high"] == 0.55
    assert lt["high_to_low"] == 0.45

    assert cfg["settings"]["process"] == "fast"
    assert cfg["settings"]["operating_conditions"] == "tst_ff_25c"
    assert cfg["settings"]["multithreaded"] == False
    assert cfg["settings"]["results_dir"] == "test_pdk_lib"
    assert cfg["settings"]["debug"] == True
    assert cfg["settings"]["quiet"] == False
    assert cfg["settings"]["omit_on_failure"] == False