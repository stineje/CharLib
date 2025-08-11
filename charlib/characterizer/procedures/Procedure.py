from typing import Callable

class Procedure:
    def __init__(self, task: Callable, *args):
        self.task = task
        self.params = args

    def __call__(self):
        """Execute self.task(self.params*)"""
        return self.task(*self.params)
