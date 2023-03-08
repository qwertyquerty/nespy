from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nespy.cmp_6502 import Cmp6502

# Addressing modes

# return 1 if the addressing mode needs an extra cycle because it crossed a page boundary

def IMP(cpu: Cmp6502) -> int:
    # just load a
    cpu.fetched = cpu.a
    return 0

def IMM(cpu: Cmp6502) -> int:
    # load the next byte
    cpu.addr_abs = cpu.pc
    cpu.pc += 1
    return 0

def ZP0(cpu: Cmp6502) -> int:
    # like IMM but zero paged
    cpu.addr_abs = cpu.bus.read(cpu.pc)
    cpu.pc += 1
    return 0

def ZPX(cpu: Cmp6502) -> int:
    # ZP0 with x as an offset
    cpu.addr_abs = (cpu.bus.read(cpu.pc) + cpu.x) & 0x00FF
    cpu.pc += 1
    return 0

def ZPY(cpu: Cmp6502) -> int:
    # ZP0 with y as an offset
    cpu.addr_abs = (cpu.bus.read(cpu.pc) + cpu.y) & 0x00FF
    cpu.pc += 1
    return 0

def REL(cpu: Cmp6502) -> int:
    # relative addressing
    addr_rel = cpu.bus.read(cpu.pc)
    cpu.pc += 1

    if addr_rel & 0x80:
        addr_rel |= 0xFF00
    
    cpu.addr_abs = cpu.pc + addr_rel
    
    return 0

def ABS(cpu: Cmp6502) -> int:
    # read next two bytes, load the address they point to
    cpu.addr_abs = cpu.bus.read(cpu.pc) | (cpu.bus.read(cpu.pc + 1) << 8)
    cpu.pc += 2
    return 0

def ABX(cpu: Cmp6502) -> int:
    # ABS with x as an offset
    lbyte = cpu.bus.read(cpu.pc)
    hbyte = cpu.bus.read(cpu.pc + 1)
    cpu.pc += 2

    cpu.addr_abs = ((hbyte << 8) | lbyte) + cpu.x

    return int((cpu.addr_abs & 0xFF00) != (hbyte << 8)) # if we changed pages, add extra clock cycle

def ABY(cpu: Cmp6502) -> int:
    # ABS with y as an offset
    lbyte = cpu.bus.read(cpu.pc)
    hbyte = cpu.bus.read(cpu.pc + 1)
    cpu.pc += 2

    cpu.addr_abs = ((hbyte << 8) | lbyte) + cpu.y

    return int((cpu.addr_abs & 0xFF00) != (hbyte << 8)) # if we changed pages, add extra clock cycle

def IND(cpu: Cmp6502) -> int:
    # indirect addressing, kind of like a double ABS
    # has a hardware bug
    lbyte = cpu.bus.read(cpu.pc)
    hbyte = cpu.bus.read(cpu.pc + 1)
    cpu.pc += 2

    ptr = (hbyte << 8) | lbyte

    # hardware bug, if on a page boundary unintended behavior happens
    if lbyte == 0x00FF:
        # Simulating the hardware bug
        cpu.addr_abs = (cpu.bus.read(ptr & 0xFF00) << 8) | cpu.bus.read(ptr + 0)
    else:
        # Otherwise behave normally
        cpu.addr_abs = (cpu.bus.read(ptr + 1) << 8) | cpu.bus.read(ptr + 0)

    return 0

def IZX(cpu: Cmp6502) -> int:
    # IND with an x offset added to the second pointers
    ptr = cpu.bus.read(cpu.pc)
    cpu.pc += 1
    lbyte = cpu.bus.read((ptr + cpu.x) & 0x00FF)
    hbyte = cpu.bus.read((ptr + cpu.x + 1) & 0x00FF)
    cpu.addr_abs = (hbyte << 8) | lbyte
    return 0

def IZY(cpu: Cmp6502) -> int:
    # IND with a y offset added to the final pointer
    ptr = cpu.bus.read(cpu.pc)
    cpu.pc += 1
    lbyte = cpu.bus.read(ptr & 0x00FF)
    hbyte = cpu.bus.read((ptr + 1) & 0x00FF)
    cpu.addr_abs = ((hbyte << 8) | lbyte) + cpu.y
    return int((cpu.addr_abs & 0xFF00) != (hbyte << 8)) # if wee changed pages, add extra clock cycle
