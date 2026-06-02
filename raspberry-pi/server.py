from flask import Flask, jsonify

import ai_server_client
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
    ai_server_result = ai_server_client.detect(image_bytes)
    ros_result = ros_control.execute_command(ai_server_result.get("command"))

    return {
        "status": "done",
        "agx": ai_server_result,
        "ros": ros_result,
    }


if __name__ == "__main__":
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT)
