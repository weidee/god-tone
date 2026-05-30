import requests

import config


def detect(image_bytes: bytes) -> dict:
    response = requests.post(
        config.AGX_URL.rstrip("/") + "/detect",
        files={"image": ("capture.jpg", image_bytes, "image/jpeg")},
        timeout=config.REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()
