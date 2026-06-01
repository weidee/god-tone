from io import BytesIO

from PIL import Image

import server


def main() -> None:
    client = server.app.test_client()

    _assert_ping(client)
    _assert_detect(client)
    _assert_missing_image(client)
    _assert_invalid_image(client)

    print("AGX smoke test passed")


def _assert_ping(client) -> None:
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "yolo": "loaded"}


def _assert_detect(client) -> None:
    image = Image.new("RGB", (640, 480), color="white")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    response = client.post(
        "/detect",
        data={"image": (buffer, "test.jpg")},
        content_type="multipart/form-data",
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["schema_version"] == "1.0"
    assert body["label"] == "plastic"
    assert body["bin"] == "bin_b"
    assert body["image_size"] == {"width": 640, "height": 480}
    assert body["pick_zone"] == "middle"
    assert body["workspace_candidate"] is None
    assert body["workspace"] is None
    assert body["command"]["action"] == "pick_and_place"
    assert body["command"]["target_bin"] == "bin_b"
    assert body["command"]["pick_zone"] == "middle"
    assert "pick" not in body["command"]
    assert body["detection"]["center"] == {"x": 320.0, "y": 240.0}


def _assert_missing_image(client) -> None:
    response = client.post("/detect", data={}, content_type="multipart/form-data")
    assert response.status_code == 422
    assert response.get_json() == {"error": "image is required"}


def _assert_invalid_image(client) -> None:
    response = client.post(
        "/detect",
        data={"image": (BytesIO(b"not an image"), "bad.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 422
    assert response.get_json() == {"error": "invalid image"}


if __name__ == "__main__":
    main()
