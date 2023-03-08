from nespy.cmp_6502 import Cmp6502
from nespy.cartridge import Cartridge

class Bus():
    cpu: Cmp6502 = None
    ram: list = None
    cartridge: Cartridge = None

    system_clock_count: int = 0

    dma_page: int = 0x00
    dma_addr: int = 0x00
    dma_value: int = 0x00 
    dma_enable: bool = False # are we currently running a DMA
    dma_wait: bool = False # set this to make sure the DMA only starts on an even cycle

    def __init__(self):
        self.cpu = Cmp6502(self)
        self.ram = [0x00 for i in range(0x0800)]
    
    def reset(self):
        if self.cartridge:
            self.cartridge.reset()
        
        self.cpu.reset()
        self.ram = [0x00 for i in range(0x0800)]

        self.system_clock_count = 0

        self.dma_page = 0x00
        self.dma_addr = 0x00
        self.dma_value = 0x00
        self.dma_enable = 0x00
        self.dma_enable = False
    
    def plug_cartridge(self, cart: Cartridge):
        self.cartridge = cart


    def read(self, addr: int, read_only: bool):
        value = 0x00

        cart_read = self.cartridge.cpu_read(addr)

        if cart_read != None: # Cartridge address range
            # The cartridge can effectively trump any bus read using the mapper
            value = cart_read

        elif 0x0000 <= addr <= 0x1FFF: # RAM address range
            value = self.ram[addr & 0x7FF] # mirrored every 0x800
        
        elif 0x2000 <= addr <= 0x3FFF: # PPU address range
            pass # TODO: read from PPU, mirrored every 0x8
        
        elif addr == 0x4015: # specific address that reads APU status
            pass # TODO: read APU status

        elif 0x4016 <= addr <= 0x4017: # both plugged in controllers
            pass # TODO: read from controllers

        return value

    def write(self, addr: int, value: int):
        if self.cartridge.cpu_write(addr, value): # cartridge mapper can trump any write
            pass

        elif 0x0000 <= addr <= 0x1FFF: # RAM address range
            self.ram[addr & 0x7FF] = value # mirrored every 0x800

        elif 0x2000 <= addr <= 0x3FFF: # PPU address range
            pass # TODO: write to PPU, mirrored every 0x8
        
        elif (0x4000 <= addr <= 0x4013) or addr == 0x4015: # APU addresses
            pass # TODO: write to APU
            
        elif addr == 0x4014: # specific address that triggers a DMA
            self.dma_page = value
            self.dma_addr = 0x00
            self.dma_enable = True
        
        elif 0x4016 <= addr <= 0x4017: # both plugged in controllers
            pass # TODO: lock in controller state

    def clock(self):
        # TODO: clock ppu

        # TODO: clock apu

        if self.system_clock_count % 3 == 0: # cpu only clocks once every 3 system clocks
            # Direct memory access
            if self.dma_enable:
                if self.dma_wait:
                    if self.system_clock_count % 2 == 1:
                        self.dma_wait = False # we are now starting on the correct clock cycle
                    
                else:
                    if self.system_clock_count % 2 == 0:
                        self.dma_value = self.cpu_read((self.dma_page << 8) | self.dma_addr)
                    
                    else:
                        # TODO: write to PPA OAM here
                        self.dma_addr = (self.dma_addr + 1) & 0xFF

                        if self.dma_addr == 0x00:
                            self.dma_enable = False
                            self.dma_wait = True

            else:
                # DMA isn't happening so we can actually clock the cpu
                self.cpu.clock()

        # TODO: PPU NMIs

        # TODO: Cartridge mapper IRQs

        self.system_clock_count += 1
