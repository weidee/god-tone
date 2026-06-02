from flask import Flask, jsonify, request

import config
import task_control
import yolo_infer


app = Flask(__name__)
yolo_model = yolo_infer.load_model(config.YOLO_MODEL_PATH)


@app.get("/ping")
def ping():
    return jsonify({"status": "ok", "yolo": "loaded"})


@app.post("/detect")
def detect():
    try:
        image = request.files.get("image")
        if image is None:
            raise ValueError("image is required")

        image_bytes = image.read()
        if not image_bytes:
            raise ValueError("image is required")

        result = yolo_infer.infer(yolo_model, image_bytes)
        if result["label"] is None:
            return jsonify(task_control.empty_result())

        final_result = task_control.build_result(result)
        return jsonify(final_result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT)
