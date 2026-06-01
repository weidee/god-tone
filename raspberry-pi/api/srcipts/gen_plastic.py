import pathlib

TEMPLATE = """\
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
board.bus_servo_set_position(1, [[2, 800]])
time.sleep(1.1)
board.bus_servo_set_position(1, [[6, {angle}]])
time.sleep(1.1)

# stretch out
board.bus_servo_set_position(1, [[2, 800]])
time.sleep(1.1)
board.bus_servo_set_position(1, [[5, 410], [4, 760], [3, 215]])
time.sleep(1.1)

# catch
board.bus_servo_set_position(1, [[1, 600]])
time.sleep(1.1)

# catch up (just change the no.6 motor)
board.bus_servo_set_position(1, [[5, 800], [4, 850], [3, 200]])
time.sleep(1.1)
board.bus_servo_set_position(1, [[6, 50]])
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
"""

outdir = pathlib.Path(".")
outdir.mkdir(exist_ok=True)

base_angle = 430
for idx, suffix in enumerate(range(9, 3, -1)):  # 9 → 8 → 7 … → 4
    angle = base_angle + (idx + 1) * 20
    filename = outdir / f"plastic_7_{suffix}.py"
    filename.write_text(TEMPLATE.format(angle=angle), encoding="utf-8")
    print("Wrote", filename, "with angle", angle)
