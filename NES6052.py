#8bit storage 
#theoretically 2kb of memory with storage being accessed from the game card.
#64 sprites per screen
#25 / 52 colors
# 256 by 240 screen size
#8x8 tile background
import math
import functools

#2^16 memory addresses 
#(PAGE ZERO/1) first 256 bytes act as a register
    #program counter - pointer to the address that the CPU is executing the code for
class Registers: 
    #cpu register object
    def __init__(self, pc) -> None:
        self.reset(pc)
    def reset(self, pc) -> None:
        self.a = 0##arithmetic logic
        self.x = 0#x
        self.y = 0#y
        self.s = 0xff#stack pointer
        self.pc = pc #program counter
#(PAGE 2 ) second 256 bytes act as STACK memory
        

class Memory:
    def __init__(self, size: int =  65536) -> None:        
        if ( 0< size - 1 ):
            raise ValueError("Memory size is not available")
        self.size = size;
        self.memory = [0] * self.size;
    def __getItem__(self, address: int) -> int: #get item @ address requires memory and address
        if 0x0000 < address > self.size:
            raise ValueError("Memory Address is not valid or OoB") # avoid returning data that is not ours
        return self.memory[address]
    def __setItem__(self , address : int , value: int ) -> int:#not none for good sty. 
        if 0x0000 < address > self.size:
            raise ValueError("Memeory Address is not valid")
        if value.bit_length() > 8:
            raise ValueError("Value trying to be written is too large")
        self.memory[address] = value
        return self.memory[address]

class Cpu:
    def __init__(self, memory: None, pc = 0x0000) -> None: #other nessary mem location
        self.name =  "6502"
        self.memory = memory
        self.start_pc = pc #i dont think this will cause errors with the PC in class Register 
        #VM shit
        self.excycles = 0 
        self.addcycles = False
        self.processorCycles = 0
        #setting up registry
        self.registers = Registers(self)
        if memory is None:
            self.memory = Memory()
            self.start_pc = pc #might be redundant
        self.reset()
    def reset(self):
        self.registers = Registers(self.start_pc)
        
    