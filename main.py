import machine
import os
import utime

class FlipdotDisplay:

    def __init__(self) -> None:
        self.led = machine.Pin(25, machine.Pin.OUT)
        
        self.pin_col = machine.Pin(0, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.pin_row = machine.Pin(1, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        
        self.pin_set_unset = machine.Pin(2, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.pin_reset = machine.Pin(3, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        
        #Why skip p4? Who knows....
        
        self.pin_pulse = machine.Pin(5, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        
        #Enable pins
        self.pin_e1 = machine.Pin(6, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.pin_e2 = machine.Pin(7, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.pin_e3 = machine.Pin(8, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.pin_e4 = machine.Pin(9, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        
        self.panel_pins = [
            self.pin_e1,
            self.pin_e2,
            self.pin_e3,
            self.pin_e4,
        ]
        
        self.disable_all_panels()

        self.x_pos = 0
        self.y_pos = 0

        self.panel_height = 16
        self.panel_width = 32
        
        self.panel_count = 2
        
        self.bytes_per_panel = (self.panel_height * self.panel_width)//8

        self.height = self.panel_height
        self.width = self.panel_count * self.panel_width
        
        self.buffer = bytearray(self.bytes_per_panel * self.panel_count)
        self._old_buffer = bytearray(self.bytes_per_panel * self.panel_count)

    def toggle_set_unset(self):
        self.pin_set_unset.toggle()
        
    def enable_all_panels(self):
        for panel_pin in self.panel_pins:
            panel_pin.on()
            
    def disable_all_panels(self):
        for panel_pin in self.panel_pins:
            panel_pin.off()

    def enable_single_panel(self, panel):
        for i, panel_pin in enumerate(self.panel_pins):
            if i == panel:
                panel_pin.on()
            else:
                panel_pin.off()

    def reset(self):
        self.x_pos = 0
        self.y_pos = 0
        
        #self.enable_all_panels()
        
        self.pin_reset.on()
        self.pin_reset.off()
        
        #self.disable_all_panels()
        

    def advance_column(self):
        #Reset row position back to 0
        self.y_pos = 0
        self.x_pos = (self.x_pos + 1) % self.panel_width
        self.pin_col.on()
        self.pin_col.off()

    def advance_row(self):
        self.y_pos = (self.y_pos + 1) % self.panel_height
        self.pin_row.on()
        self.pin_row.off()
        
    def _pulse(self):
        self.pin_pulse.on()
        utime.sleep_us(250)
        self.pin_pulse.off()
        
    def pulse_bit(self, bit):
        
        if bit:
            self.pin_set_unset.on()
        else:
            self.pin_set_unset.off()
        self._pulse()
    
    def clear_buffer(self):
        #reinitialize buffer to a blank bit array
        for i in range(len(self.buffer)):
            self.buffer[i] = 0x00

    def _set_all(self, bit):
        self.reset()
        self.enable_all_panels()
        for i in range(self.panel_width):
            for j in range(self.panel_height):
                self.pulse_bit(bit)
                self.advance_row()    
            self.advance_column()

    def clear(self):
        self._set_all(0)

    def fill(self):
        self._set_all(1)

    def _set_bit(self, x,y,value):
        print(f"x:{self.x_pos} y:{self.y_pos}")
        
        while self.x_pos != x:
            self.advance_column()
        
        while self.y_pos != y:
            self.advance_row()
        self.pulse_bit(value)


    def pulse_panels(self, panels, bit):
        if len(panels) == 0:
            return
        
        if bit:
            self.pin_set_unset.on()
        else:
            self.pin_set_unset.off()
        
        self.disable_all_panels()
        
        print(f"set bit:{bit} panels:{panels}")
        for panel in panels:
            self.panel_pins[panel].on()
        
        self.pulse_bit(bit)
        
    def get_bit_changes_by_panel(self, old_panel_byte_array, new_panel_byte_array, bit_num):
        panels_on = []
        panels_off = []
        
        bit_mask = (1 << bit_num)
        
        for panel_index in range(len(old_panel_byte_array)):
            old_bit = bit_mask & old_panel_byte_array[panel_index]
            bit = bit_mask & new_panel_byte_array[panel_index]
            
            if old_bit != bit:
                bit = bit != 0
                if bit:
                    panels_on.append(panel_index)
                else:
                    panels_off.append(panel_index)
        
        return (panels_on, panels_off)
        
    
    def flip_panel(self, panel):
        
        # Always reset to the origin before flipping
        self.reset()
        i = 0
        
        self.enable_single_panel(panel)
        
        for byte_index in range(self.bytes_per_panel//2):
            pannel_offset = panel * self.bytes_per_panel
            b0 = (byte_index * 2) + pannel_offset
            b1 = b0 + 1
            
            old_bytes = [self._old_buffer[b0], self._old_buffer[b1]]
            new_bytes = [self.buffer[b0], self.buffer[b1]]
            
            if old_bytes == new_bytes:
                i += 16
                self.advance_column()
                continue
            
            for b_index in range(2):
                old_byte = old_bytes[b_index]
                new_byte = new_bytes[b_index]
                
                if old_byte == new_byte:
                    i += 8
                    if i % self.panel_height == 0:
                        #Advancing the column will advance the row as well
                        self.advance_column()
                    else:
                        for j in range(8):
                            self.advance_row()
                    continue
                
                for bit_num in range(8):
                    
                    bit_mask = (1 << bit_num)
                    old_bit = bit_mask & old_byte
                    new_bit = bit_mask & new_byte
                    
                    x = i // 16
                    y = i % 16

                    # Only update the bit if it's changing, compare to the previous buffer
                    if old_bit != new_bit:
                        bit = new_bit != 0
                        # print(f"Updating {x},{y} to {bit}")
                        self.pulse_bit(bit)
                    
                    i += 1
                    if i % self.panel_height == 0:
                        #Advancing the column will advance the row as well
                        self.advance_column()
                    else:
                        self.advance_row()
                    
    def flip(self):
        for panel in range(self.panel_count):
            self.flip_panel(panel)
            
        self._old_buffer[:] = self.buffer

    def get_byte_num(self, x, y):
        return (x * 2) + (y//8)

    def set_bit(self, x, y, value):
        byte_num = self.get_byte_num(x,y)       
        bit_num = y % 8
        bit_mask = (1 << bit_num)
        if value:
            self.buffer[byte_num] = self.buffer[byte_num] | bit_mask
        else:
            self.buffer[byte_num] = self.buffer[byte_num] & ~bit_mask
                    

    def draw_rect(x,y,height,width,bit):
        # TODO: draw a rectangle to the buffer
        pass

class Ball:
    def __init__(self, display) -> None:
        self.x = display.width // 2
        self.y = display.height // 2
        self.x_speed = -1
        self.y_speed = 1
        self.display = display
    
    def update(self):
        self.x += self.x_speed
        self.y += self.y_speed

        if self.x <= 0 or self.x >= self.display.width - 1:
            self.x_speed = -1 * self.x_speed
        if self.y <= 0 or self.y >= self.display.height - 1:
            self.y_speed = -1 * self.y_speed

    def draw(self):
        self.display.set_bit(self.x, self.y, 1)

class Paddle:
    def __init__(self, x, display:FlipdotDisplay) -> None:
        self.height = 4
        self.x = x
        self.y = 0
        self.speed = 1
        self.display = display

    def update(self, ball:Ball):

        if abs(ball.x - self.x) > 10:
            return

        if ball.y < self.y:
            self.y -= self.speed
        if ball.y > self.y + self.height:
            self.y += self.speed

        if self.y < 0:
            self.y = 0
        if self.y + self.height > self.display.height:
            self.y = self.display.height - self.height

    def draw(self):
        for i in range(self.height):
            self.display.set_bit(self.x, self.y + i, 1)


class Pong:

    def __init__(self, display:FlipdotDisplay) -> None:
        self.display = display
        self.ball = Ball(display)      
        self.paddle_1 = Paddle(0, display)
        self.paddle_2 = Paddle(display.width - 1, display)  

    def update(self):

        #move ball
        self.ball.update()
        self.paddle_1.update(self.ball)
        self.paddle_2.update(self.ball)

        #Check conditions

        #draw to display
        self.ball.draw()
        self.paddle_1.draw()
        self.paddle_2.draw()

def main():
    display = FlipdotDisplay()

    display.clear()
    display.fill()
    display.clear()
    
    frame_num = 0

    game = Pong(display)

    while True:

        display.led.toggle()

        display.clear_buffer()

        #draw the middle line
        mid = display.width // 2
        for i in range(display.height):
            display.set_bit(mid, i, 1)

        game.update()

        display.flip()
        
        utime.sleep_ms(10)
        frame_num += 1


main()


