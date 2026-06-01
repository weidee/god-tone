import os
import re
import cv2
import time
import json
import signal
import platform
import requests
import subprocess
from urllib.parse import urljoin

API_BASE   = "http://192.168.149.10:5000"
API_UPLOAD = urljoin(API_BASE, "/garbage")  # 上傳圖片 → 伺服器決定/設定任務
API_TASK   = urljoin(API_BASE, "/task")     # 取目前任務
API_RESET  = urljoin(API_BASE, "/reset")    # 任務完成後重置

SCRIPT_DIR = "/home/pi/api/srcipts"         # 注意：是 scripts（不是 srcipts）
CAPTURE_PREFIX = "/home/pi/photo_"
CAM_INDEX = 0

UPLOAD_TIMEOUT   = 100       # 上傳逾時（秒）
SCRIPT_TIMEOUT   = 500       # 腳本最長執行時間（秒）
NO_TASK_INTERVAL = 1.5      # 沒任務時，每秒拍一張

# ========== 基本工具 ==========
def sanitize_task_name(name: str) -> str:
    """清理任務名稱：去空白、摺疊雙底線、只留 [a-zA-Z0-9_.]，並確保結尾為 .py"""
    if not name:
        return ""
    name = name.strip().replace(" ", "")
    while "__" in name:
        name = name.replace("__", "_")
    # 只允許安全字元
    name = re.sub(r"[^a-zA-Z0-9_.]", "_", name)
    # 一律確保 .py
    if not name.endswith(".py"):
        name = f"{name}.py"
    return name

def resolve_script_path(task_name: str) -> str | None:
    """
    全部都用 .py：
    - 僅取 basename 防止路徑穿越
    - 補齊/校正副檔名
    - 找不到就列出資料夾檔案協助診斷
    """
    if not task_name:
        return None
    safe = os.path.basename(sanitize_task_name(task_name))
    candidate = os.path.join(SCRIPT_DIR, safe)
    if os.path.exists(candidate):
        return candidate

    # 找不到：列出目錄前 80 個檔案幫你對照
    try:
        listing = ", ".join(sorted(os.listdir(SCRIPT_DIR))[:80])
        print(f"[DEBUG] not found: {safe}; in {SCRIPT_DIR} we have: {listing}")
    except Exception as e:
        print(f"[DEBUG] cannot list {SCRIPT_DIR}: {e}")
    return None

def capture_and_upload():
    """沒任務時拍一張上傳到 /garbage，回傳伺服器 JSON（含 task）或 None。"""
    cap = cv2.VideoCapture(CAM_INDEX)
    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        print("[ERROR] cannot read frame from camera")
        return None

    ts = time.strftime("%Y%m%d_%H%M%S")
    img_path = f"{CAPTURE_PREFIX}{ts}.jpg"
    if not cv2.imwrite(img_path, frame):
        print("[ERROR] failed to save image:", img_path)
        return None

    try:
        with open(img_path, "rb") as f:
            r = requests.post(API_UPLOAD, files={"image": f}, timeout=UPLOAD_TIMEOUT)
        ctype = r.headers.get("Content-Type", "")
        print("[DEBUG] POST /garbage ->", r.status_code, r.text[:160])
        if r.ok and ctype.startswith("application/json"):
            return r.json()
    except Exception as e:
        print("[ERROR] upload failed:", e)
    return None

def get_current_task() -> str:
    try:
        r = requests.get(API_TASK, timeout=5)
        if r.ok:
            data = r.json() if r.headers.get("Content-Type","").startswith("application/json") else {}
            return (data or {}).get("task", "none")
    except Exception as e:
        print("[WARN] GET /task failed:", e)
    return "none"

def reset_task():
    try:
        r = requests.post(API_RESET, timeout=5)
        msg = r.text if hasattr(r, "text") else ""
        print("[INFO] POST /reset ->", r.status_code, msg[:120])
    except Exception as e:
        print("[WARN] reset failed:", e)

def execute_script(script_path: str):
    """執行 .py 腳本，最長 SCRIPT_TIMEOUT 秒，逾時強制終止（Linux 用 process group）。"""
    if not script_path or not os.path.exists(script_path):
        print("[ERROR] script not found:", script_path)
        return

    cmd = ["python3", script_path]
    print(f"[INFO] running: {cmd} (timeout={SCRIPT_TIMEOUT}s)")

    try:
        if platform.system().lower().startswith("win"):
            proc = subprocess.Popen(cmd)
        else:
            # 建立新 process group，逾時可以整組終止
            proc = subprocess.Popen(cmd, preexec_fn=os.setsid)

        try:
            proc.wait(timeout=SCRIPT_TIMEOUT)
            print("[INFO] script finished with code:", proc.returncode)
        except subprocess.TimeoutExpired:
            print("[WARN] timeout, killing script...")
            if platform.system().lower().startswith("win"):
                proc.terminate()
            else:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                except Exception:
                    proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                pass
            print("[WARN] script terminated due to timeout")
    except Exception as e:
        print("[ERROR] execute failed:", e)

def main():
    print("[INFO] client runner started")
    if not os.path.isdir(SCRIPT_DIR):
        print(f"[WARN] script dir not found: {SCRIPT_DIR}")

    try:
        while True:
            # 1) 檢查是否已有任務（執行時不拍照）
            task = get_current_task()
            if task and task != "none":
                task = sanitize_task_name(task)
                print("information:", task)
                path = resolve_script_path(task)
                print("[DEBUG] resolved path:", path)
                execute_script(path)
                reset_task()
                time.sleep(0.2)  # 小歇一下
            else:
                # 2) 沒任務：每秒拍一次，讓伺服器決定要不要派任務
                _ = capture_and_upload()
                time.sleep(NO_TASK_INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] stopped by user")

if __name__ == "__main__":
    main()
