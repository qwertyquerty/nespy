from typing import Tuple

from nespy.mapper import *

class Mapper0(Mapper):
    def map_cpu_read(self, addr: int) -> Tuple[int, int]: # (addr, value)
        if 0x8000 <= addr <= 0xFFFF:
            return (addr & (0x7FFF if self.prg_banks > 1 else 0x3FFF), 0x00)
        
        return None

    def map_cpu_write(self, addr: int, value: int) -> int: # addr
        if 0x8000 <= addr <= 0xFFFF:
            return addr & (0x7FFF if self.prg_banks > 1 else 0x3FFF)
        
        return None

    def map_ppu_read(self, addr: int) -> int: # addr
        if addr <= 0x1FFF:
            return addr
        
        return None

    def map_ppu_write(self, addr: int) -> int: # addr
        if addr <= 0x1FFF:
            if self.chr_banks == 0:
                return addr
        
        return None
