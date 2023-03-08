import io

from nespy.mapper import *
from nespy.const import *

class Cartridge():
    mapper: Mapper = None

    mapper_id: int = 0
    prg_banks: int = 0
    chr_banks: int = 0
    prg_memory: list = None
    chr_memory: list = None

    hardware_mirror: int = MIRROR_HORIZONTAL

    def __init__(self, rom_path: str):
        rom_file = open(rom_path, "rb")

        stream = io.BytesIO(rom_file.read())
    
        # read in the header of the file
        name = stream.read(4).decode("ascii")
        prg_rom_chunks = int.from_bytes(stream.read(1), 'little')
        chr_rom_chunks = int.from_bytes(stream.read(1), 'little')
        mapper_1 = int.from_bytes(stream.read(1), 'little')
        mapper_2 = int.from_bytes(stream.read(1), 'little')
        prg_ram_size = int.from_bytes(stream.read(1), 'little')
        tv_system_1 = int.from_bytes(stream.read(1), 'little')
        tv_system_2 = int.from_bytes(stream.read(1), 'little')

        stream.read(5) # unused bytes

        if mapper_1 & 0x04: # trainer exists, seek past it
            stream.seek(512)

        self.mapper_id = ((mapper_2 << 4) << 4) | (mapper_1 >> 4)

        # load hardware mirror
        self.hardware_mirror = MIRROR_VERTICAL if (mapper_1 & 1) else MIRROR_HORIZONTAL

        # file types
        file_type = 2 if (mapper_2 & 0x0C) == 0x08 else 1

        if file_type == 1:
            self.prg_banks = prg_rom_chunks
            self.prg_memory = [0x00 for i in range(0x4000 * self.prg_banks)]

            for i in range(len(self.prg_memory)):
                self.prg_memory[i] = int.from_bytes(stream.read(1), 'little')
            
            self.chr_banks = chr_rom_chunks

            if self.chr_banks == 0:
                self.chr_memory = [0x00 for i in range(0x2000)]
            else:
                self.chr_memory = [0x00 for i in range(0x2000 * self.chr_banks)]
            
            for i in range(len(self.chr_memory)):
                self.chr_memory[i] = int.from_bytes(stream.read(1), 'little')


        elif file_type == 2:
            self.prg_banks = ((prg_ram_size & 0x07) << 8) | prg_rom_chunks
            self.prg_memory = [0x00 for i in range(0x4000 * self.prg_banks)]

            for i in range(len(self.prg_memory)):
                self.prg_memory[i] = int.from_bytes(stream.read(1), 'little')
            
            self.chr_banks = ((prg_ram_size & 0x38) << 8) | chr_rom_chunks
            self.chr_memory = [0x00 for i in range(0x2000 * self.chr_banks)]

            for i in range(len(self.chr_memory)):
                self.chr_memory[i] = int.from_bytes(stream.read(1), 'little')
        
        assert self.mapper_id in MAPPER_LOOKUP, f"unimplemented mapper id: {self.mapper_id}"

        self.mapper = MAPPER_LOOKUP[self.mapper_id](self.prg_banks, self.chr_banks)

        stream.close()
        rom_file.close()

    def cpu_read(self, addr: int) -> int:
        out = self.mapper.map_cpu_read(addr)

        if out is not None:
            (mapped_addr, value) = out

            if mapped_addr != 0xFFFFFFFF:
                value = self.prg_memory[mapped_addr]
            
            return value

        return None
    
    def cpu_write(self, addr: int, value: int) -> bool:
        mapped_addr = self.mapper.map_cpu_write(addr, value)

        if mapped_addr is not None:
            if mapped_addr != 0xFFFFFFFF:
                self.prg_memory[mapped_addr] = value
            
            return True
        
        return False

    def ppu_read(self, addr: int):
        mapped_addr = self.mapper.map_ppu_read(addr)

        if mapped_addr is not None:
            return self.chr_memory[mapped_addr]
        
        return None

    def ppu_write(self, addr: int, value: int) -> bool:
        mapped_addr = self.mapper.map_ppu_write(addr)

        if mapped_addr is not None:
            self.chr_memory[mapped_addr] = value
            return True
        
        return False

    def reset(self):
        if self.mapper:
            self.mapper.reset()

    def get_mirror(self):
        mirror_mode = self.mapper.mirror_mode()

        if mirror_mode == MIRROR_HARDWARE: # the mirror was determined in hardware with a solder, return it
            return self.hardware_mirror
        
        return mirror_mode
