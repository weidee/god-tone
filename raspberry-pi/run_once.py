import json

from server import run_once


if __name__ == "__main__":
    print(json.dumps(run_once(), ensure_ascii=False, indent=2))
