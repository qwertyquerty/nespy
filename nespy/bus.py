from nespy.cmp_6502 import Cmp6502
from nespy.cmp_ram import CmpRAM

class Bus():
    def __init__(self):
        self.cpu = Cmp6502(self)
        self.ram = CmpRAM(self)

    def read(self, addr: int, read_only: bool = False) -> int:
        return self.ram.read(addr)

    def write(self, addr: int, value: int) -> None:
        # ensure the addr and value are in accepted ranges for byte widths
        addr &= 0xFFFF
        value &= 0xFF
        
        self.ram.write(addr, value)
