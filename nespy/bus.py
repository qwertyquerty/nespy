from nespy.cmp_2A03 import Cmp2A03
from nespy.cmp_2C02 import Cmp2C02
from nespy.cmp_6502 import Cmp6502
from nespy.cartridge import Cartridge
from nespy.const import *

class Bus():
    cpu: Cmp6502 = None
    ppu: Cmp2C02 = None
    apu: Cmp2A03 = None
    ram: list = None
    cartridge: Cartridge = None

    system_clock_count: int = 0

    dma_page: int = 0x00
    dma_addr: int = 0x00
    dma_value: int = 0x00 
    dma_enable: bool = False # are we currently running a DMA
    dma_wait: bool = True # set this to make sure the DMA only starts on an even cycle

    open_bus: int = 0x00

    controller_states: list = None
    controllers: tuple = None

    audio_sample: float = 0
    audio_time: float = 0
    audio_global_time: float = 0
    audio_time_per_clock: float = 1 / PPU_CLOCK_FREQ
    audio_system_per_system_sample: float = 1/AUDIO_SAMPLE_RATE
    audio_sample: int = 0x00

    def __init__(self):
        self.cpu = Cmp6502(self)
        self.ppu = Cmp2C02(self)
        self.apu = Cmp2A03()
        self.ram = [0x00 for i in range(0x0800)]
        self.controllers = (0x00, 0x00)
        self.controller_state = [0x00, 0x00]
        self.audio_samples = []
    
    def reset(self):
        if self.cartridge:
            self.cartridge.reset()
        
        self.cpu.reset()
        self.ppu.reset()
        self.ram = [0x00 for i in range(0x0800)]

        self.system_clock_count = 0

        self.dma_page = 0x00
        self.dma_addr = 0x00
        self.dma_value = 0x00
        self.dma_wait = True
        self.dma_enable = False
    
        self.audio_time = 0
        self.audio_global_time = 0
        self.audio_sample = 0x00

    def plug_cartridge(self, cart: Cartridge):
        self.cartridge = cart
        self.ppu.plug_cartridge(self.cartridge)

    def read(self, addr: int, read_only: bool = False):
        cart_read = self.cartridge.cpu_read(addr)

        if cart_read is not None: # Cartridge address range
            # The cartridge can effectively trump any bus read using the mapper
            return cart_read

        elif 0x0000 <= addr <= 0x1FFF: # RAM address range
            return self.ram[addr & 0x7FF] # mirrored every 0x800
        
        elif 0x2000 <= addr <= 0x3FFF: # PPU address range
            return self.ppu.cpu_read(addr & 0x0007, read_only)
        
        elif addr == 0x4015: # specific address that reads APU status
            return self.apu.cpu_read(addr)

        elif 0x4016 <= addr <= 0x4017: # both plugged in controllers
            value = (self.controller_state[addr & 0x0001] & 0x80) > 0
            self.controller_state[addr & 0x0001] = (self.controller_state[addr & 0x0001] << 1) & 0xFF
            return value

        return self.open_bus

    def write(self, addr: int, value: int):
        value &= 0xFF # bounds checking

        self.open_bus = value

        if self.cartridge.cpu_write(addr, value): # cartridge mapper can trump any write
            pass

        elif 0x0000 <= addr <= 0x1FFF: # RAM address range
            self.ram[addr & 0x7FF] = value # mirrored every 0x800

        elif 0x2000 <= addr <= 0x3FFF: # PPU address range
            self.ppu.cpu_write(addr & 0x0007, value)
        
        elif (0x4000 <= addr <= 0x4013) or addr == 0x4015: # APU addresses
            self.apu.cpu_write(addr, value)
            
        elif addr == 0x4014: # specific address that triggers a DMA
            self.dma_page = value
            self.dma_addr = 0x00
            self.dma_enable = True
        
        elif 0x4016 <= addr <= 0x4017: # both plugged in controllers
            self.controller_state[addr & 0x0001] = self.controllers[addr & 0x0001]

    def clock(self):
        self.ppu.clock()

        #self.apu.clock()

        if self.system_clock_count % 3 == 0: # cpu only clocks once every 3 system clocks
            # Direct memory access
            if self.dma_enable:
                if self.dma_wait:
                    if self.system_clock_count % 2 == 1:
                        self.dma_wait = False # we are now starting on the correct clock cycle
                    
                else:
                    if self.system_clock_count % 2 == 0:
                        self.dma_value = self.read((self.dma_page << 8) | self.dma_addr)
                    
                    else:
                        self.write(0x2004, self.dma_value)

                        self.dma_addr = (self.dma_addr + 1) & 0xFF

                        if self.dma_addr == 0x00:
                            self.dma_enable = False
                            self.dma_wait = True

            else:
                # DMA isn't happening so we can actually clock the cpu
                self.cpu.clock()

        self.audio_time += self.audio_time_per_clock

        #if self.audio_time >= self.audio_system_per_system_sample:
        #    self.audio_time -= self.audio_system_per_system_sample
        #    self.audio_sample = self.apu.get_sample()

        if self.ppu.nmi:
            self.ppu.nmi = False
            self.cpu.non_maskable_interrupt()
        
        if self.cartridge.mapper.irq_state():
            self.cartridge.mapper.irq_clear()
            self.cpu.interrupt_request()

        self.system_clock_count += 1
