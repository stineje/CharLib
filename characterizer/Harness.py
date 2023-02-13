class Harness:
    """Characterization parameters for one path through a cell
    
    A Harness defines characterization parameters from one input to one
    output of a standard cell circuit."""

    def __init__(self, target_in_port, target_out_port, timing_sense, direction) -> None:
        self._target_in_port = target_in_port   # This pin will change while other inputs will be held stable
        self._target_out_port = target_out_port # This output will be measured for an expected result
        self._timing_type = timing_sense        # Timing on positive unate, negative unate, or none
        self._direction = direction             # Rising or falling

        @property
        def timing_type(self) -> str:
            return "combinational"
