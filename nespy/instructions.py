from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nespy.cmp_6502 import Cmp6502

from nespy.addr_modes import *
from nespy.const import *

def ADC(cpu: Cmp6502, addr_abs) -> int:
    fetched = cpu.fetch()

    t = cpu.a + fetched + bool(cpu.status & C)

    cpu.set_flag(C, t > 0xFF) # set carry bit since result is greater than 0xFF
    cpu.set_flag(Z, not (t & 0xFF)) # set zero bit if the actual resulting value is 0 (regardless of carry)
    cpu.set_flag(V, (~(cpu.a ^ fetched) & (cpu.a ^ t)) & 0x80) # wacky logic for signed carry bit
    cpu.set_flag(N, t & 0x80)

    cpu.a = t & 0xFF

    return 1

def SBC(cpu: Cmp6502, addr_abs) -> int:
    fetched = cpu.fetch()
    
    t = cpu.a + (fetched ^ 0xFF) + bool(cpu.status & C) # fetched is inverted using xor

    cpu.set_flag(C, t & 0xFF00) # set carry bit since result is greater than 0xFF
    cpu.set_flag(Z, not (t & 0xFF)) # set zero bit if the actual resulting value is 0 (regardless of carry)
    cpu.set_flag(V, ((t ^ cpu.a) & (t ^ (fetched ^ 0xFF))) & 0x80) # wacky logic for signed carry bit
    cpu.set_flag(N, t & 0x80)

    cpu.a = t & 0xFF

    return 1

def AND(cpu: Cmp6502, addr_abs) -> int:    
    cpu.a &= cpu.fetch()
    cpu.set_flag(Z, not cpu.a)
    cpu.set_flag(N, cpu.a & 0x80)

    return 1

def ASL(cpu: Cmp6502, addr_abs) -> int:    
    t = (cpu.fetch() << 1)

    cpu.set_flag(C, t & 0xFF00)
    cpu.set_flag(Z, not (t & 0xFF))
    cpu.set_flag(N, t & 0x80)

    if cpu.addr_mode is IMP:
        cpu.a = t
    else:
        cpu.bus.write(cpu.addr_abs, t)
    
    return 0

def BRK(cpu: Cmp6502, addr_abs) -> int: # program sourced interrupt
    cpu.pc = (cpu.pc + 1) & 0xFFFF
    cpu.bus.read(cpu.pc)

    cpu.status |= I
    cpu.bus.write(0x0100 + cpu.s, (cpu.pc >> 8) & 0xFF)
    cpu.bus.write(0x0100 + cpu.s - 1, cpu.pc & 0xFF)
    cpu.bus.write(0x0100 + cpu.s - 2, cpu.status | (B | U))

    cpu.s = (cpu.s - 3) & 0xFF

    cpu.status &= ~B

    cpu.pc = (cpu.bus.read(0xFFFF) << 8) | cpu.bus.read(0xFFFE)

    return 0

def CLC(cpu: Cmp6502, addr_abs) -> int:
    cpu.status &= ~C
    return 0

def CLD(cpu: Cmp6502, addr_abs) -> int:
    cpu.status &= ~D
    return 0

def CLI(cpu: Cmp6502, addr_abs) -> int:
    cpu.status &= ~I
    return 0

def CLV(cpu: Cmp6502, addr_abs) -> int:
    cpu.status &= ~V
    return 0

def SEC(cpu: Cmp6502, addr_abs) -> int:
    cpu.status |= C
    return 0

def SED(cpu: Cmp6502, addr_abs) -> int:
    cpu.status |= D
    return 0

def SEI(cpu: Cmp6502, addr_abs) -> int:
    cpu.status |= I
    return 0

def CMP(cpu: Cmp6502, addr_abs) -> int:
    fetched = cpu.fetch()
    
    t = cpu.a - fetched
    cpu.set_flag(Z, not (t & 0xFF))
    cpu.set_flag(C, cpu.a >= fetched)
    cpu.set_flag(N, t & 0x80) 
    
    return 1

