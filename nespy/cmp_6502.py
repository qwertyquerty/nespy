from typing import Callable

from nespy.operations import OPCODE_LOOKUP

class Cmp6502():
    class flags:
        C = (1 << 0) # carry
        Z = (1 << 1) # zero
        I = (1 << 2) # interrupt disable
        D = (1 << 3) # decimal
        B = (1 << 4) # break
        U = (1 << 5) # unused
        V = (1 << 6) # overflow
        N = (1 << 7) # negative
    
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
    instruction: Callable = None # current instruction
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
        self.fetched = self.read(self.addr_abs)
    
    def set_flag(self, flag: int, val: bool):
        if val:
            self.status |= flag
        else:
            self.status &= ~flag
    
    def read(self, addr: int) -> int:
        return self.bus.read(addr, read_only = False)

    def write(self, addr: int, value: int) -> None:
        self.bus.write(addr, value)

    def clock(self) -> None:
        if self.cycles == 0: # preivous instruction done, we're ready for the next instruction
            self.opcode = self.read(self.pc) # read opcode at the program counter pointer
            
            self.status |= self.flags.U # for some reason this needs to be true

            self.pc = (self.pc + 1) & 0xFFFF # increment program counter in bounds

            operation = OPCODE_LOOKUP[self.opcode] # look up the instruction from the opcode lookup table
            operation.run(self) # and run it
        
            self.status |= self.flags.U # for some reason this needs to be true

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
        self.status = 0x00 | self.flags.U

        # read FFFC and FFFD, these addresses hold the value for the program counter start
        self.pc = (self.read(0xFFFD) << 8) | self.read(0xFFFC)
        
        # reset addressing mode util
        self.fetched = 0x00
        self.addr_abs = 0x0000

        # a reset takes 8 cycles to run
        self.cycles = 8

    def interrupt_request(self) -> None:
        if not (self.status | self.flags.I): # make sure interrupts aren't disabled
            self.write(0x0100 + self.s, (self.pc >> 8) & 0x00FF)
            self.s = (self.s - 1) & 0xFF
            self.write(0x0100 + self.s, self.pc & 0x00FF)
            self.s = (self.s - 1) & 0xFF
        
            self.status &= ~self.flags.B
            self.status |= self.flags.U
            self.status |= self.flags.I

            self.write(0x0100 + self.s, self.status)

            self.s = (self.s - 1) & 0xFF
            self.pc = (self.read(0xFFFF) << 8) | self.read(0xFFFE)
    
            # an interrupt request takes 7 cycles
            self.cylces = 7
    
    def non_maskable_interrupt(self) -> None:
        self.write(0x0100 + self.s, (self.pc >> 8) & 0x00FF)
        self.s = (self.s - 1) & 0xFF
        self.write(0x0100 + self.s, self.pc & 0x00FF)
        self.s = (self.s - 1) & 0xFF
    
        self.status &= ~self.flags.B
        self.status |= self.flags.U
        self.status |= self.flags.I

        self.write(0x0100 + self.s, self.status)

        self.s = (self.s - 1) & 0xFF
        self.pc = (self.read(0xFFFB) << 8) | self.read(0xFFFA)

        # an NMI takes 8 cycles
        self.cylces = 8
