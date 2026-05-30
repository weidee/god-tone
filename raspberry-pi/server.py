from flask import Flask, jsonify

import agx_client
import camera
import config
import ros_control


app = Flask(__name__)


@app.get("/ping")
def ping():
    return jsonify({"status": "ok"})


@app.post("/trigger")
def trigger():
    try:
        result = run_once()
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


def run_once() -> dict:
    image_bytes = camera.capture_image()
    agx_result = agx_client.detect(image_bytes)
    ros_result = ros_control.execute_command(agx_result.get("command"))

    return {
        "status": "done",
        "agx": agx_result,
        "ros": ros_result,
    }


if __name__ == "__main__":
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT)
