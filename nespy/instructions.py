from nespy.cmp_6502 import Cmp6502
from nespy.addr_modes import *
#addess modes IMP(Implied), ACC (Accumaluator), IMM (Immediate), ZP0 (Zero Page), REL (Relative), ABS (Absolute), IND (Indirect)
def AND(cpu: Cmp6502) -> int:
    cpu.a &= cpu.fetched
    cpu.set_flag(cpu.flags.Z, cpu.a == 0x00)
    cpu.set_flag(cpu.flags.N, cpu.a & 0x80)

    return 1

def ASL(cpu: Cmp6502) -> int:
    t = cpu.fetched << 1

    cpu.set_flag(cpu.flags.C, (t & 0xFF00) > 0)
    cpu.set_flag(cpu.flags.Z, (t & 0x00FF) == 0x00)
    cpu.set_flag(cpu.flags.N, t & 0x80)

    if cpu.addr_mode == IMP:
        cpu.a = t & 0x00FF
    else:
        cpu.write(cpu.addr_abs, t & 0x00FF)
    
    return 0

def UNK(cpu: Cmp6502) -> int:
    # placeholder for opcodes that dont exist (but we still need to handle just in case)
    return 0
def CMP(cpu: Cmp6502) -> int: #compares A (Accumator with another memory value)
    return
def DEC(cpu: Cmp6502) -> int: #subtracts one from the value held at a spefic memory location (setting zero and negative flags appropriatly)
    cpu.set_flag(cpu.flags.C, cpu.a-1 > 0)
    cpu.set_flag(cpu.flags.Z, cpu.a-1 == 0)
    cpu.set_flag(cpu.flags.N, cpu.a-1 < 0)
    cpu.a -= 1
    return
#X and Y clones of this instructions
def INC(cpu: Cmp6502) -> int: #adds one to from the value at a spefic memory location
    #flags
    cpu.set_flag(cpu.flags.C, cpu.a+1 > 0)
    cpu.set_flag(cpu.flags.Z, cpu.a+1 == 0)
    cpu.set_flag(cpu.flags.N, cpu.a+1 < 0)
    cpu.a += 1
    return
#X and Y clones of this instructions
def JMP(cpu: Cmp6502) -> int: #sets the pc (program counter) to the addess specified
    return
def LDA(cpu: Cmp6502) -> int: #Loads specific memory into the accumator and sets flags appropriately
    if cpu.addr_mode == IMM:
        cpu.a = 
    if cpu.addr_mode == ZP0:
        cpu.a = cpu.read(0x00)
    if cpu.addr_mode == ZPX:
        cpu.a = cpu.read(0x00+ cpu.x)
    if cpu.addr_mode == ABS:
        cpu.a = cpu.read(cpu.addr_abs)
    if cpu.addr_mode == IZX:
        cpu.a = cpu.read(0x20+cpu.x)
    #for if correct to implement Adress modesABX,ABY, ABX, IZY and Clone Instructions LDY and LDX
    return cpu.a
def LDY(cpu: Cmp6502) -> int: #Load Y - Register (clone of above minus IMP and Y statements)
    return
def NOP(cpu: Cmp6502) -> None: #no changes just incrementing program counter
    cpu.cycles += 1
def STA(cpu: Cmp6502) -> None: # stores the content of the acculamator to a specific address based off address mode
    if cpu.addr_mode == ZP0:
        cpu.write(0x00, cpu.a)
    if cpu.addr_mode == ZPX:
        cpu.write(0x00+cpu.x, cpu.a) #this one confused me reading wikis about it
    if cpu.addr_mode == ABS:
        cpu.write(0x00+ 0x23, cpu.a)
    if cpu.addr_mode == IZX:
        cpu.write(cpu.read(0x20+cpu.x), cpu.a) #store accumulator to the address calculated by $20+ content of cpu.x 
    return 