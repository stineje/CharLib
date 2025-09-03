registered_procedures = {}

def register(procedure):
    """Decorator to register a procedure"""
    registered_procedures[procedure.__name__] = procedure
    return procedure
