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
board.bus_servo_set_position(2, [[1, 0],[2,500],[3,300],[4,850],[5,600],[6,500]])
time.sleep(2)
board.bus_servo_set_position(2, [[5, 380],[4, 800],[3, 390]])
time.sleep(2)
board.bus_servo_set_position(1, [[1, 600]])
time.sleep(1)
board.bus_servo_set_position(2, [[1, 600],[2,500],[3,300],[4,850],[5,600],[6,300]])
time.sleep(2)
board.bus_servo_set_position(2, [[5, 380],[4, 800],[3, 390]])
time.sleep(2)
board.bus_servo_set_position(1, [[1, 0]])
time.sleep(1)
board.bus_servo_set_position(2, [[1, 0],[2,500],[3,200],[4,850],[5,600],[6,500]])
time.sleep(2)