def CPX(cpu: Cmp6502, addr_abs) -> int:
    fetched = cpu.fetch()
    
    t = cpu.x - fetched
    cpu.set_flag(Z, not t)
    cpu.set_flag(C, cpu.x >= fetched)
    cpu.set_flag(N, t & 0x80) 
    
    return 0

def CPY(cpu: Cmp6502, addr_abs) -> int:
    fetched = cpu.fetch()
    
    t = cpu.y - fetched
    cpu.set_flag(Z, not t)
    cpu.set_flag(C, cpu.y >= fetched)
    cpu.set_flag(N, t & 0x80) 
    
    return 0

def DEC(cpu: Cmp6502, addr_abs) -> int:
    t = cpu.fetch() - 1
    cpu.set_flag(Z, not t)
    cpu.set_flag(N, t & 0x80)
    cpu.bus.write(cpu.addr_abs, t)

    return 0

def DEX(cpu: Cmp6502, addr_abs) -> int:
    cpu.x = (cpu.x - 1) & 0xFF
    cpu.set_flag(Z, not cpu.x)
    cpu.set_flag(N, cpu.x & 0x80)

    return 0

def DEY(cpu: Cmp6502, addr_abs) -> int:
    cpu.y = (cpu.y - 1) & 0xFF
    cpu.set_flag(Z, not cpu.y)
    cpu.set_flag(N, cpu.y & 0x80)

    return 0

def EOR(cpu: Cmp6502, addr_abs) -> int:
    cpu.a ^= cpu.fetch()
    cpu.set_flag(Z, not cpu.a)
    cpu.set_flag(N, cpu.a & 0x80)

    return 1

def ORA(cpu: Cmp6502, addr_abs) -> int:
    cpu.a |= cpu.fetch()
    cpu.set_flag(Z, not cpu.a)
    cpu.set_flag(N, cpu.a & 0x80)

    return 1

def INC(cpu: Cmp6502, addr_abs) -> int:
    t = (cpu.fetch() + 1) & 0xFF
    cpu.set_flag(Z, not t)
    cpu.set_flag(N, t & 0x80)
    cpu.bus.write(cpu.addr_abs, t)

    return 0

def INX(cpu: Cmp6502, addr_abs) -> int:
    cpu.x = (cpu.x + 1) & 0xFF
    cpu.set_flag(Z, not cpu.x)
    cpu.set_flag(N, cpu.x & 0x80)

    return 0

def INY(cpu: Cmp6502, addr_abs) -> int:
    cpu.y = (cpu.y + 1) & 0xFF
    cpu.set_flag(Z, not cpu.y)
    cpu.set_flag(N, cpu.y & 0x80)
    
    return 0

def JMP(cpu: Cmp6502, addr_abs) -> int:
    cpu.pc = cpu.addr_abs
    return 0

def JSR(cpu: Cmp6502, addr_abs) -> int:
    t = (cpu.pc - 1) & 0xFFFF

    cpu.bus.write(0x0100 + cpu.s, (t >> 8) & 0xFF)
    cpu.bus.write(0x0100 + cpu.s - 1, t & 0xFF)

    cpu.s = (cpu.s - 2) & 0xFF

    cpu.pc = cpu.addr_abs

    return 0

def LDA(cpu: Cmp6502, addr_abs) -> int:
    cpu.a = cpu.fetch()
    cpu.set_flag(Z, not cpu.a)
    cpu.set_flag(N, cpu.a & 0x80)

    return 1

def LDX(cpu: Cmp6502, addr_abs) -> int:
    cpu.x = cpu.fetch()
    cpu.set_flag(Z, not cpu.x)
    cpu.set_flag(N, cpu.x & 0x80)

    return 1

def LDY(cpu: Cmp6502, addr_abs) -> int:
    cpu.y = cpu.fetch()
    cpu.set_flag(Z, not cpu.y)
    cpu.set_flag(N, cpu.y & 0x80)

    return 1

