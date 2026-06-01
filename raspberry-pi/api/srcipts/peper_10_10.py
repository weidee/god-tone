import sys
sys.path.append("/home/pi/board_demo")
from ros_robot_controller_sdk import Board
import time

board = Board()
board.enable_reception()

print("try read ID...")
servo_id = board.bus_servo_read_id(1)
print("recall:", servo_id)

print("move...")
# rotation
board.bus_servo_set_position(1, [[6, 430]])
time.sleep(1)

# stretch out
board.bus_servo_set_position(2, [[5, 370], [4, 760], [3, 330]])
time.sleep(2)

# catch
board.bus_servo_set_position(1, [[1, 600]])
time.sleep(1)

# catch up (just change the no.6 motor)
board.bus_servo_set_position(2, [[6, 620]])
time.sleep(2)
board.bus_servo_set_position(1, [[5, 800], [4, 850], [3, 200]])
time.sleep(1)
board.bus_servo_set_position(1, [[4, 400]])
time.sleep(1)
board.bus_servo_set_position(1, [[3, 500]])
time.sleep(1)

# put down
board.bus_servo_set_position(1, [[1, 0]])
time.sleep(1)

# return to original position
board.bus_servo_set_position(2, [[1, 0], [2, 500], [3, 200], [4, 850], [5, 600], [6, 500]])
time.sleep(2)
