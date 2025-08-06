from typing import Callable

class Procedure:
    def __init__(self, task: Callable, params: list):
        self.task = task
        self.params = params

    def __call__(self):
        """Execute self.task(self.params*)"""
        return self.task(*self.params)
