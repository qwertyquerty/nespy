from nespy.cmp_6502 import Cmp6502
from nespy.addr_modes import *

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
