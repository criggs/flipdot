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
    
    def clear_buffer(self):
        #reinitialize buffer to a blank bit array
        for i in range(len(self.buffer)):
            self.buffer[i] = 0x00

    def clear(self):
        self.reset()
        self.p2_set_unset.off()
        for i in range(self.width):
            for j in range(self.height):
                self.pulse()
                self.advance_row()    
            self.advance_column()

    def _set_bit(self, x,y,value):
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
                    # print(f"Updating {x},{y} to {bit}")
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
        self.y = (display.height // 2) - (self.height // 2)
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
    frame_num = 0

    game = Pong(display)

    while True:

        display.clear_buffer()

        #draw the middle line

        mid = display.width // 2


        for i in range(display.height):
            display.set_bit(mid, i, 1)


        game.update()

        display.flip()
        
        utime.sleep_ms(20)
        frame_num += 1


main()

