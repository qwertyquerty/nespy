from typing import Tuple

from nespy.const import *

class Mapper():
    prg_banks: int = 0
    chr_banks: int = 0

    def __init__(self, prg_banks: int, chr_banks: int):
        self.prg_banks = prg_banks
        self.chr_banks = chr_banks
        self.reset()

    def map_cpu_read(self, addr: int) -> Tuple[int, int]: # (addr, value)
        pass

    def map_cpu_write(self, addr: int, value: int) -> int: # addr
        pass

    def map_ppu_read(self, addr: int) -> int: # addr
        pass

    def map_ppu_write(self, addr: int) -> int: # addr
        pass

    def reset(self):
        pass

    def mirror_mode(self) -> int:
        return MIRROR_HARDWARE

    def irq_state(self) -> bool:
        return False

    def irq_clear(self):
        pass

    def scanline(self):
        pass

from nespy.mappers import *

MAPPER_LOOKUP = {
    0: Mapper0,
    1: Mapper1
}
