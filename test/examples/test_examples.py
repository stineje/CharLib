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

def test_examples():
    for file in utils.find_yaml_files(Path(__file__).resolve().parent):
        if file.name.startswith("ex"):
            config = utils.find_config(file)
            run(config['settings'], config['cells'])

