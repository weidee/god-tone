import sys
sys.path.append("/home/pi/board_demo")
from ros_robot_controller_sdk import Board
import time

board = Board()
board.enable_reception()

print("try read ID...")
servo_id = board.bus_servo_read_id(1)
print("recall：", servo_id)

print("move...")
board.bus_servo_set_position(2, [[6, 1000]])
time.sleep(2)
board.bus_servo_set_position(2, [[6, 0]])
time.sleep(2)
board.bus_servo_set_position(2, [[6, 1000]])
time.sleep(2)
