from dataclasses import dataclass
import pygame as pg

import numpy as np

from nespy.cartridge import Cartridge
from nespy.const import *

class Cmp2C02():
    bus = None

    tbl_name: list[list] = None
    tbl_pattern: list[list] = None
    tbl_palette: list = None

    screen: pg.Surface = None
    display: pg.Surface = None

    spr_screen: list[list[tuple]] = None

    frame_complete: bool = False

    nmi: bool = False

    fine_x: int = 0x00
    address_latch: int = 0x00
    ppu_data_buffer: int = 0x00

    scanline: int = 0x00
    cycle: int = 0x00

    bg_next_tile_id: int = 0x00
    bg_next_tile_attrib: int = 0x00
    bg_next_tile_lsb: int = 0x00
    bg_next_tile_msb: int = 0x00
    bg_shifter_pattern_lwrd: int = 0x0000
    bg_shifter_pattern_hwrd: int = 0x0000
    bg_shifter_attrib_lwrd: int = 0x0000
    bg_shifter_attrib_hwrd: int = 0x0000

    status: int = 0x00
    mask: int = 0x00
    control: int = 0x00
    
    @dataclass
    class RamAddrRegister:
        coarse_x: int = 0x00
        coarse_y: int = 0x00
        nametable_x: bool = False
        nametable_y: bool = False
        fine_y: int = 0x00

        def pack(self) -> int:
            return (self.fine_y << 12) | (self.nametable_x << 11) | (self.nametable_y << 10) | (self.coarse_y << 5) | (self.coarse_x)

        def load(self, value):
            self.fine_y = ((value & 0b111000000000000) >> 12)
            self.nametable_x = ((value & 0b100000000000) >> 11)
            self.nametable_y = ((value & 0b10000000000) >> 10)
            self.coarse_y = ((value & 0b1111100000) >> 5)
            self.coarse_x = ((value & 0b11111) >> 0)

    vram_addr: RamAddrRegister = None
    tram_addr: RamAddrRegister = None
    
    def __init__(self, bus):
        self.bus = bus

        self.vram_addr = self.RamAddrRegister()
        self.tram_addr = self.RamAddrRegister()

        self.screen = pg.Surface((256, 240), pg.HWACCEL|pg.DOUBLEBUF)
        self.display = pg.display.set_mode((256*2, 240*2), pg.HWACCEL|pg.DOUBLEBUF)

        self.spr_screen = [[0x00 for j in range(240)] for i in range(256)]

        self.tbl_name = [[0x00 for j in range(1024)] for i in range(2)]
        self.tbl_pattern = [[0x00 for j in range(4096)] for i in range(2)]
        self.tbl_palette = [0x00 for i in range(32)]

    def reset(self):
        self.fine_x = 0
        self.address_latch = 0
        self.ppu_data_buffer = 0
        self.scanline = 0
        self.cycle = 0
        self.bg_next_tile_id = 0
        self.bg_next_tile_attrib = 0
        self.bg_next_tile_lsb = 0
        self.bg_next_tile_msb = 0
        self.bg_shifter_attrib_lwrd = 0
        self.bg_shifter_pattern_hwrd = 0
        self.bg_shifter_attrib_lwrd = 0
        self.bg_shifter_attrib_hwrd = 0
        self.status = 0x00
        self.mask = 0x00
        self.control = 0x00
        self.vram_addr.load(0x0000)
        self.tram_addr.load(0x000)

    def cpu_read(self, addr: int, read_only: bool = False) -> int:
        value = 0x00

        if addr == 0x0002:
            value = (self.status & 0xE0) | (self.ppu_data_buffer & 0x1F)
            self.status &= ~VERTICAL_BLANK
            self.address_latch = 0
            return value
        
        if addr == 0x0003: # OAM addr
            pass

        if addr == 0x0004: # OAM data
            pass

        if addr == 0x0007:
            value = self.ppu_data_buffer
            self.ppu_data_buffer = self.ppu_read(self.vram_addr.pack())

            if self.vram_addr >= 0x3F00:
                value = self.ppu_data_buffer
            
            self.vram_addr.load(self.vram_addr.pack() + (32 if self.control & INCREMENT_MODE else 1))
        
            return value

    def cpu_write(self, addr: int, value: int):
        if addr == 0x0000:
            self.control = value
            self.tram_addr.nametable_x = bool(self.control & NAMETABLE_X)
            self.tram_addr.nametable_y = bool(self.control & NAMETABLE_Y)

            return
        
        if addr == 0x0001:
            self.mask = value
            return

        if addr == 0x0002:
            pass # status
        if addr == 0x0003:
            pass # OAM addr
        if addr == 0x0004:
            pass # OAM data

        if addr == 0x0005:
            # scroll
            if self.address_latch == 0:
                self.fine_x = value & 0x07
                self.tram_addr.coarse_x = value >> 3
                self.address_latch = 1
            
            else:
                self.tram_addr.fine_y = value & 0x07
                self.tram_addr.coarse_y = value >> 3
                self.address_latch = 0
            
            return
        
        if addr == 0x0006:
            # ppu address
            if self.address_latch == 0:
                self.tram_addr.load(((value & 0x3F) << 8) | (self.tram_addr.pack() & 0x00FF))
                self.address_latch = 1

            else:
                self.tram_addr.load((self.tram_addr.pack() & 0xFF00) | value)
                self.vram_addr.load(self.tram_addr.pack())
                self.address_latch = 0
            
            return

        if addr == 0x0007:
            self.ppu_write(self.vram_addr.pack(), value)
            self.vram_addr.load(self.vram_addr.pack() + (32 if self.control & INCREMENT_MODE else 1))
            return

    def ppu_read(self, addr: int, read_only: bool = False) -> int:
        value = 0x00
        addr &= 0x3FFF

        out = self.cartridge.ppu_read(addr)
        if out is not None:
            return out
        
        if addr <= 0x1FFF:
            return self.tbl_pattern[(addr & 0x1000) >> 12][addr & 0x0FFF]

        if 0x2000 <= addr <= 0x3EFF:
            addr &= 0x0FFF

            mirror = self.cartridge.get_mirror()

            if mirror == MIRROR_VERTICAL:
                if addr <= 0x03FF:
                    return self.tbl_name[0][addr & 0x03FF]
                if 0x0400 <= addr <= 0x07FF:
                    return self.tbl_name[1][addr & 0x03FF]
                if 0x0800 <= addr <= 0x0BFF:
                    return self.tbl_name[0][addr & 0x03FF]
                if 0x0C00 <= addr <= 0x0FFF:
                    return self.tbl_name[1][addr & 0x03FF]

            elif mirror == MIRROR_HORIZONTAL:
                if addr <= 0x03FF:
                    return self.tbl_name[0][addr & 0x03FF]
                if 0x0400 <= addr <= 0x07FF:
                    return self.tbl_name[0][addr & 0x03FF]
                if 0x0800 <= addr <= 0x0BFF:
                    return self.tbl_name[1][addr & 0x03FF]
                if 0x0C00 <= addr <= 0x0FFF:
                    return self.tbl_name[1][addr & 0x03FF]
            
        if 0x3F00 <= addr <= 0x3FFF:
            addr &= 0x001F
            if addr == 0x0010: addr = 0x0000
            elif addr == 0x0014: addr = 0x0004
            elif addr == 0x0018: addr = 0x0008
            elif addr == 0x001C: addr = 0x000C
            return self.tbl_palette[addr] & (0x30 if self.mask & GRAYSCALE else 0x3F)
        
        return value

    def ppu_write(self, addr: int, value: int):
        addr &= 0x3FFF

        if self.cartridge.ppu_write(addr, value):
            return
        
        if addr <= 0x1FFF:
            self.tbl_pattern[(addr & 0x1000) >> 12][addr & 0x0FFF] = value
            return
        
        if 0x2000 <= addr <= 0x3EFF:
            addr &= 0x0FFF

            mirror = self.cartridge.get_mirror()

            if mirror == MIRROR_VERTICAL:
                if addr <= 0x03FF:
                    self.tbl_name[0][addr & 0x03FF] = value
                    return
                if 0x0400 <= addr <= 0x07FF:
                    self.tbl_name[1][addr & 0x03FF] = value
                    return
                if 0x0800 <= addr <= 0x0BFF:
                    self.tbl_name[0][addr & 0x03FF] = value
                    return
                if 0x0C00 <= addr <= 0x0FFF:
                    self.tbl_name[1][addr & 0x03FF] = value
                    return

            elif mirror == MIRROR_HORIZONTAL:
                if addr <= 0x03FF:
                    self.tbl_name[0][addr & 0x03FF] = value
                    return
                if 0x0400 <= addr <= 0x07FF:
                    self.tbl_name[0][addr & 0x03FF] = value
                    return
                if 0x0800 <= addr <= 0x0BFF:
                    self.tbl_name[1][addr & 0x03FF] = value
                    return
                if 0x0C00 <= addr <= 0x0FFF:
                    self.tbl_name[1][addr & 0x03FF] = value
                    return
            
        if 0x3F00 <= addr <= 0x3FFF:
            addr &= 0x001F
            if addr == 0x0010: addr = 0x0000
            elif addr == 0x0014: addr = 0x0004
            elif addr == 0x0018: addr = 0x0008
            elif addr == 0x001C: addr = 0x000C
            self.tbl_palette[addr] = value
            return
     

    def get_color_from_palette(self, palette: int, pixel: int) -> int:
        return PAL_COLORS[self.ppu_read(0x3F00 + (palette << 2) + pixel) & 0x3F]

    def increment_scroll_x(self):
        if self.mask & (RENDER_BACKGROUND | RENDER_SPRITES):
            if self.vram_addr.coarse_x == 31:
                self.vram_addr.coarse_x = 0
                self.vram_addr.nametable_x = not self.vram_addr.nametable_x
            else:
                self.vram_addr.coarse_x += 1
    
    def increment_scroll_y(self):
        if self.mask & (RENDER_BACKGROUND | RENDER_SPRITES):
            if self.vram_addr.fine_y < 7:
                self.vram_addr.fine_y += 1
            else:
                self.vram_addr.fine_y = 0
                
                if self.vram_addr.coarse_y == 29:
                    self.vram_addr.coarse_y = 0
                    self.vram_addr.nametable_y = not self.vram_addr.nametable_y
                
                elif self.vram_addr.coarse_y == 31:
                    self.vram_addr.coarse_y = 0
                
                else:
                    self.vram_addr.coarse_y += 1

    def transfer_address_x(self):
        if self.mask & (RENDER_BACKGROUND | RENDER_SPRITES):
            self.vram_addr.nametable_x = self.tram_addr.nametable_x
            self.vram_addr.coarse_x = self.tram_addr.coarse_x

    def transfer_address_y(self):
        if self.mask & (RENDER_BACKGROUND | RENDER_SPRITES):
            self.vram_addr.fine_y = self.tram_addr.fine_y
            self.vram_addr.nametable_y = self.tram_addr.nametable_y
            self.vram_addr.coarse_y = self.tram_addr.coarse_y
    
    def load_background_shifters(self):
        self.bg_shifter_pattern_lwrd = (self.bg_shifter_pattern_lwrd & 0xFF00) | self.bg_next_tile_lsb
        self.bg_shifter_pattern_hwrd = (self.bg_shifter_pattern_hwrd & 0xFF00) | self.bg_next_tile_msb
        self.bg_shifter_attrib_lwrd = (self.bg_shifter_attrib_lwrd & 0xFF00) | (0xFF if (self.bg_next_tile_attrib & 0x01) else 0x00)
        self.bg_shifter_attrib_hwrd = (self.bg_shifter_attrib_hwrd & 0xFF00) | (0xFF if (self.bg_next_tile_attrib & 0x02) else 0x00)

    def update_shifters(self):
        if self.mask & RENDER_BACKGROUND:
            self.bg_shifter_pattern_lwrd = (self.bg_shifter_attrib_lwrd << 1) & 0xFFFF
            self.bg_shifter_pattern_hwrd = (self.bg_shifter_pattern_hwrd << 1) & 0xFFFF
            self.bg_shifter_attrib_lwrd = (self.bg_shifter_attrib_lwrd << 1) & 0xFFFF
            self.bg_shifter_attrib_hwrd = (self.bg_shifter_attrib_hwrd << 1) & 0xFFFF


    def clock(self):
        if -1 <= self.scanline < 240:
            if self.scanline == 0 and self.cycle == 0:
                self.cycle = 1
            
            elif self.scanline == -1 and self.cycle == 1:
                self.status &= ~VERTICAL_BLANK
            
            elif (2 <= self.cycle < 258) or (321 <= self.cycle < 338):
                self.update_shifters()

                k = (self.cycle - 1) % 8

                if k == 0:
                    self.load_background_shifters()
                    self.bg_next_tile_id = self.ppu_read(0x2000 | (self.vram_addr.pack() & 0x0FFF))

                elif k == 2:
                    self.bg_next_tile_attrib = self.ppu_read(
                        0x23C0 | (self.vram_addr.nametable_y << 11) | (self.vram_addr.nametable_x << 10) | ((self.vram_addr.coarse_y >> 2) << 3) | (self.vram_addr.coarse_x >> 2)
                    )

                    if self.vram_addr.coarse_y & 0x02: self.bg_next_tile_attrib >>= 4
                    if self.vram_addr.coarse_x & 0x02: self.bg_next_tile_attrib >>= 2
                    self.bg_next_tile_attrib &= 0x03

                elif k == 4:
                    self.bg_next_tile_lsb = self.ppu_read((bool(self.control & PATTERN_BACKGROUND) << 12) + (self.bg_next_tile_id << 4) + self.vram_addr.fine_y)

                elif k == 6:
                    self.bg_next_tile_msb = self.ppu_read((bool(self.control & PATTERN_BACKGROUND) << 12) + (self.bg_next_tile_id << 4) + self.vram_addr.fine_y + 8)

                elif k == 7:
                    self.increment_scroll_x()
            
            if self.cycle == 256:
                self.increment_scroll_y()
    
            elif self.cycle == 257:
                self.load_background_shifters()
                self.transfer_address_x()
            
            elif self.cycle == 338 or self.cycle == 340:
                self.bg_next_tile_id = self.ppu_read(0x2000 | (self.vram_addr.pack() & 0x0FFF))

            if self.scanline == -1 and (280 <= self.cycle < 305):
                self.transfer_address_y()
        
        elif self.scanline == 240:
            pass
            
        elif 241 <= self.scanline < 261:
            if self.scanline == 241 and self.cycle == 1:
                self.status |= VERTICAL_BLANK

                if self.control & ENABLE_NMI:
                    self.nmi = True
        
        bg_pixel = 0x00
        bg_palette = 0x00

        if self.mask & RENDER_BACKGROUND:
            bitmux = 0x8000 >> self.fine_x
            p0 = (self.bg_shifter_pattern_lwrd & bitmux) > 0
            p1 = (self.bg_shifter_pattern_hwrd & bitmux) > 0
            
            bg_pixel = (p1 << 1) | p0

            bg0 = (self.bg_shifter_attrib_lwrd & bitmux) > 0
            bg1 = (self.bg_shifter_attrib_hwrd & bitmux) > 0
            bg_palette = (bg1 << 1) | bg0

        if 0 <= self.cycle < 256 and 0 <= self.scanline < 240:
            self.spr_screen[self.cycle - 1][self.scanline] = self.get_color_from_palette(bg_palette, bg_pixel)

        self.cycle += 1

        if self.cycle >= 341:
            self.cycle = 0
            self.scanline += 1

            if self.scanline >= 261:
                self.scanline = -1
                self.frame_complete = True
                
                pg.surfarray.blit_array(self.screen, np.array(self.spr_screen))
                pg.transform.scale2x(self.screen, self.display)
                pg.display.flip()

    def plug_cartridge(self, cart: Cartridge):
        self.cartridge = cart
