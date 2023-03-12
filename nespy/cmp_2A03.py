from typing import Callable
from dataclasses import dataclass
import math

def apx_sin(t: float):
    j = t * 0.15915
    j = j - int(j)
    return 20.785 * j * (j - 0.5) * (j - 1.0)

APX_PI = 3.14159

@dataclass
class Sequencer():
    sequence = 0x00000000
    new_sequence = 0x00000000
    timer = 0x0000
    reload = 0x0000
    output = 0x00

    def clock(self, enable: bool, func: Callable):
        if enable:
            self.timer = (self.timer - 1) & 0xFFFF

            if self.timer == 0xFFFF:
                self.timer = self.reload
                self.sequence = func(self.sequence)
                self.output = self.sequence & 0x1
        
        return self.output

@dataclass
class LengthCounter():
    counter = 0x00

    def clock(self, enable: bool, halt: bool):
        if not enable:
            self.counter = 0x00
        elif self.counter > 0 and not halt:
            self.counter = (self.counter - 1) & 0xFF
        
        return self.counter

@dataclass
class Envelope():
    start: bool = False
    disable: bool = False
    divider_count: int = 0x0000
    volume: int = 0x0000
    output: int = 0x0000
    decay_count: int = 0x0000

    def clock(self, loop: bool):
        if not self.start:
            if self.divider_count == 0:
                self.divider_count = self.volume

                if self.decay_count == 0 and loop:
                    self.decay_count = 15
                
                else:
                    self.decay_count = (self.decay_count - 1) & 0xFFFF
            
            else:
                self.divider_count = (self.divider_count - 1) & 0xFFFF
            
        else:
            self.start = False
            self.decay_count = 15
            self.divider_count = self.volume
        
        if self.disable:
            self.output = self.volume
        
        else:
            self.output = self.decay_count

class Oscpulse():
    frequency: float = 0
    dutycycle: float = 0
    amplitude: float = 1
    harmonics: float = 20

    def sample(self, t: float):
        a = 0
        b = 0
        p = self.dutycycle * 2 * APX_PI

        for n in range(1, self.harmonics+1):
            c = n * self.frequency * 2 * APX_PI * t
            a += -apx_sin(c) / n
            b += -apx_sin(c - p * n) / n
        
        return (2 * self.amplitude / APX_PI) * (a - b)

@dataclass
class Sweeper():
    enabled: bool = False
    down: bool = False
    reload: bool = False
    shift: int = 0x00
    timer: int = 0x00
    period: int = 0x00
    change: int = 0x00
    mute: bool = False

    def track(self, target: int):
        if self.enabled:
            self.change = target >> self.shift
            self.mute = (target < 8) or (target > 0x07FF)

    def clock(self, target: int, channel: bool):
        changed = False

        if self.timer == 0 and self.enabled and self.shift > 0 and not self.mute:
            if self.target >= 8 and self.change < 0x077F:
                if self.down:
                    target -= self.change - channel
                else:
                    target += self.change
                
                changed = True
            
            if self.timer == 0 or self.reload:
                self.timer = self.period
                self.reload = False
            else:
                self.timer -= 1

            self.mute = (target < 8) or (target > 0x07FF)

            return target if changed else None