def NOP(cpu: Cmp6502, addr_abs) -> int:
    # NOP has weird behavior on specific opcodes where it has potential to add a cycle on page boundary, specicaly on any ABX opcodes
    if cpu.addr_mode is ABX:
        return 1

    return 0


def PHA(cpu: Cmp6502, addr_abs) -> int: #pushes the content of the Accumulator onto the stack structure
    cpu.bus.write(0x0100 + cpu.s, cpu.a)
    cpu.s = (cpu.s - 1) & 0xFF
    return 0

def PHP(cpu: Cmp6502, addr_abs) -> int: 
    cpu.bus.write(0x0100 + cpu.s, cpu.status | (B|U))
    cpu.status &= ~(B|U)
    cpu.s = (cpu.s - 1) & 0xFF

    return 0

def PLA(cpu: Cmp6502, addr_abs) -> int:
    cpu.s = (cpu.s + 1) & 0xFF
    cpu.a = cpu.bus.read(0x0100 + cpu.s)
    cpu.set_flag(Z, not cpu.a)
    cpu.set_flag(N, cpu.a & 0x80)

    return 0

def PLP(cpu: Cmp6502, addr_abs) -> int:
    cpu.s = (cpu.s + 1) & 0xFF
    cpu.status = cpu.bus.read(0x100 + cpu.s)
    cpu.status |= U

    return 0

def RTI(cpu: Cmp6502, addr_abs) -> None:
    cpu.bus.read(cpu.pc) # dummy fetch

    cpu.s = (cpu.s + 1) & 0xFF
    cpu.status = cpu.bus.read(0x0100 + cpu.s)
    cpu.status &= ~(B|U)

    cpu.pc = cpu.bus.read(0x0100 + cpu.s + 1) | (cpu.bus.read(0x0100 + cpu.s + 2) << 8)
    cpu.s = (cpu.s + 2) & 0xFF

    return 0

def RTS(cpu: Cmp6502, addr_abs) -> None:
    cpu.bus.read(cpu.pc) # dummy fetch

    cpu.pc = ((cpu.bus.read(0x0100 + cpu.s + 1) | (cpu.bus.read(0x0100 + cpu.s + 2) << 8)) + 1) & 0xFFFF
    cpu.s = (cpu.s + 2) & 0xFF

    return 0

def STA(cpu: Cmp6502, addr_abs) -> None:
    cpu.bus.write(cpu.addr_abs, cpu.a)
    return 0

def STX(cpu: Cmp6502, addr_abs) -> None:
    cpu.bus.write(cpu.addr_abs, cpu.x)
    return 0

def STY(cpu: Cmp6502, addr_abs) -> None:
    cpu.bus.write(cpu.addr_abs, cpu.y)
    return 0

def TAX(cpu: Cmp6502, addr_abs) -> int:
    #transfers accumulator's value to X
    cpu.x = cpu.a
    cpu.set_flag(Z, not cpu.x)
    cpu.set_flag(N, cpu.x & 0x80)    

    return 0

def TXA(cpu: Cmp6502, addr_abs) -> int:
    #transers X to A
    cpu.a = cpu.x
    cpu.set_flag(Z, not cpu.a)
    cpu.set_flag(N, cpu.a & 0x80)    

    return 0

def TAY(cpu: Cmp6502, addr_abs) -> int:
    #transers accumulator's value to Y
    cpu.y = cpu.a
    cpu.set_flag(Z, not cpu.y)
    cpu.set_flag(N, cpu.y & 0x80)    

    return 0

def TYA(cpu: Cmp6502, addr_abs) -> int:
    #transers Y to A
    cpu.a = cpu.y
    cpu.set_flag(Z, not cpu.a)
    cpu.set_flag(N, cpu.a & 0x80)    

    return 0

def TSX(cpu: Cmp6502, addr_abs) -> int:
    cpu.x = cpu.s
    cpu.set_flag(Z, not cpu.x)
    cpu.set_flag(N, cpu.x & 0x80)    

    return 0

def TXS(cpu: Cmp6502, addr_abs) -> int:
    cpu.s = cpu.x
    return 0

