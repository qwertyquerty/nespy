from typing import Callable

class Operation():
    def __init__(self, name: str = "???", instruction: Callable = None, cycles: int = 0):
        self.name = name
        self.instruction = instruction
        self.cycles = cycles
