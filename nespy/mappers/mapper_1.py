from typing import Tuple

from nespy.mapper import *

class Mapper1(Mapper):
    chr_bank_select_lnib: int = 0x0
    chr_bank_select_hnib: int = 0x0
    chr_bank_select: int = 0x00

    prg_bank_select_lwrd: int = 0x0000
    prg_bank_select_hwrd: int = 0x0000
    prg_bank_select: int = 0x00000000

    load_register: int = 0x00
    load_register_count: int = 0
    control_register: int = 0x00

    ram_static: list = None

    mirroring: int = MIRROR_HORIZONTAL
    
    mirroring_cases: list = [MIRROR_ONSCREEN_LO, MIRROR_ONSCREEN_HI, MIRROR_VERTICAL, MIRROR_HORIZONTAL]

    def __init__(self):
        self.ram_static = [0x00 for i in range(0x8000)]

    def map_cpu_read(self, addr: int) -> Tuple[int, int]: # (addr, value)
        value = 0x00

        if 0x6000 <= addr <= 0x7FFF:
            value = self.ram_static[addr & 0x1FFF]
            return (0xFFFFFFFF, value)

        if addr >= 0x8000:
            if self.control_register & 0x8:
                # 16K mode
                if 0x8000 <= addr <= 0xBFFF:
                    return (self.prg_bank_select_lwrd * 0x4000 + (addr & 0x3FFF), value)
                
                if 0xC000 <= addr <= 0xFFFF:
                    return (self.prg_bank_select_hwrd * 0x4000 + (addr & 0x3FFF), value)
                
            else:
                # 32K mode
                return (self.prg_bank_select * 0x8000 + (addr & 0x7FFF), value)
        
        return None

    def map_cpu_write(self, addr: int, value: int) -> int: # addr
        if 0x6000 <= addr <= 0x7FFF:
            self.ram_static[addr & 0x1FFF] = value
            return 0xFFFFFFFF

        if addr >= 0x8000:
            if value & 0x80:
                # MSB set, reset serial loading
                self.load_register = 0x00
                self.load_register_count = 0x00
                self.control_register |= 0x0C
            
            else:
                # load value into left of load register
                self.load_register = self.load_register >> 1
                self.load_register |= (value & 0x01 << 4)
                self.load_register_count += 1

                if self.load_register_count == 5:
                    target_register = (addr >> 13) & 0x03

                    if target_register == 0:
                        self.control_register = self.load_register & 0x1F
                        self.mirroring = self.mirroring_cases[self.control_register & 0x03]

                    elif target_register == 1:
                        if self.control_register & 0x10:
                            self.chr_bank_select_lnib = self.load_register & 0x1F
                        
                        else:
                            self.chr_bank_select = self.load_register & 0x1E
                    
                    elif target_register == 2 and self.control_register & 0x10:
                        self.chr_bank_select_hnib = self.load_register & 0x1F

                    elif target_register == 3:
                        prg_mode = (self.control_register >> 2) & 0x03

                        if prg_mode == 0 or prg_mode == 1:
                            # Set 32K PRG Bank at CPU 0x8000
                            self.prg_bank_select = (self.load_register & 0x0E) >> 1
                        
                        elif prg_mode == 2:
                            # Fix 16KB PRG Bank at CPU 0x8000 to First Bank
                            self.prg_bank_select_lwrd = 0x0000
                            # Set 16KB PRG Bank at CPU 0xC000
                            self.prg_bank_select_hwrd = self.load_register & 0x0F
                        
                        elif prg_mode == 3:
                            # Set 16KB PRG Bank at CPU 0x8000
                            self.prg_bank_select_lwrd = self.load_register & 0x0F
                            # Fix 16KB PRG Bank at CPU 0xC000 to Last Bank
                            self.prg_bank_select_hwrd = self.prg_banks - 1
                
                    self.load_register = 0x00
                    self.load_register_count = 0
        
        return None

    def map_ppu_read(self, addr: int) -> int: # addr
        if addr <= 0x1FFF:
            if self.chr_banks == 0:
                return addr
            
            else:
                if self.control_register & 0x10:
                    # 4K CHR Bank Mode    
                    if addr <= 0x0FFF:
                        return self.chr_bank_select_lnib * 0x1000 + (addr & 0x0FFF)
                    
                    elif 0x1000 <= addr <= 0x1FFF:
                        return self.chr_bank_select_hnib * 0x1000 + (addr & 0x0FFF)
                    
                else:
                    # 8K CHR Bank Mode
                    return self.chr_bank_select * 0x2000 + (addr & 0x1FFF)
        
        return None

    def map_ppu_write(self, addr: int) -> int: # addr
        if addr <= 0x1FFF:
            if self.chr_banks == 0:
                return addr
            
            return 0x00
        
        return None

    def reset(self):
        self.control_register = 0x1C
        self.load_register = 0x00
        self.load_register_count = 0x00
        self.chr_bank_select_lnib = 0x0
        self.chr_bank_select_hnib = 0x0
        self.chr_bank_select = 0x00
        self.prg_bank_select_lwrd = 0x0000
        self.prg_bank_select_hwrd = self.prg_banks - 1
        self.prg_bank_select = 0x00000000
    
    def mirror_mode(self) -> int:
        return self.mirroring
