from typing import Callable

from nespy.const import *
from nespy.operations import OPCODE_LOOKUP, IMP

class Cmp6502():
    a: int = 0x00 # a register
    x: int = 0x00 # x register
    y: int = 0x00 # y register
    pc: int = 0x0000 # program counter
    s: int = 0x00 # stack pointer
    status: int = 0x00 # status register

    # these are util used for addressing modes to store the data that they fetch or represent
    fetched: int = 0x00 # stores a byte fetched by the addressing mode read from addr_abs
    addr_abs: int = 0x0000 # address fetched from, set by addressing modes
    addr_mode: Callable = None # current addressing mode
    opcode: int = 0x00 # current opcode

    # these aren't used for emulation but are used for interface / debugging
    clock_count: int = 0 # how many cycles have passed since reset

    # this is used to time instructions, it will be incremented by the cycle count of an instruction
    # when an instruction is run and then will be decremented every clock cycle to zero before
    # the next instruction can be run
    cycles = 0

    def __init__(self, bus):
        self.bus = bus
    
    def fetch(self) -> int:
        if self.addr_mode != IMP:
            self.fetched = self.bus.read(self.addr_abs)
    
    def set_flag(self, flag: int, val: bool):
        if val == 0:
            self.status &= ~flag
        else:
            self.status |= flag
    
    def clock(self) -> None:
        if self.cycles == 0: # preivous instruction done, we're ready for the next instruction
            self.opcode = self.bus.read(self.pc) # read opcode at the program counter pointer
            
            self.status |= U # for some reason this needs to be true

            self.pc = (self.pc + 1) & 0xFFFF # increment program counter in bounds

            OPCODE_LOOKUP[self.opcode].run(self) # look up the instruction from the opcode lookup table, run it

            self.status |= U # for some reason this needs to be true

        self.cycles -= 1
        self.clock_count += 1
    
    def reset(self) -> None:
        """
        Equivalent to replugging the NES or hitting the reset button
        """
        # reset non-emulation related variables
        self.clock_count = 0

        # reset registers to default states
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.s = 0xFD
        self.status = 0x00 | U

        # read FFFC and FFFD, these addresses hold the value for the program counter start
        self.pc = (self.bus.read(0xFFFD) << 8) | self.bus.read(0xFFFC)
        
        # reset addressing mode util
        self.fetched = 0x00
        self.addr_abs = 0x0000

        # a reset takes 8 cycles to run
        self.cycles = 8

    def interrupt_request(self) -> None:
        if not (self.status | I): # make sure interrupts aren't disabled
            self.write(0x0100 + self.s, (self.pc >> 8) & 0x00FF)
            self.s = (self.s - 1) & 0xFF
            self.write(0x0100 + self.s, self.pc & 0x00FF)
            self.s = (self.s - 1) & 0xFF
        
            self.status &= ~B
            self.status |= U
            self.status |= I

            self.write(0x0100 + self.s, self.status)

            self.s = (self.s - 1) & 0xFF
            self.pc = (self.bus.read(0xFFFF) << 8) | self.bus.read(0xFFFE)
    
            # an interrupt request takes 7 cycles
            self.cylces = 7
    
    def non_maskable_interrupt(self) -> None:
        self.write(0x0100 + self.s, (self.pc >> 8) & 0x00FF)
        self.s = (self.s - 1) & 0xFF
        self.write(0x0100 + self.s, self.pc & 0x00FF)
        self.s = (self.s - 1) & 0xFF
    
        self.status &= ~B
        self.status |= U
        self.status |= I

        self.write(0x0100 + self.s, self.status)

        self.s = (self.s - 1) & 0xFF
        self.pc = (self.bus.read(0xFFFB) << 8) | self.bus.read(0xFFFA)

        # an NMI takes 8 cycles
        self.cylces = 8
