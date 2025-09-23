registered_procedures = {}

def register(procedure):
    """Decorator to register a procedure"""
    registered_procedures[procedure.__name__] = procedure
    return procedure

class ProcedureFailedException(Exception):
    """Indicates that the procedure failed for the reason specified in the message."""
    pass
