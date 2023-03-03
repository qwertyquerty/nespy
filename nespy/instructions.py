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

def DEC(cpu: Cmp6502) -> int:
    t = cpu.fetched - 1
    cpu.set_flag(cpu.flags.Z, (t & 0x00FF) == 0x00)
    cpu.set_flag(cpu.flags.N, t & 0x80)
    cpu.write(cpu.addr_abs, t & 0x00FF)

    return 0

def INC(cpu: Cmp6502) -> int:
    t = cpu.fetched + 1
    cpu.set_flag(cpu.flags.Z, (t & 0x00FF) == 0x00)
    cpu.set_flag(cpu.flags.N, t & 0x80)
    cpu.write(cpu.addr_abs, t & 0x00FF)

    return 0

def LDA(cpu: Cmp6502) -> int:
    cpu.a = cpu.fetched
    cpu.set_flag(cpu.flags.Z, cpu.a == 0x00)
    cpu.set_flag(cpu.flags.N, cpu.a & 0x80)

    return 1

def LDX(cpu: Cmp6502) -> int:
    cpu.x = cpu.fetched
    cpu.set_flag(cpu.flags.Z, cpu.x == 0x00)
    cpu.set_flag(cpu.flags.N, cpu.x & 0x80)

    return 1

def LDY(cpu: Cmp6502) -> int:
    cpu.y = cpu.fetched
    cpu.set_flag(cpu.flags.Z, cpu.y == 0x00)
    cpu.set_flag(cpu.flags.N, cpu.y & 0x80)

    return 1

def NOP(cpu: Cmp6502) -> None:
    # NOP has weird behavior on specific opcodes where it has potential to add a cycle on page boundary, specicaly on any ABX opcodes
    if cpu.addr_mode == ABX:
        return 1

    return 0

def STA(cpu: Cmp6502) -> None:
    cpu.write(cpu.addr_abs, cpu.a)

    return 0

def STX(cpu: Cmp6502) -> None:
    cpu.write(cpu.addr_abs, cpu.x)

    return 0

def STY(cpu: Cmp6502) -> None:
    cpu.write(cpu.addr_abs, cpu.y)

    return 0
