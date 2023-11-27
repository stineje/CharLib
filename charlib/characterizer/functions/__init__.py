from pathlib import Path
import yaml
from .functions import Function

registered_functions = {}

with open(Path('charlib/characterizer/functions/functions.yml'), 'r') as file:
    functions = yaml.safe_load(file)
    for name in functions:
        registered_functions[name] = Function(**functions[name])
