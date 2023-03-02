from typing import Callable

from nespy.instructions import *
from nespy.addr_modes import *

class Operation():
    def __init__(self, opcode: int, name: str = "???", addr_mode: Callable = None, instruction: Callable = None, cycles: int = 0):
        self.opcode = opcode
        self.name = name
        self.addr_mode
        self.instruction = instruction
        self.cycles = cycles
    
    def run(self, cpu: Cmp6502):
        # set some util information that the instructions might use for special cases
        cpu.opcode = self.opcode
        cpu.addr_mode = self.addr_mode
        cpu.instruction = self.instruction

        ec1 = self.addr_mode(cpu)

        if self.addr_mode != IMP:
            # If we aren't in implied mode, read addr_abs into fetched
            cpu.fetch()

        ec2 = self.instruction(cpu)

        cpu.cycles += self.cycles

        # If both the addressing mode and instruction request an extra cycle, add it
        cpu.cycles += (ec1 & ec2)