def ROL(cpu: Cmp6502, addr_abs) -> int: #moves accumator left a bit 
    fetched = cpu.fetch()
    
    t = (bool(cpu.status & C) | (fetched << 1)) & 0xFF
    cpu.set_flag(N, t & 0x80)
    cpu.set_flag(Z, not t)
    cpu.set_flag(C, fetched & 0x80)

    if cpu.addr_mode is IMP:
        cpu.a = t
    else:
        cpu.bus.write(cpu.addr_abs, t)

    return 0

def ROR(cpu: Cmp6502, addr_abs) -> int:
    fetched = cpu.fetch()
    
    t = (bool(cpu.status & C) << 7) | (fetched >> 1)

    cpu.set_flag(C, fetched & 0x01)
    cpu.set_flag(Z, not t)
    cpu.set_flag(N, t & 0x80)

    if cpu.addr_mode is IMP:
        cpu.a = t
    else:
        cpu.bus.write(cpu.addr_abs, t)

    return 0

def LSR(cpu: Cmp6502, addr_abs) -> int:
    fetched = cpu.fetch()
    
    t = fetched >> 1
    
    cpu.set_flag(N, t & 0x80)
    cpu.set_flag(Z, not t)
    cpu.set_flag(C, fetched & 0x01)

    if cpu.addr_mode is IMP:
        cpu.a = t
    else:
        cpu.bus.write(cpu.addr_abs, t)
    
    return 0
    

def BIT(cpu: Cmp6502, addr_abs) -> int:
    fetched = cpu.fetch()
    
    t = cpu.a & fetched
    cpu.set_flag(Z, not t)
    cpu.set_flag(N, fetched & 0x80) #bit 7  
    cpu.set_flag(V, fetched & 0x40) #bit 6

    return 0

def BCC(cpu: Cmp6502, addr_abs) -> int:
    if not (cpu.status & C): 
        cpu.cycles += 1 + ((cpu.addr_abs & 0xFF00) != (cpu.pc & 0xFF00))
        cpu.pc = cpu.addr_abs
    
    return 0


def BCS(cpu: Cmp6502, addr_abs) -> int:
    if cpu.status & C: 
        cpu.cycles += 1 + ((cpu.addr_abs & 0xFF00) != (cpu.pc & 0xFF00))
        cpu.pc = cpu.addr_abs
    
    return 0


def BEQ(cpu: Cmp6502, addr_abs) -> int:
    if cpu.status & Z: 
        cpu.cycles += 1 + ((cpu.addr_abs & 0xFF00) != (cpu.pc & 0xFF00))
        cpu.pc = cpu.addr_abs
    
    return 0


def BNE(cpu: Cmp6502, addr_abs) -> int:
    if not (cpu.status & Z): 
        cpu.cycles += 1 + ((cpu.addr_abs & 0xFF00) != (cpu.pc & 0xFF00))
        cpu.pc = cpu.addr_abs
    
    return 0


def BVC(cpu: Cmp6502, addr_abs) -> int:
    if not (cpu.status & V): 
        cpu.cycles += 1 + ((cpu.addr_abs & 0xFF00) != (cpu.pc & 0xFF00))
        cpu.pc = cpu.addr_abs
    
    return 0


def BVS(cpu: Cmp6502, addr_abs) -> int:
    if cpu.status & V: 
        cpu.cycles += 1 + ((cpu.addr_abs & 0xFF00) != (cpu.pc & 0xFF00))
        cpu.pc = cpu.addr_abs
    
    return 0


def BPL(cpu: Cmp6502, addr_abs) -> int:
    if not (cpu.status & N): 
        cpu.cycles += 1 + ((cpu.addr_abs & 0xFF00) != (cpu.pc & 0xFF00))
        cpu.pc = cpu.addr_abs
    
    return 0


def BMI(cpu: Cmp6502, addr_abs) -> int:
    if cpu.status & N: 
        cpu.cycles += 1 + ((cpu.addr_abs & 0xFF00) != (cpu.pc & 0xFF00))
        cpu.pc = cpu.addr_abs
    
    return 0
