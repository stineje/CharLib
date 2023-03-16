import os, shutil

from characterizer.LibrarySettings import LibrarySettings
from characterizer.LogicCell import LogicCell, SequentialCell
from characterizer.char_comb import runCombinational
from characterizer.char_seq import *

class Characterizer:
    """Main object of Charlib. Keeps track of settings, cells, and results."""
    
    def __init__(self) -> None:
        self.settings = LibrarySettings()
        self.cells = []
        self.num_files_generated = 0

    def __str__(self) -> str:
        lines = []
        lines.append('Library settings:')
        for line in str(self.settings).split('\n'):
            lines.append(f'    {line}')
        lines.append('Cells:')
        for cell in self.cells:
            for line in str(cell):
                lines.append(f'    {line}')
        return '\n'.join(lines)

    def target_cell(self) -> LogicCell:
        """Get last cell"""
        return self.cells[-1]

    def add_cell(self, name, in_ports, out_ports, function):
        # Create a new logic cell
        self.cells.append(LogicCell(name, in_ports, out_ports, function))

    def add_flop(self, name, in_ports, out_ports, clock_pin, set_pin, reset_pin, flops, functions):
        # Create a new sequential cell
        self.cells.append(SequentialCell(name, in_ports, out_ports, clock_pin, set_pin, reset_pin, flops, functions))

    def initialize_work_dir(self):
        if self.settings.run_sim:
            # Clear out the old work_dir if it exists
            if self.settings.work_dir.exists() and self.settings.work_dir.is_dir():
                shutil.rmtree(self.settings.work_dir)
            self.settings.work_dir.mkdir()
        else:
            print("Save previous working directory and files")

    def characterize(self, cell: LogicCell = None):
        """Characterize a single cell"""
        os.chdir(self.settings.work_dir)

        if isinstance(cell, SequentialCell):
            pass # TODO: runSequential(self.settings, cell, cell.test_vectors)
        elif isinstance(cell, LogicCell):
            runCombinational(self.settings, cell, cell.test_vectors)
        else:
            raise ValueError('Unrecognized cell type')

    def print_msg(self, message: str):
        if not self.settings.suppress_message:
            print(message)
    
    def print_sim(self, message: str):
        if not self.settings.suppress_sim_message:
            print(f'SIM: {message}')
    
    def print_debug(self, message: str):
        if not self.settings.suppress_debug_message:
            print(f'DEBUG: {message}')