class Cmp2A03():
    frame_clock_counter: int = 0x00000000
    clock_counter: int = 0x00000000
    use_raw_mode: bool = False

    length_table: list = [10, 254, 20, 2, 40, 4, 80, 6, 160, 8, 60, 10, 14, 12, 26, 14, 12, 16, 24, 18, 48, 20, 96, 22, 192, 24, 72, 26, 16, 28, 32, 30]

    global_time: float = 0.0

    pulse1_enable: bool = False
    pulse1_halt: bool = False
    pulse1_sample: bool = 0.0
    pulse1_output: float = 0.0
    pulse1_seq: Sequencer = None
    pulse1_osc: Oscpulse = None
    pulse1_env: Envelope = None
    pulse1_lc: LengthCounter = None
    pulse1_sweep: Sweeper = None

    pulse2_enable: bool = False
    pulse2_halt: bool = False
    pulse2_sample: bool = 0.0
    pulse2_output: float = 0.0
    pulse2_seq: Sequencer = None
    pulse2_osc: Oscpulse = None
    pulse2_env: Envelope = None
    pulse2_lc: LengthCounter = None
    pulse2_sweep: Sweeper = None

    noise_enable: bool = False
    noise_halt: bool = False
    noise_sample: bool = 0.0
    noise_output: float = 0.0
    noise_seq: Sequencer = None
    noise_env: Envelope = None
    noise_lc: LengthCounter = None

    def __init__(self):
        self.pulse1_seq = Sequencer()
        self.pulse1_osc = Oscpulse()
        self.pulse1_env = Envelope()
        self.pulse1_lc = LengthCounter()
        self.pulse1_sweep = Sweeper()

        self.pulse2_seq = Sequencer()
        self.pulse2_osc = Oscpulse()
        self.pulse2_env = Envelope()
        self.pulse2_lc = LengthCounter()
        self.pulse2_sweep = Sweeper()

        self.noise_seq = Sequencer()
        self.noise_env = Envelope()
        self.noise_lc = LengthCounter() 

        self.noise_seq.sequence = 0xDBFB

    def cpu_write(self, addr: int, value: int):
        if addr == 0x4000:
            r = (value & 0xC0) >> 6

            if r == 0x00:
                self.pulse1_seq.new_sequence = 0b01000000
                self.pulse1_osc.dutycycle = 0.125

            elif r == 0x01:
                self.pulse1_seq.new_sequence = 0b01100000
                self.pulse1_osc.dutycycle = 0.250

            elif r == 0x02:
                self.pulse1_seq.new_sequence = 0b01111000
                self.pulse1_osc.dutycycle = 0.500

            elif r == 0x03:
                self.pulse1_seq.new_sequence = 0b10011111
                self.pulse1_osc.dutycycle = 0.750
            
            self.pulse1_seq.sequence = self.pulse1_seq.new_sequence
            self.pulse1_halt = bool(value & 0x20)
            self.pulse1_env.volume = value & 0x0F
            self.pulse1_env.disable = bool(value & 0x10)

        elif addr == 0x4001:
            self.pulse1_sweep.enabled = bool(value & 0x80)
            self.pulse1_sweep.period = (value & 0x70) >> 4
            self.pulse1_sweep.down = bool(value & 0x08)
            self.pulse1_sweep.shift = value & 0x07
            self.pulse1_sweep.reload = True

        elif addr == 0x4002:
            self.pulse1_seq.reload = bool((self.pulse1_seq.reload & 0xFF00) | value)
        
        elif addr == 0x4003:
            self.pulse1_seq.reload = ((value & 0x07) << 8) | (self.pulse1_seq.reload & 0x00FF)
            self.pulse1_seq.timer = self.pulse1_seq.reload
            self.pulse1_seq.sequence = self.pulse1_seq.new_sequence
            self.pulse1_lc.counter = self.length_table[(value & 0xF8) >> 3]
            self.pulse1_env.start = True
        
        if addr == 0x4004:
            r = (value & 0xC0) >> 6

            if r == 0x00:
                self.pulse2_seq.new_sequence = 0b01000000
                self.pulse2_osc.dutycycle = 0.125

            elif r == 0x01:
                self.pulse2_seq.new_sequence = 0b01100000
                self.pulse2_osc.dutycycle = 0.250

            elif r == 0x02:
                self.pulse2_seq.new_sequence = 0b01111000
                self.pulse2_osc.dutycycle = 0.500

            elif r == 0x03:
                self.pulse2_seq.new_sequence = 0b10011111
                self.pulse2_osc.dutycycle = 0.750
            
            self.pulse2_seq.sequence = self.pulse2_seq.new_sequence
            self.pulse2_halt = bool(value & 0x20)
            self.pulse2_env.volume = value & 0x0F
            self.pulse2_env.disable = bool(value & 0x10)

        elif addr == 0x4005:
            self.pulse2_sweep.enabled = bool(value & 0x80)
            self.pulse2_sweep.period = (value & 0x70) >> 4
            self.pulse2_sweep.down = bool(value & 0x08)
            self.pulse2_sweep.shift = value & 0x07
            self.pulse2_sweep.reload = True

        elif addr == 0x4006:
            self.pulse2_seq.reload = bool((self.pulse2_seq.reload & 0xFF00) | value)
        
        elif addr == 0x4007:
            self.pulse2_seq.reload = ((value & 0x07) << 8) | (self.pulse2_seq.reload & 0x00FF)
            self.pulse2_seq.timer = self.pulse2_seq.reload
            self.pulse2_seq.sequence = self.pulse2_seq.new_sequence
            self.pulse2_lc.counter = self.length_table[(value & 0xF8) >> 3]
            self.pulse2_env.start = True
        
        elif addr == 0x400E:
            self.noise_seq.reload = (0, 4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 1016, 2034, 4068)[value & 0x0F]
        
        elif addr == 0x4015:
            self.pulse1_enable = bool(value & 0x01)
            self.pulse2_enable = bool(value & 0x02)
            self.noise_enable = bool(value & 0x04)

            if not self.pulse1_enable: self.pulse1_lc.counter = 0
            if not self.pulse2_enable: self.pulse2_lc.counter = 0
            if not self.noise_enable: self.noise_lc.counter = 0

        elif addr == 0x400F:
            self.pulse1_env.start = True
            self.pulse2_env.start = True
            self.noise_env.start = True
            self.noise_lc.counter = self.length_table[(value & 0xF8) >> 3]

        elif addr == 0x4017:
            self.frame_clock_counter = value

            if self.frame_clock_counter & 0x80:
                self.pulse1_lc.clock(self.pulse1_enable, self.pulse1_halt)
                self.pulse2_lc.clock(self.pulse2_enable, self.pulse2_halt)
                self.noise_lc.clock(self.noise_enable, self.noise_halt)
                self.pulse1_sweep.clock(self.pulse1_seq.reload, 0)
                self.pulse2_sweep.clock(self.pulse2_seq.reload, 1)
                self.pulse1_seq.clock(self.pulse1_enable, lambda s: ((s & 0x0001) << 7) | ((s & 0x00FE) >> 1))
                self.pulse2_seq.clock(self.pulse2_enable, lambda s: ((s & 0x0001) << 7) | ((s & 0x00FE) >> 1))
                self.noise_seq.clock(self.noise_enable, lambda s: (((s & 0x0001) ^ ((s & 0x0002) >> 1)) << 14) | ((s & 0x7FFF) >> 1))

    def cpu_read(self, addr: int) -> int:
        if addr == 0x4015:
            return (0x01 if (self.pulse1_lc.counter > 0) else 0x00) | (0x02 if (self.pulse1_lc.counter > 0) else 0x00) | (0x04 if (self.pulse1_lc.counter > 0) else 0x00)
        
        return 0x00

    def clock(self):
        quarter_frame_clock = False
        half_frame_clock = False

        self.global_time += (1/3) / 1789773

        if self.clock_counter & 6 == 0:
            self.frame_clock_counter += 1

            if self.frame_clock_counter == 3729:
                quarter_frame_clock = True
            
            elif self.frame_clock_counter == 7457:
                quarter_frame_clock = True
                half_frame_clock = True
            
            elif self.frame_clock_counter == 11186:
                quarter_frame_clock = True
            
            elif self.frame_clock_counter == 14916:
                quarter_frame_clock = True
                half_frame_clock = True
                self.frame_clock_counter = 0
            
            if quarter_frame_clock:
                self.pulse1_env.clock(self.pulse1_halt)
                self.pulse2_env.clock(self.pulse2_halt)
                self.noise_env.clock(self.noise_halt)

            if half_frame_clock:
                self.pulse1_lc.clock(self.pulse1_enable, self.pulse1_halt)
                self.pulse2_lc.clock(self.pulse2_enable, self.pulse2_halt)
                self.noise_lc.clock(self.noise_enable, self.noise_halt)
                self.pulse1_sweep.clock(self.pulse1_seq.reload, 0)
                self.pulse2_sweep.clock(self.pulse2_seq.reload, 1)

            self.pulse1_seq.clock(self.pulse1_enable, lambda s: ((s & 0x0001) << 7) | ((s & 0x00FE) >> 1))

            self.pulse1_osc.frequency = 1789773 / (16 * (self.pulse1_seq.reload + 1))
            self.pulse1_osc.amplitude = (self.pulse1_env.output - 1) / 16
            self.pulse1_sample = self.pulse1_osc.sample(self.global_time)

            if self.pulse1_lc.counter > 0 and self.pulse1_seq.timer >= 8 and not self.pulse1_sweep.mute and self.pulse1_env.output > 2:
                self.pulse1_output += (self.pulse1_sample - self.pulse1_output) * 0.5
            else:
                self.pulse1_output = 0


            self.pulse2_seq.clock(self.pulse2_enable, lambda s: ((s & 0x0001) << 7) | ((s & 0x00FE) >> 1))

            self.pulse2_osc.frequency = 1789773 / (16 * (self.pulse2_seq.reload + 1))
            self.pulse2_osc.amplitude = (self.pulse2_env.output - 1) / 16
            self.pulse2_sample = self.pulse2_osc.sample(self.global_time)

            if self.pulse2_lc.counter > 0 and self.pulse2_seq.timer >= 8 and not self.pulse2_sweep.mute and self.pulse2_env.output > 2:
                self.pulse2_output += (self.pulse2_sample - self.pulse2_output) * 0.5
            else:
                self.pulse2_output = 0
            
            
            self.noise_seq.clock(self.noise_enable, lambda s: (((s & 0x0001) ^ ((s & 0x0002) >> 1)) << 14) | ((s & 0x7FFF) >> 1))

            if self.noise_lc.counter > 0 and self.noise_seq.timer >= 8:
                self.noise_output = self.noise_seq.output * (self.noise_env.output - 1) / 16
            
            if not self.pulse1_enable: self.pulse1_output = 0
            if not self.pulse2_enable: self.pulse2_output = 0
            if not self.noise_enable: self.noise_output = 0
        
        self.pulse1_sweep.track(self.pulse1_seq.reload)
        self.pulse2_sweep.track(self.pulse2_seq.reload)

        self.clock_counter += 1

    def reset(self):
        pass

    def get_sample(self):
        return (1.0 * self.pulse1_output - 0.8) * 0.1 + (1.0 * self.pulse2_output - 0.8) * 0.1 + (2.0 * self.noise_output - 0.5) * 0.1
