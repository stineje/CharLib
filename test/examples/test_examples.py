from charlib.characterizer.characterizer import Characterizer
from charlib.cli import utils

from pathlib import Path

def run(settings, cells):
    characterizer = Characterizer(**settings)
    for name, properties in utils.read_cell_configs(cells):
        characterizer.add_cell(name, properties)
    libtext = characterizer.characterize()

    libfile = characterizer.settings.results_dir / characterizer.library.file_name
    libfile.parent.mkdir(parents=True, exist_ok=True)
    with open(libfile, 'w') as f:
        f.write(str(libtext))

def test_ex_osu350_adders():
    config = utils.find_config('test/examples/ex_osu350_adders.yaml')
    run(config['settings'], config['cells'])

def test_ex_osu350_invx1():
    config = utils.find_config('test/examples/ex_osu350_invx1.yaml')
    run(config['settings'], config['cells'])

def test_ex_gf180_osu_9t():
    config = utils.find_config('test/examples/ex_gf180_osu_9t.yaml')
    run(config['settings'], config['cells'])

def test_ex_osu350_dffsr():
    from ex_osu350_dffsr import characterize_osu350_dffsr
    characterize_osu350_dffsr()
