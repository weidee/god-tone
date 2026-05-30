import base64
from pathlib import Path

import config


def capture_image() -> bytes:
    if config.CAMERA_MODE == "mock":
        return _capture_mock_image()
    if config.CAMERA_MODE == "file":
        return _capture_file_image()

    raise ValueError(f"unsupported CAMERA_MODE: {config.CAMERA_MODE}")


def _capture_mock_image() -> bytes:
    return base64.b64decode(
        "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
        "////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////"
        "////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAE"
        "AAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAA"
        "AAAAAAAAA/9oACAEDAQE/ASP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/ASP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAE"
        "BAAY/Aqf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/EFBQRAQAAAAAAAAAAAAAAAAAAABD/2g"
        "AIAQMBAT8QH//EFBQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EFBABAQAAAAAAAAAAAAAAAAAAABD/2gAIAQEAAT8QH//Z"
    )


def _capture_file_image() -> bytes:
    path = _image_path()
    if not path.exists():
        raise ValueError(f"camera image file not found: {path}")
    if not path.is_file():
        raise ValueError(f"camera image path is not a file: {path}")

    image_bytes = path.read_bytes()
    if not image_bytes:
        raise ValueError(f"camera image file is empty: {path}")

    return image_bytes


def _image_path() -> Path:
    raw_path = getattr(config, "CAMERA_IMAGE_PATH", "")
    if not raw_path:
        raise ValueError("CAMERA_IMAGE_PATH is required")

    path = Path(raw_path)
    if path.is_absolute():
        return path

    return Path(config.__file__).resolve().parent / path
