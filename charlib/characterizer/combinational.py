"""A Harness for combinational cells"""

from charlib.characterizer.harness import harness

class CombinationalHarness (Harness):
    """A CombinationalHarness captures configuration for testing a combinational cell."""

    def __init__(self, target_cell, test_vector) -> None:
        """Create a new CombinationalHarness."""
        super().__init__(target_cell, test_vector)
        # Error if we don't have a target input port
        if not self.target_in_port:
            raise ValueError(f'Unable to parse target input port from test vector {test_vector}')
