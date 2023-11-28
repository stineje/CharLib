import importlib
from pathlib import Path
import yaml
from .functions import Function

registered_functions = {}

with importlib.resources.as_file(importlib.resources.files('resources') / 'functions.yml') as file:
    functions = yaml.safe_load(file.open('rb'))
    for name in functions:
        registered_functions[name] = Function(**functions[name])
