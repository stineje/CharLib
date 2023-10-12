from pathlib import Path
import yaml
from .functions import Function

with open(Path('characterizer/functions/functions.yml'), 'r') as file:
    functions = yaml.safe_load(file)
    for name in functions:
        globals()[name] = Function(functions[name])
