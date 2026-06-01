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
# return to original position
board.bus_servo_set_position(1, [[1, 0], [2, 500], [3, 200], [4, 850], [5, 600], [6, 500]])
time.sleep(1.1)
# rotation
board.bus_servo_set_position(1, [[6, 530]])
time.sleep(1.1)

# stretch out
board.bus_servo_set_position(1, [[5, 330], [4, 770], [3, 440]])
time.sleep(1.1)

# catch
board.bus_servo_set_position(1, [[1, 600]])
time.sleep(1.1)

# catch up (just change the no.6 motor)
board.bus_servo_set_position(1, [[6, 400]])
time.sleep(1.1)
board.bus_servo_set_position(1, [[5, 800], [4, 850], [3, 200]])
time.sleep(1.1)
board.bus_servo_set_position(1, [[4, 400]])
time.sleep(1.1)
board.bus_servo_set_position(1, [[3, 500]])
time.sleep(1.1)

# put down
board.bus_servo_set_position(1, [[1, 0]])
time.sleep(1.1)

# return to original position
board.bus_servo_set_position(1, [[1, 0], [2, 500], [3, 200], [4, 850], [5, 600], [6, 500]])
time.sleep(1.1)
