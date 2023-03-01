
class CmpRAM():
    def __init__(self, bus):
        self.bus = bus
        
        self.ram = [0] * 0xFFFF

    def read(self, addr: int) -> int:
        return self.ram[addr]

    def write(self, addr: int, value: int) -> None:
        self.ram[addr] = value