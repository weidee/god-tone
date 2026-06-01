
# ~/api/scripts/runner.py
import sys, time
sys.path.append("/home/pi/board_demo")
from ros_robot_controller_sdk import Board

# 先只放兩個示範點，等會你自己加
POSES = {
    "r0c0": [[1,430],[2,530],[3,770],[4,770],[5,440],[6,600]],
    "r0c1": [[1,410],[2,540],[3,760],[4,760],[5,450],[6,600]],
}

BUS1 = {1,6}              # 依你現有腳本習慣
BUS2 = {2,3,4,5}

def move(board, joints, t=1.0):
    p1 = [p for p in joints if p[0] in BUS1]
    p2 = [p for p in joints if p[0] in BUS2]
    if p1: board.bus_servo_set_position(1, p1)
    if p2: board.bus_servo_set_position(2, p2)
    time.sleep(t)

def run(key):
    if key not in POSES:
        print("未知位置:", key); return
    board = Board(); board.enable_reception()
    print("move to", key)
    move(board, POSES[key], 1.5)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 runner.py r0c0")
    else:
        run(sys.argv[1])
