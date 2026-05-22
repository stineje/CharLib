registered_procedures = {}

def register(*parameters):
    """
    Decorator to register a procedure (and any required parameters) with the Characterizer.

    If used as a decorator with string arguments, each arg will be added to the list of supported
    parameters for CellTestConfig.
    """
    # When used without parentheses: @register
    if len(parameters) == 1 and callable(parameters[0]):
        procedure = parameters[0]
        registered_procedures[procedure.__name__] = {
            'callable': procedure,
            'parameters': ()
        }
        return procedure

    # When used with parentheses: @register('fizz', 'buzz')
    def decorator_with_args(procedure):
        registered_procedures[procedure.__name__] = {
            'callable': procedure,
            'parameters': parameters
        }
        return procedure
    return decorator_with_args

class ProcedureFailedException(Exception):
    """Indicates that the procedure failed for the reason specified in the message."""
    pass
