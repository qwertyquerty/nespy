from nespy.cmp_6502 import Cmp6502
from nespy.cmp_ram import CmpRAM

class Bus():
    def __init__(self):
        self.cpu = Cmp6502(self)
        self.ram = CmpRAM(self)
