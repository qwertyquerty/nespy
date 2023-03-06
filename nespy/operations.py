from typing import Callable

from nespy.instructions import *
from nespy.addr_modes import *

class Operation():
    def __init__(self, name: str = "???", instruction: Callable = None, addr_mode: Callable = None, cycles: int = 0):
        self.name = name
        self.addr_mode = addr_mode
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

OPCODE_LOOKUP = []
#OPCODE_LOOKUP = [
#    Operation("BRK", BRK, IMM, 7),Operation("ORA", ORA, IZX, 6),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 8),Operation("???", NOP, IMP, 3),Operation("ORA", ORA, ZP0, 3),Operation("ASL", ASL, ZP0, 5),Operation("???", UNK, IMP, 5),Operation("PHP", PHP, IMP, 3),Operation("ORA", ORA, IMM, 2),Operation("ASL", ASL, IMP, 2),Operation("???", UNK, IMP, 2),Operation("???", NOP, IMP, 4),Operation("ORA", ORA, ABS, 4),Operation("ASL", ASL, ABS, 6),Operation("???", UNK, IMP, 6),
#    Operation("BPL", BPL, REL, 2),Operation("ORA", ORA, IZY, 5),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 8),Operation("???", NOP, IMP, 4),Operation("ORA", ORA, ZPX, 4),Operation("ASL", ASL, ZPX, 6),Operation("???", UNK, IMP, 6),Operation("CLC", CLC, IMP, 2),Operation("ORA", ORA, ABY, 4),Operation("???", NOP, IMP, 2),Operation("???", UNK, IMP, 7),Operation("???", NOP, IMP, 4),Operation("ORA", ORA, ABX, 4),Operation("ASL", ASL, ABX, 7),Operation("???", UNK, IMP, 7),
#    Operation("JSR", JSR, ABS, 6),Operation("AND", AND, IZX, 6),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 8),Operation("BIT", BIT, ZP0, 3),Operation("AND", AND, ZP0, 3),Operation("ROL", ROL, ZP0, 5),Operation("???", UNK, IMP, 5),Operation("PLP", PLP, IMP, 4),Operation("AND", AND, IMM, 2),Operation("ROL", ROL, IMP, 2),Operation("???", UNK, IMP, 2),Operation("BIT", BIT, ABS, 4),Operation("AND", AND, ABS, 4),Operation("ROL", ROL, ABS, 6),Operation("???", UNK, IMP, 6),
#    Operation("BMI", BMI, REL, 2),Operation("AND", AND, IZY, 5),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 8),Operation("???", NOP, IMP, 4),Operation("AND", AND, ZPX, 4),Operation("ROL", ROL, ZPX, 6),Operation("???", UNK, IMP, 6),Operation("SEC", SEC, IMP, 2),Operation("AND", AND, ABY, 4),Operation("???", NOP, IMP, 2),Operation("???", UNK, IMP, 7),Operation("???", NOP, IMP, 4),Operation("AND", AND, ABX, 4),Operation("ROL", ROL, ABX, 7),Operation("???", UNK, IMP, 7),
#    Operation("RTI", RTI, IMP, 6),Operation("EOR", EOR, IZX, 6),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 8),Operation("???", NOP, IMP, 3),Operation("EOR", EOR, ZP0, 3),Operation("LSR", LSR, ZP0, 5),Operation("???", UNK, IMP, 5),Operation("PHA", PHA, IMP, 3),Operation("EOR", EOR, IMM, 2),Operation("LSR", LSR, IMP, 2),Operation("???", UNK, IMP, 2),Operation("JMP", JMP, ABS, 3),Operation("EOR", EOR, ABS, 4),Operation("LSR", LSR, ABS, 6),Operation("???", UNK, IMP, 6),
#    Operation("BVC", BVC, REL, 2),Operation("EOR", EOR, IZY, 5),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 8),Operation("???", NOP, IMP, 4),Operation("EOR", EOR, ZPX, 4),Operation("LSR", LSR, ZPX, 6),Operation("???", UNK, IMP, 6),Operation("CLI", CLI, IMP, 2),Operation("EOR", EOR, ABY, 4),Operation("???", NOP, IMP, 2),Operation("???", UNK, IMP, 7),Operation("???", NOP, IMP, 4),Operation("EOR", EOR, ABX, 4),Operation("LSR", LSR, ABX, 7),Operation("???", UNK, IMP, 7),
#    Operation("RTS", RTS, IMP, 6),Operation("ADC", ADC, IZX, 6),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 8),Operation("???", NOP, IMP, 3),Operation("ADC", ADC, ZP0, 3),Operation("ROR", ROR, ZP0, 5),Operation("???", UNK, IMP, 5),Operation("PLA", PLA, IMP, 4),Operation("ADC", ADC, IMM, 2),Operation("ROR", ROR, IMP, 2),Operation("???", UNK, IMP, 2),Operation("JMP", JMP, IND, 5),Operation("ADC", ADC, ABS, 4),Operation("ROR", ROR, ABS, 6),Operation("???", UNK, IMP, 6),
#    Operation("BVS", BVS, REL, 2),Operation("ADC", ADC, IZY, 5),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 8),Operation("???", NOP, IMP, 4),Operation("ADC", ADC, ZPX, 4),Operation("ROR", ROR, ZPX, 6),Operation("???", UNK, IMP, 6),Operation("SEI", SEI, IMP, 2),Operation("ADC", ADC, ABY, 4),Operation("???", NOP, IMP, 2),Operation("???", UNK, IMP, 7),Operation("???", NOP, IMP, 4),Operation("ADC", ADC, ABX, 4),Operation("ROR", ROR, ABX, 7),Operation("???", UNK, IMP, 7),
#    Operation("???", NOP, IMP, 2),Operation("STA", STA, IZX, 6),Operation("???", NOP, IMP, 2),Operation("???", UNK, IMP, 6),Operation("STY", STY, ZP0, 3),Operation("STA", STA, ZP0, 3),Operation("STX", STX, ZP0, 3),Operation("???", UNK, IMP, 3),Operation("DEY", DEY, IMP, 2),Operation("???", NOP, IMP, 2),Operation("TXA", TXA, IMP, 2),Operation("???", UNK, IMP, 2),Operation("STY", STY, ABS, 4),Operation("STA", STA, ABS, 4),Operation("STX", STX, ABS, 4),Operation("???", UNK, IMP, 4),
#    Operation("BCC", BCC, REL, 2),Operation("STA", STA, IZY, 6),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 6),Operation("STY", STY, ZPX, 4),Operation("STA", STA, ZPX, 4),Operation("STX", STX, ZPY, 4),Operation("???", UNK, IMP, 4),Operation("TYA", TYA, IMP, 2),Operation("STA", STA, ABY, 5),Operation("TXS", TXS, IMP, 2),Operation("???", UNK, IMP, 5),Operation("???", NOP, IMP, 5),Operation("STA", STA, ABX, 5),Operation("???", UNK, IMP, 5),Operation("???", UNK, IMP, 5),
#    Operation("LDY", LDY, IMM, 2),Operation("LDA", LDA, IZX, 6),Operation("LDX", LDX, IMM, 2),Operation("???", UNK, IMP, 6),Operation("LDY", LDY, ZP0, 3),Operation("LDA", LDA, ZP0, 3),Operation("LDX", LDX, ZP0, 3),Operation("???", UNK, IMP, 3),Operation("TAY", TAY, IMP, 2),Operation("LDA", LDA, IMM, 2),Operation("TAX", TAX, IMP, 2),Operation("???", UNK, IMP, 2),Operation("LDY", LDY, ABS, 4),Operation("LDA", LDA, ABS, 4),Operation("LDX", LDX, ABS, 4),Operation("???", UNK, IMP, 4),
#    Operation("BCS", BCS, REL, 2),Operation("LDA", LDA, IZY, 5),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 5),Operation("LDY", LDY, ZPX, 4),Operation("LDA", LDA, ZPX, 4),Operation("LDX", LDX, ZPY, 4),Operation("???", UNK, IMP, 4),Operation("CLV", CLV, IMP, 2),Operation("LDA", LDA, ABY, 4),Operation("TSX", TSX, IMP, 2),Operation("???", UNK, IMP, 4),Operation("LDY", LDY, ABX, 4),Operation("LDA", LDA, ABX, 4),Operation("LDX", LDX, ABY, 4),Operation("???", UNK, IMP, 4),
#    Operation("CPY", CPY, IMM, 2),Operation("CMP", CMP, IZX, 6),Operation("???", NOP, IMP, 2),Operation("???", UNK, IMP, 8),Operation("CPY", CPY, ZP0, 3),Operation("CMP", CMP, ZP0, 3),Operation("DEC", DEC, ZP0, 5),Operation("???", UNK, IMP, 5),Operation("INY", INY, IMP, 2),Operation("CMP", CMP, IMM, 2),Operation("DEX", DEX, IMP, 2),Operation("???", UNK, IMP, 2),Operation("CPY", CPY, ABS, 4),Operation("CMP", CMP, ABS, 4),Operation("DEC", DEC, ABS, 6),Operation("???", UNK, IMP, 6),
#    Operation("BNE", BNE, REL, 2),Operation("CMP", CMP, IZY, 5),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 8),Operation("???", NOP, IMP, 4),Operation("CMP", CMP, ZPX, 4),Operation("DEC", DEC, ZPX, 6),Operation("???", UNK, IMP, 6),Operation("CLD", CLD, IMP, 2),Operation("CMP", CMP, ABY, 4),Operation("NOP", NOP, IMP, 2),Operation("???", UNK, IMP, 7),Operation("???", NOP, IMP, 4),Operation("CMP", CMP, ABX, 4),Operation("DEC", DEC, ABX, 7),Operation("???", UNK, IMP, 7),
#    Operation("CPX", CPX, IMM, 2),Operation("SBC", SBC, IZX, 6),Operation("???", NOP, IMP, 2),Operation("???", UNK, IMP, 8),Operation("CPX", CPX, ZP0, 3),Operation("SBC", SBC, ZP0, 3),Operation("INC", INC, ZP0, 5),Operation("???", UNK, IMP, 5),Operation("INX", INX, IMP, 2),Operation("SBC", SBC, IMM, 2),Operation("NOP", NOP, IMP, 2),Operation("???", SBC, IMP, 2),Operation("CPX", CPX, ABS, 4),Operation("SBC", SBC, ABS, 4),Operation("INC", INC, ABS, 6),Operation("???", UNK, IMP, 6),
#    Operation("BEQ", BEQ, REL, 2),Operation("SBC", SBC, IZY, 5),Operation("???", UNK, IMP, 2),Operation("???", UNK, IMP, 8),Operation("???", NOP, IMP, 4),Operation("SBC", SBC, ZPX, 4),Operation("INC", INC, ZPX, 6),Operation("???", UNK, IMP, 6),Operation("SED", SED, IMP, 2),Operation("SBC", SBC, ABY, 4),Operation("NOP", NOP, IMP, 2),Operation("???", UNK, IMP, 7),Operation("???", NOP, IMP, 4),Operation("SBC", SBC, ABX, 4),Operation("INC", INC, ABX, 7),Operation("???", UNK, IMP, 7),
#]
