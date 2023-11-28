import importlib
from pathlib import Path
import yaml
from .functions import Function

registered_functions = {}

with importlib.resources.open_text('charlib.characterizer.functions', 'functions.yml') as file:
    functions = yaml.safe_load(file)
    for name in functions:
        registered_functions[name] = Function(**functions[name])
