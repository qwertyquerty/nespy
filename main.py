from nespy.bus import Bus
from nespy.cartridge import Cartridge

if __name__ == "__main__":
    nes = Bus()
    cart = Cartridge("./roms/cpu.nes")
    nes.plug_cartridge(cart)

    import time
    start = time.time()
    time.sleep(0.01)
    while True:
        if (nes.system_clock_count & 0xFFFFF) == 0:
            print(int(nes.cpu.clock_count / (time.time() - start)), "Hz")

        nes.clock()
