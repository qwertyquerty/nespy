from typing import Tuple

MIRROR_HARDWARE = 1
MIRROR_HORIZONTAL = 2
MIRROR_VERTICAL = 3
MIRROR_ONSCREEN_LO = 4
MIRROR_ONSCREEN_HI = 5

class Mapper():
    prg_banks: int = 0
    chr_banks: int = 0

    def __init__(self, prg_banks: int, chr_banks: int):
        self.prg_banks = prg_banks
        self.chr_banks = chr_banks

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
        pass

    def irq_state(self) -> bool:
        pass

    def irq_clear(self):
        pass

    def scanline(self):
        pass

from nespy.mappers import *

MAPPER_LOOKUP = {
    1: Mapper1
}
