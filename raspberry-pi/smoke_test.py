import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tempfile import NamedTemporaryFile
from threading import Thread

import agx_client
import camera
import config
import ros_control
import server


def main() -> None:
    client = server.app.test_client()

    _assert_ping(client)
    _assert_trigger(client)
    _assert_run_once()
    _assert_file_camera()
    _assert_http_detect()
    _assert_http_value_error()
    _assert_invalid_command()

    print("Raspberry Pi smoke test passed")


def _assert_ping(client) -> None:
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def _assert_trigger(client) -> None:
    response = client.post("/trigger")
    body = response.get_json()

    assert response.status_code == 200
    assert body["status"] == "done"
    assert body["agx"]["label"] == "plastic"
    assert body["agx"]["bin"] == "bin_c"
    assert body["agx"]["command"]["action"] == "pick_and_place"
    assert body["agx"]["command"]["pick_zone"] == "left"
    assert body["ros"]["executed"] is True
    assert body["ros"]["mode"] == "mock"
    assert body["ros"]["motion_plan"][0]["step"] == "move_above_pick"
    assert body["ros"]["motion_plan"][0]["x"] == config.PICK_POINTS["left"]["x"]
    assert body["ros"]["motion_plan"][-1]["step"] == "return_home"


def _assert_run_once() -> None:
    result = server.run_once()

    assert result["status"] == "done"
    assert result["agx"]["command"]["target_bin"] == "bin_c"
    assert result["agx"]["command"]["pick_zone"] == "left"
    assert result["ros"]["executed"] is True
    assert result["ros"]["motion_plan"][4]["target_bin"] == "bin_c"


def _assert_file_camera() -> None:
    old_mode = getattr(config, "CAMERA_MODE", None)
    old_path = getattr(config, "CAMERA_IMAGE_PATH", None)
    expected = b"file camera image bytes"

    with NamedTemporaryFile() as image_file:
        image_file.write(expected)
        image_file.flush()

        try:
            config.CAMERA_MODE = "file"
            config.CAMERA_IMAGE_PATH = image_file.name
            assert camera.capture_image() == expected
        finally:
            _restore_config("CAMERA_MODE", old_mode)
            _restore_config("CAMERA_IMAGE_PATH", old_path)


def _assert_http_detect() -> None:
    received = {}
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _handler(received))
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    old_mode = getattr(config, "AGX_MODE", None)
    old_url = getattr(config, "AGX_URL", None)
    try:
        config.AGX_MODE = "http"
        config.AGX_URL = f"http://127.0.0.1:{httpd.server_port}"

        result = agx_client.detect(b"mock image bytes")

        assert result["label"] == "plastic"
        assert result["bin"] == "bin_c"
        assert result["command"]["target_bin"] == "bin_c"
        assert result["command"]["pick_zone"] == "left"
        assert received["path"] == "/detect"
        assert received["content_type"].startswith("multipart/form-data")
        assert b'name="image"' in received["body"]
        assert b"capture.jpg" in received["body"]
    finally:
        _restore_config("AGX_MODE", old_mode)
        _restore_config("AGX_URL", old_url)
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def _assert_http_value_error() -> None:
    received = {}
    httpd = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        _handler(received, status=422, response_body={"error": "image is required"}),
    )
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    old_mode = getattr(config, "AGX_MODE", None)
    old_url = getattr(config, "AGX_URL", None)
    try:
        config.AGX_MODE = "http"
        config.AGX_URL = f"http://127.0.0.1:{httpd.server_port}"

        try:
            agx_client.detect(b"mock image bytes")
        except ValueError as exc:
            assert str(exc) == "image is required"
        else:
            raise AssertionError("expected ValueError")
    finally:
        _restore_config("AGX_MODE", old_mode)
        _restore_config("AGX_URL", old_url)
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def _assert_invalid_command() -> None:
    try:
        ros_control.execute_command(
            {
                "action": "bad_action",
                "target_bin": "bin_c",
                "pick_zone": "left",
            }
        )
    except ValueError as exc:
        assert str(exc) == "unsupported command action: bad_action"
    else:
        raise AssertionError("expected ValueError")


def _handler(received: dict, status: int = 200, response_body: dict | None = None):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            received["path"] = self.path
            received["content_type"] = self.headers.get("Content-Type", "")
            received["body"] = self.rfile.read(content_length)

            if self.path != "/detect":
                self.send_response(404)
                self.end_headers()
                return

            payload = response_body if response_body is not None else _mock_ai_server_result()
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args) -> None:
            return

    return Handler


def _mock_ai_server_result() -> dict:
    return {
        "schema_version": "1.0",
        "label": "plastic",
        "bin": "bin_c",
        "message": "已產生塑膠分類控制指令",
        "confidence": 0.91,
        "image_size": {
            "width": 640,
            "height": 480,
        },
        "detection": {
            "bbox": {
                "x1": 120,
                "y1": 80,
                "x2": 260,
                "y2": 220,
            },
            "center": {
                "x": 190,
                "y": 150,
            },
        },
        "pick_zone": "left",
        "workspace_candidate": None,
        "workspace": None,
        "command": {
            "action": "pick_and_place",
            "target_bin": "bin_c",
            "pick_zone": "left",
        },
    }


def _restore_config(name: str, old_value) -> None:
    if old_value is None:
        delattr(config, name)
        return

    setattr(config, name, old_value)


if __name__ == "__main__":
    main()
