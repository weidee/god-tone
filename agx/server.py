from flask import Flask, jsonify, request

import config
import skill
import yolo_infer


app = Flask(__name__)
yolo_model = yolo_infer.load_model(config.YOLO_MODEL_PATH)


@app.get("/ping")
def ping():
    return jsonify({"status": "ok", "yolo": "loaded"})


@app.post("/classify")
def classify():
    try:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")

        text = data.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text is required")

        result = skill.run_skill_voice(text.strip())
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


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
            return jsonify(
                {
                    "bin": None,
                    "label": None,
                    "message": "未偵測到垃圾",
                    "confidence": None,
                }
            )

        final_result = skill.run_skill_vision(result["label"], result["confidence"])
        return jsonify(final_result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.FLASK_PORT)
