from charlib.characterizer.logic.functions import generate_yml

def generate_functions(args):
    """Generate YAML files for caching function-to-test-vector mappings"""
    generate_yml(args.expressions)
