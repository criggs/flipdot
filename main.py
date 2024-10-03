import machine
import os
import utime

class FlipdotDisplay:

    def __init__(self) -> None:
        self.p0_col = machine.Pin(0, machine.Pin.OUT)
        self.p1_row = machine.Pin(1, machine.Pin.OUT)
        self.p2_set_unset = machine.Pin(2, machine.Pin.OUT)
        self.p3_reset = machine.Pin(3, machine.Pin.OUT)
        self.p4_pulse = machine.Pin(5, machine.Pin.OUT)

        self.x_pos = 0
        self.y_pos = 0

        self.height = 16
        self.width = 32
        self.buffer = bytearray((self.height * self.width)//8)
        self._old_buffer = bytearray((self.height * self.width)//8)

    def toggle_set_unset(self):
        self.p2_set_unset.toggle()
        

    def reset(self):
        self.x_pos = 0
        self.y_pos = 0
        self.p3_reset.on()
        self.p3_reset.off()
        

    def advance_column(self):
        #Reset row position back to 0
        self.y_pos = 0
        self.x_pos = (self.x_pos + 1) % self.width
        self.p0_col.on()
        utime.sleep_us(1)
        self.p0_col.off()
        

    def advance_row(self):
        self.y_pos = (self.y_pos + 1) % self.height
        self.p1_row.on()
        utime.sleep_us(1)
        self.p1_row.off()
        

    def pulse(self):
        self.p4_pulse.on()
        utime.sleep_us(600)
        self.p4_pulse.off()
        

    def clear(self):
        self.reset()
        self.p2_set_unset.off()
        for i in range(self.width):
            for j in range(self.height):
                self.pulse()
                self.advance_row()    
            self.advance_column()

    def set_bit(self, x,y,value):
        print(f"x:{self.x_pos} y:{self.y_pos}")
        
        while self.x_pos != x:
            self.advance_column()
        
        while self.y_pos != y:
            self.advance_row()
        if value:
            self.p2_set_unset.on()
        else:
            self.p2_set_unset.off()
        self.pulse()

    def flip(self):
        # Always reset to the origin before flipping
        self.reset()
        i = 0
        for byte_index, b in enumerate(self.buffer):
            for bit_num in range(8):
                bit_mask = (1 << bit_num)
                old_bit = bit_mask & self._old_buffer[byte_index]
                bit = bit_mask & b
                
                x = i // 16
                y = i % 16

                # Only update the bit if it's changing, compare to the previous buffer
                if old_bit != bit:
                    bit = bit != 0
                    print(f"Updating {x},{y} to {bit}")
                    if bit:
                        self.p2_set_unset.on()
                    else:
                        self.p2_set_unset.off()
                    self.pulse()
                i += 1
                if i % self.height == 0:
                    #Advancing the column will advance the row as well
                    self.advance_column()
                else:
                    self.advance_row()
        self._old_buffer[:] = self.buffer
                

    def draw_rect(x,y,height,width,bit):
        # TODO: draw a rectangle to the buffer
        pass

def main():
    display = FlipdotDisplay()
    # for n in range(100):
    #     utime.sleep_ms(1000)
    #     display.clear()
    #     utime.sleep_ms(500)
    #     for i in range(32):
    #         display.set_bit(i,((i//2) + n )%16,1)
    display.clear()
    for n in range(200):
        
        display.buffer[(n-1) % len(display.buffer)] = 0x28
        display.buffer[n % len(display.buffer)] = 0xF7
        display.flip()
        # utime.sleep_ms(100)

main()

