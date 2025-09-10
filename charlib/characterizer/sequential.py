"""A Harness for Sequential cells"""

from charlib.characterizer.Harness import Harness, PinTestBinding

class SequentialHarness (Harness):
    def __init__(self, test_manager, pin_state_map: dict) -> None:
        # Parse internal storage states, clock, set, and reset out of pin mapping
        # Note that set and reset are optional, but must be provided if present
        # on the target cell
        self.set = None
        self.reset = None
        self.clock = PinTestBinding(test_manager.clock, pin_state_map[test_manager.clock.name])
        pin_state_map[test_manager.clock.name] = 'ignore'
        # Set up Reset
        if test_manager.reset:
            self.reset = PinTestBinding(test_manager.reset, pin_state_map[test_manager.reset.name])
            pin_state_map[test_manager.reset.name] = 'ignore'
        # Set up Set
        if test_manager.set:
            self.set = PinTestBinding(test_manager.set, pin_state_map[test_manager.set.name])
            pin_state_map[test_manager.set.name] = 'ignore'
        # TODO: handle flop internal states
        self.flops = []
        super().__init__(test_manager, pin_state_map)

    def short_str(self):
        harness_str = f'{self.clock.pin.name}={self.clock.state} {super().short_str()}'
        if self.set:
            harness_str += f' {self.set.pin.name}={self.set.state}'
        if self.reset:
            harness_str += f' {self.reset.pin.name}={self.reset.state}'
        return harness_str

    @property
    def set_direction(self) -> str:
        if not self.set:
            return None
        return self.set.direction

    @property
    def reset_direction(self) -> str:
        if not self.reset:
            return None
        return self.reset.direction

    def invert_set_reset(self):
        self.set.state = self.set.state[::-1] if self.set.state else None
        self.reset.state = self.reset.state[::-1] if self.reset.state else None

    @property
    def timing_sense_constraint(self) -> str:
        # TODO: Check that this is correct
        return f'{self.in_direction}_constraint'

    def _timing_type_with_mode(self, mode) -> str:
        # Determine from target input and direction
        if self.set_direction or self.reset_direction:
            # We're targeting set or reset
            if mode == 'recovery':
                if self.in_direction == 'rise':
                    return f'{mode}_rising'
                else:
                    return f'{mode}_falling'
            elif mode == 'removal':
                if self.in_direction == 'rise':
                    return f'{mode}_falling'
                else:
                    return f'{mode}_rising'
            else:
                return None
        elif not self.target_in_port.pin.name in [*self.flops]:
            # We're targeting an input port
            if mode == 'clock':
                if self.clock.state == '0101':
                    return 'rising_edge'
                else:
                    return 'falling_edge'
            elif mode in ['hold', 'setup']:
                if self.in_direction == 'rise':
                    return f'{mode}_rising'
                else:
                    return f'{mode}_falling'
        # If we get here, most likely the harness isn't configured correctly
        raise ValueError(f'Unable to determine timing type for mode "{mode}"')

    @property
    def timing_type_hold(self) -> str:
        return self._timing_type_with_mode('hold')

    @property
    def timing_type_setup(self) -> str:
        return self._timing_type_with_mode('setup')

    @property
    def timing_type_recovery(self) -> str:
        return self._timing_type_with_mode('recovery')

    @property
    def timing_type_removal(self) -> str:
        return self._timing_type_with_mode('removal')

    @property
    def timing_type_clock(self) -> str:
        return self._timing_type_with_mode('clock')

    @property
    def timing_when(self) -> str:
        if self.in_direction == 'rise':
            return self.target_in_port
        else:
            return f'!{self.target_in_port}'

    def plot_energy(self, settings, slews, loads, cell_name):
        pass
